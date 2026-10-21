"""Hourly floating-point energy dispatch by Jason Stys.

Function simulate. Variables: stored Wh, source budgets, prioritized loads, conversions and losses.
Exact definitions/variable lines: docs/CODE_INDEX.md. No infrastructure interface or optimizer.
"""

from typing import Any


def simulate(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Allocate renewables, feeder and battery by source; charge only without discharge in a slot."""
    config = data["config"]
    stored = float(config["initial_wh"])
    capacity = config["capacity_wh"]
    reserve = capacity * config["reserve_pct"] / 100
    charge_eff = config["charge_eff_permille"] / 1000
    discharge_eff = config["discharge_eff_permille"] / 1000
    rows = []
    for hour, profile in enumerate(data["profile"]):
        start = stored
        renewable = float(profile["solar_w"] + profile["wind_w"])
        grid = float(profile["grid_limit_w"])
        critical = float(profile["critical_w"])
        flexible = float(profile["flexible_w"])
        # Source-first allocation: critical before flexible for every source.
        rc = min(renewable, critical)
        renewable -= rc
        critical -= rc
        rf = min(renewable, flexible)
        renewable -= rf
        flexible -= rf
        gc = min(grid, critical)
        grid -= gc
        critical -= gc
        gf = min(grid, flexible)
        grid -= gf
        flexible -= gf
        bc = bf = 0.0
        if profile["battery_available"]:
            bc = min(critical, float(config["discharge_limit_w"]), stored * discharge_eff)
            stored = max(0.0, stored - bc / discharge_eff)
            critical -= bc
            flexible_energy = max(0.0, stored - (reserve if config["policy"] else 0))
            bf = min(flexible, config["discharge_limit_w"] - bc, flexible_energy * discharge_eff)
            stored = max(0.0, stored - bf / discharge_eff)
            flexible -= bf
        cr = cg = 0.0
        if profile["battery_available"] and bc + bf == 0:
            cr = min(
                renewable, float(config["charge_limit_w"]), max(0.0, capacity - stored) / charge_eff
            )
            stored += cr * charge_eff
            renewable -= cr
            if config["precharge"]:
                cg = min(
                    grid, config["charge_limit_w"] - cr, max(0.0, capacity - stored) / charge_eff
                )
                stored += cg * charge_eff
                grid -= cg
        served = rc + rf + gc + gf + bc + bf
        charge = cr + cg
        delivered = bc + bf
        charge_loss = charge * (1 - charge_eff)
        discharge_loss = delivered * (1 / discharge_eff - 1)
        grid_import = gc + gf + cg
        generation = profile["solar_w"] + profile["wind_w"]
        rows.append(
            {
                "hour": hour,
                "solar_wh": profile["solar_w"],
                "wind_wh": profile["wind_w"],
                "grid_limit_wh": profile["grid_limit_w"],
                "battery_available": profile["battery_available"],
                "critical_demand_wh": profile["critical_w"],
                "flexible_demand_wh": profile["flexible_w"],
                "start_wh": start,
                "end_wh": stored,
                "renewable_critical_wh": rc,
                "renewable_flexible_wh": rf,
                "grid_critical_wh": gc,
                "grid_flexible_wh": gf,
                "battery_critical_wh": bc,
                "battery_flexible_wh": bf,
                "charge_renewable_wh": cr,
                "charge_grid_wh": cg,
                "curtailed_wh": renewable,
                "critical_unserved_wh": critical,
                "flexible_unserved_wh": flexible,
                "charge_loss_wh": charge_loss,
                "discharge_loss_wh": discharge_loss,
                "bus_residual_wh": generation
                + grid_import
                + delivered
                - served
                - charge
                - renewable,
                "storage_residual_wh": stored
                - start
                - charge * charge_eff
                + delivered / discharge_eff,
                "system_residual_wh": generation
                + grid_import
                + start
                - served
                - renewable
                - stored
                - charge_loss
                - discharge_loss,
            }
        )
    return rows
