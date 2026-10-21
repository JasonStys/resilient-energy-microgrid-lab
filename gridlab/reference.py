"""Independent exact-rational dispatch oracle by Jason Stys.

Function reference. Variables: Fraction energy, per-load resource budgets, losses and ledgers.
Line inventory: docs/CODE_INDEX.md. No production dispatch helpers are called.
"""

from fractions import Fraction as F
from typing import Any


def reference(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Allocate load-first with rational arithmetic; compare the same stated hourly specification."""
    c = data["config"]
    energy = F(c["initial_wh"])
    efficiency_in, efficiency_out = (
        F(c["charge_eff_permille"], 1000),
        F(c["discharge_eff_permille"], 1000),
    )
    floor = F(c["capacity_wh"] * c["reserve_pct"], 100) if c["policy"] else F(0)
    rows = []
    for hour, p in enumerate(data["profile"]):
        before = energy
        resources = [F(p["solar_w"] + p["wind_w"]), F(p["grid_limit_w"])]
        battery_budget = F(c["discharge_limit_w"]) if p["battery_available"] else F(0)
        allocation: list[list[F]] = []
        unserved = []
        # Load-first reference: complete critical demand before allocating flexible demand.
        for index, demand in enumerate((p["critical_w"], p["flexible_w"])):
            remaining = F(demand)
            service = []
            for source in range(2):
                amount = min(remaining, resources[source])
                remaining -= amount
                resources[source] -= amount
                service.append(amount)
            available = max(F(0), energy - (floor if index else F(0)))
            amount = min(remaining, battery_budget, available * efficiency_out)
            energy -= amount / efficiency_out
            battery_budget -= amount
            remaining -= amount
            service.append(amount)
            allocation.append(service)
            unserved.append(remaining)
        battery_out = allocation[0][2] + allocation[1][2]
        charging = [F(0), F(0)]
        charge_budget = F(c["charge_limit_w"])
        if p["battery_available"] and battery_out == 0:
            for source in range(2):
                if source == 1 and not c["precharge"]:
                    continue
                amount = min(
                    resources[source], charge_budget, (F(c["capacity_wh"]) - energy) / efficiency_in
                )
                resources[source] -= amount
                charge_budget -= amount
                energy += amount * efficiency_in
                charging[source] = amount
        rc, gc, bc = allocation[0]
        rf, gf, bf = allocation[1]
        cr, cg = charging
        served = sum(sum(service) for service in allocation)
        charge_in = sum(charging)
        loss_in = charge_in * (1 - efficiency_in)
        loss_out = battery_out * (1 / efficiency_out - 1)
        imported = gc + gf + cg
        generated = p["solar_w"] + p["wind_w"]
        row = {
            "hour": hour,
            "solar_wh": p["solar_w"],
            "wind_wh": p["wind_w"],
            "grid_limit_wh": p["grid_limit_w"],
            "battery_available": p["battery_available"],
            "critical_demand_wh": p["critical_w"],
            "flexible_demand_wh": p["flexible_w"],
            "start_wh": before,
            "end_wh": energy,
            "renewable_critical_wh": rc,
            "renewable_flexible_wh": rf,
            "grid_critical_wh": gc,
            "grid_flexible_wh": gf,
            "battery_critical_wh": bc,
            "battery_flexible_wh": bf,
            "charge_renewable_wh": cr,
            "charge_grid_wh": cg,
            "curtailed_wh": resources[0],
            "critical_unserved_wh": unserved[0],
            "flexible_unserved_wh": unserved[1],
            "charge_loss_wh": loss_in,
            "discharge_loss_wh": loss_out,
            "bus_residual_wh": generated
            + imported
            + battery_out
            - served
            - charge_in
            - resources[0],
            "storage_residual_wh": energy
            - before
            - charge_in * efficiency_in
            + battery_out / efficiency_out,
            "system_residual_wh": generated
            + imported
            + before
            - served
            - resources[0]
            - energy
            - loss_in
            - loss_out,
        }
        rows.append(
            {key: float(value) if isinstance(value, F) else value for key, value in row.items()}
        )
    return rows
