"""Independent stress-profile expectations by Jason Stys.

Functions: test_*; variables: disconnected one-hour demand and unchanged original input.
The exact-rational reference gates every stressed policy trace. Lines: docs/CODE_INDEX.md.
"""

from copy import deepcopy

from gridlab.engine import analyze, build_run
from gridlab.model import CASES, Settings, configuration, validate


def test_one_hour_manual_feeder_loss_and_input_immutability():
    """No stored energy/renewables: losing a 10W feeder leaves exactly10Wh critical unserved."""
    data = configuration(Settings())
    data["config"].update(initial_wh=0, charge_limit_w=0, discharge_limit_w=0)
    data["profile"] = [
        {
            "solar_w": 0,
            "wind_w": 0,
            "critical_w": 10,
            "flexible_w": 4,
            "grid_limit_w": 20,
            "battery_available": True,
        }
    ]
    before = deepcopy(data)
    run = analyze(data)
    assert data == before
    stress = run["feeder_loss"]
    assert run["selected"]["summary"]["critical_unserved_wh"] == 0
    assert stress["selected"]["summary"]["critical_unserved_wh"] == 10
    assert stress["critical_unserved_delta_wh"] == 10
    assert stress["flexible_unserved_delta_wh"] == 4
    assert stress["grid_import_reduction_wh"] == 14
    validate(stress["input"])


def test_all_profiles_stress_both_policies_and_replay_input():
    """Stress removes only feeder availability; zero-demand remains undefined, not100% service."""
    for scenario in CASES:
        run = build_run(Settings(scenario=scenario))
        stress = run["feeder_loss"]
        assert all(slot["grid_limit_w"] == 0 for slot in stress["input"]["profile"])
        for key in ("selected", "comparison"):
            assert stress[key]["summary"]["grid_import_wh"] == 0
            assert stress[key]["verification"]["reference_verified"]
            assert stress[key]["verification"]["energy_ledgers_verified"]
        assert analyze(stress["input"])["selected"] == stress["selected"]
        if scenario == "zero-demand":
            assert stress["selected"]["summary"]["critical_service_pct"] is None
