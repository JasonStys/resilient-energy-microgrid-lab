"""Analytical energy contracts and independent audit fault injection by Jason Stys. Index: docs/CODE_INDEX.md."""

import copy

import pytest

from gridlab import engine
from gridlab.dispatch import simulate
from gridlab.model import Settings, configuration


def case(**config):
    """Return a loss-controlled single-slot fixture with explicit, independently calculable values."""
    data = configuration(Settings())
    data["config"].update(
        capacity_wh=10000,
        initial_wh=10000,
        reserve_pct=50,
        charge_eff_permille=800,
        discharge_eff_permille=800,
        **config,
    )
    data["profile"] = [
        dict(
            solar_w=0,
            wind_w=0,
            critical_w=1000,
            flexible_w=5000,
            grid_limit_w=0,
            battery_available=True,
        )
    ]
    return data


def test_reserve_and_rate():
    """Critical load uses reserve; flexible load stops at reserve; combined AC rate remains bounded."""
    run = engine.analyze(case())
    selected = run["selected"]["rows"][0]
    assert selected["battery_critical_wh"] == 1000
    assert selected["battery_flexible_wh"] == 3000
    assert selected["end_wh"] == 5000
    assert selected["discharge_loss_wh"] == 1000
    other = run["comparison"]["rows"][0]
    assert other["battery_flexible_wh"] == 4000
    assert other["end_wh"] == 3750


def test_critical_can_exhaust_reserve():
    """Reserve protects future critical energy from flexible demand, not from present critical demand."""
    data = case()
    data["config"]["initial_wh"] = 1000
    row = engine.analyze(data)["selected"]["rows"][0]
    assert row["battery_critical_wh"] == 800
    assert row["critical_unserved_wh"] == 200
    assert row["battery_flexible_wh"] == 0
    assert row["end_wh"] == 0


def test_charge_headroom_and_loss():
    """Charge power is AC input; headroom divides by efficiency and losses close the system ledger."""
    data = case()
    data["config"]["initial_wh"] = 9000
    data["profile"][0].update(solar_w=10000, critical_w=0, flexible_w=0)
    row = engine.analyze(data)["selected"]["rows"][0]
    assert row["charge_renewable_wh"] == 1250
    assert row["end_wh"] == 10000
    assert row["charge_loss_wh"] == 250
    assert row["curtailed_wh"] == 8750


def test_grid_topup_and_trip():
    """Feeder top-up respects load priority, feeder cap, shared charger rate and battery availability."""
    data = case()
    data["config"].update(initial_wh=0, precharge=1)
    data["profile"][0].update(grid_limit_w=8000)
    row = engine.analyze(data)["selected"]["rows"][0]
    assert row["charge_grid_wh"] == 2000
    assert row["end_wh"] == 1600
    data["profile"][0]["battery_available"] = False
    row = engine.analyze(data)["selected"]["rows"][0]
    assert row["charge_grid_wh"] == 0 and row["end_wh"] == 0


def test_nullable_and_recovery():
    """No demand is unavailable coverage; recovery is the first later connected, reserve-restored slot."""
    run = engine.build_run(Settings(scenario="zero-demand"))
    assert run["selected"]["summary"]["critical_service_pct"] is None
    assert run["selected"]["summary"]["first_critical_shortfall_hour"] is None
    data = case()
    data["config"].update(initial_wh=0, precharge=1)
    data["profile"] += [dict(data["profile"][0], grid_limit_w=15000)] * 2
    summary = engine.analyze(data)["selected"]["summary"]
    assert summary["reserve_recovery_hour"] == 2
    assert summary["longest_critical_shortfall_run_hours"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("end_wh", 10001),
        ("start_wh", 1),
        ("curtailed_wh", -1),
        ("charge_loss_wh", 5),
        ("hour", 9),
        ("grid_critical_wh", float("nan")),
        ("critical_unserved_wh", 0),
    ],
)
def test_audit_detects_corruption(field, value):
    """The independent ledger rejects corrupted states, signs, time indices, losses and missing demand."""
    data = case()
    data["config"]["initial_wh"] = 0
    rows = simulate(data)
    rows[0][field] = value
    with pytest.raises(RuntimeError):
        engine.audit(rows, data)


def test_audit_missing_rows():
    """Silent truncation is not a valid simulation."""
    with pytest.raises(RuntimeError):
        engine.audit([], case())


def test_fail_closed_reference(monkeypatch):
    """A disagreement or missing reference trace prevents a verified report being emitted."""
    original = engine.reference

    def corrupted(data):
        """Fault-inject one reference field without changing the production algorithm."""
        rows = original(data)
        rows[0]["end_wh"] += 1
        return rows

    monkeypatch.setattr(engine, "reference", corrupted)
    with pytest.raises(RuntimeError, match="reference disagreement"):
        engine.analyze(case())
    monkeypatch.setattr(engine, "reference", lambda data: [])
    with pytest.raises(RuntimeError):
        engine.analyze(case())


def test_paired_fairness_and_identity():
    """The counterfactual shares the exact profile/initial state, and deterministic identity is stable."""
    data = case()
    before = copy.deepcopy(data)
    run = engine.analyze(data)
    assert data == before
    assert run == engine.analyze(data)
    assert run["selected"]["rows"][0]["start_wh"] == run["comparison"]["rows"][0]["start_wh"]
    data["provenance"] += " edited"
    assert engine.analyze(data)["id"] != run["id"]
