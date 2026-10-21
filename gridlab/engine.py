"""Independent verification, conservation gates and paired policy evidence by Jason Stys.

Functions: canonical, audit, summarize, evaluate, analyze, build_run. Variables: tolerance, Wh ledgers.
Exact symbol/variable lines: docs/CODE_INDEX.md. No optimizer, physical controller or remote inputs.
"""

import copy
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from gridlab.dispatch import simulate
from gridlab.model import Settings, configuration, validate
from gridlab.reference import reference

ABS_TOL = 1e-7
REL_TOL = 1e-12
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def canonical(value: Any) -> bytes:
    """Serialize stable finite ASCII JSON; identity is content integrity, not authorship."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def audit(rows: list[dict[str, Any]], data: dict[str, Any]) -> float:
    """Independently reconstruct balances and enforce bounds, availability, and dispatch exclusivity."""
    c = data["config"]
    previous = float(c["initial_wh"])
    maximum = 0.0
    if len(rows) != len(data["profile"]):
        raise RuntimeError("Missing dispatch intervals")
    for hour, (r, p) in enumerate(zip(rows, data["profile"], strict=True)):
        if (
            r["hour"] != hour
            or r["battery_available"] != p["battery_available"]
            or any(
                not math.isfinite(value) for key, value in r.items() if key != "battery_available"
            )
        ):
            raise RuntimeError("Invalid interval structure")
        if any(
            value < -ABS_TOL
            for key, value in r.items()
            if key.endswith("_wh") and "residual" not in key
        ):
            raise RuntimeError("Negative energy")
        critical = r["renewable_critical_wh"] + r["grid_critical_wh"] + r["battery_critical_wh"]
        flexible = r["renewable_flexible_wh"] + r["grid_flexible_wh"] + r["battery_flexible_wh"]
        charge = r["charge_renewable_wh"] + r["charge_grid_wh"]
        discharge = r["battery_critical_wh"] + r["battery_flexible_wh"]
        imported = r["grid_critical_wh"] + r["grid_flexible_wh"] + r["charge_grid_wh"]
        eta_c, eta_d = c["charge_eff_permille"] / 1000, c["discharge_eff_permille"] / 1000
        residuals = [
            r["start_wh"] - previous,
            critical + r["critical_unserved_wh"] - p["critical_w"],
            flexible + r["flexible_unserved_wh"] - p["flexible_w"],
            p["solar_w"]
            + p["wind_w"]
            + imported
            + discharge
            - critical
            - flexible
            - charge
            - r["curtailed_wh"],
            r["end_wh"] - r["start_wh"] - charge * eta_c + discharge / eta_d,
            p["solar_w"]
            + p["wind_w"]
            + imported
            + r["start_wh"]
            - critical
            - flexible
            - r["curtailed_wh"]
            - r["end_wh"]
            - r["charge_loss_wh"]
            - r["discharge_loss_wh"],
            r["charge_loss_wh"] - charge * (1 - eta_c),
            r["discharge_loss_wh"] - discharge * (1 / eta_d - 1),
        ]
        maximum = max(maximum, *(abs(value) for value in residuals))
        if (
            maximum > ABS_TOL
            or r["end_wh"] < -ABS_TOL
            or r["end_wh"] > c["capacity_wh"] + ABS_TOL
            or charge > c["charge_limit_w"] + ABS_TOL
            or discharge > c["discharge_limit_w"] + ABS_TOL
            or imported > p["grid_limit_w"] + ABS_TOL
        ):
            raise RuntimeError("Energy or capacity ledger failed")
        if (
            charge > ABS_TOL
            and discharge > ABS_TOL
            or not p["battery_available"]
            and charge + discharge > ABS_TOL
        ):
            raise RuntimeError("Invalid simultaneous/unavailable battery flow")
        if not c["precharge"] and r["charge_grid_wh"] > ABS_TOL:
            raise RuntimeError("Unrequested feeder top-up")
        # Flexible discharge must stop at reserve after critical battery service.
        if (
            c["policy"]
            and r["battery_flexible_wh"] > ABS_TOL
            and r["end_wh"] + ABS_TOL < c["capacity_wh"] * c["reserve_pct"] / 100
        ):
            raise RuntimeError("Flexible load consumed protected reserve")
        previous = r["end_wh"]
    return maximum


def summarize(rows: list[dict[str, Any]], config: dict[str, int]) -> dict[str, Any]:
    """Aggregate energy/service metrics; zero demand has unavailable coverage, not an invented score."""

    def total(key: str) -> float:
        """Sum a named energy ledger over all hourly intervals."""
        return sum(float(r[key]) for r in rows)

    demand = total("critical_demand_wh")
    critical_unserved = total("critical_unserved_wh")
    failures = [r["hour"] for r in rows if r["critical_unserved_wh"] > ABS_TOL]
    consecutive = longest = 0
    for r in rows:
        consecutive = consecutive + 1 if r["critical_unserved_wh"] > ABS_TOL else 0
        longest = max(longest, consecutive)
    seen_outage = False
    recovery = None
    for r in rows:
        if r["grid_limit_wh"] == 0:
            seen_outage = True
        elif (
            seen_outage
            and recovery is None
            and r["end_wh"] + ABS_TOL >= config["capacity_wh"] * config["reserve_pct"] / 100
            and r["critical_unserved_wh"] <= ABS_TOL
        ):
            recovery = r["hour"]
    values = {
        "hours": len(rows),
        "critical_demand_wh": demand,
        "critical_unserved_wh": critical_unserved,
        "flexible_unserved_wh": total("flexible_unserved_wh"),
        "critical_service_pct": 100 * (demand - critical_unserved) / demand if demand else None,
        "first_critical_shortfall_hour": failures[0] if failures else None,
        "critical_shortfall_hours": len(failures),
        "longest_critical_shortfall_run_hours": longest,
        "outage_hours": sum(r["grid_limit_wh"] == 0 for r in rows),
        "fully_served_critical_outage_hours": sum(
            r["grid_limit_wh"] == 0
            and r["critical_demand_wh"] > 0
            and r["critical_unserved_wh"] <= ABS_TOL
            for r in rows
        ),
        "reserve_recovery_hour": recovery,
        "generation_wh": total("solar_wh") + total("wind_wh"),
        "grid_import_wh": total("grid_critical_wh")
        + total("grid_flexible_wh")
        + total("charge_grid_wh"),
        "curtailed_wh": total("curtailed_wh"),
        "loss_wh": total("charge_loss_wh") + total("discharge_loss_wh"),
        "end_wh": rows[-1]["end_wh"],
        "min_wh": min(config["initial_wh"], *(r["end_wh"] for r in rows)),
        "direct_renewable_service_wh": total("renewable_critical_wh")
        + total("renewable_flexible_wh"),
    }
    return {
        key: round(value, 6) if type(value) is float else value for key, value in values.items()
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    """Compare every field to exact rational computation, then gate independently rebuilt energy ledgers."""
    rows = simulate(data)
    expected = reference(data)
    if len(rows) != len(expected) or any(
        set(a) != set(b)
        or any(not math.isclose(a[key], b[key], rel_tol=REL_TOL, abs_tol=ABS_TOL) for key in a)
        for a, b in zip(rows, expected, strict=True)
    ):
        raise RuntimeError("Rational reference disagreement")
    residual = audit(rows, data)
    return {
        "policy": data["config"]["policy"],
        "rows": [
            {key: round(value, 9) if type(value) is float else value for key, value in row.items()}
            for row in rows
        ],
        "summary": summarize(rows, data["config"]),
        "verification": {
            "reference_verified": True,
            "energy_ledgers_verified": True,
            "max_residual_wh": round(residual, 12),
            "absolute_tolerance_wh": ABS_TOL,
            "relative_tolerance": REL_TOL,
        },
    }


def analyze(data: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    """Evaluate both policies from identical initial state/profile; neither is claimed universally best."""
    validate(data)
    selected = evaluate(data)
    other = copy.deepcopy(data)
    other["config"]["policy"] = 1 - data["config"]["policy"]
    comparison = evaluate(other)
    run: dict[str, Any] = {
        "schema": 1,
        "name": data["name"],
        "author": "Jason Stys",
        "settings": asdict(settings) if settings else None,
        "input": data,
        "selected": selected,
        "comparison": comparison,
        "method": {
            "interval_hours": 1,
            "data": "Synthetic hourly average powers; no measured weather or facility telemetry",
            "model": "Single AC bus, capacity/rate limits, separate charge/discharge efficiencies and prioritized energy dispatch",
            "reference": "Independent load-first Fraction arithmetic; production uses source-first floats",
            "limits": "No AC/DC power flow, voltage/frequency, protection, switching transients, battery chemistry/aging, forecast, optimal scheduling, cost/emissions calculation or real device control. Hourly adequacy is not electrical safety or guaranteed outage survival.",
        },
    }
    run["id"] = hashlib.sha256(canonical(run)).hexdigest()
    return run


def build_run(settings: Settings) -> dict[str, Any]:
    """Evaluate the finite preset and its counterfactual policy under the same supplied profile."""
    return analyze(configuration(settings), settings)
