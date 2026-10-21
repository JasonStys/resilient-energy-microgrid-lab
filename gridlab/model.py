"""Strict hourly energy profiles by Jason Stys.

Types: Settings. Functions: catalog, configuration, validate, unique_object, load_input.
Parameters/variables and exact line locations: docs/CODE_INDEX.md. All profile data is invented.
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CASES = {
    "feeder-outage": "Research station / feeder outage",
    "clear-day": "Clear weather / connected",
    "winter-drought": "Low renewable output / long outage",
    "load-surge": "Critical load surge / constrained feeder",
    "battery-trip": "Battery unavailable / isolated hours",
    "zero-demand": "No demand / curtailment control",
}
CHOICES = {
    "policy": (0, 1),
    "capacity": (10000, 20000, 40000),
    "reserve": (0, 25, 50),
    "initial": (25, 50, 75),
    "precharge": (0, 1),
}
CONFIG_RANGES = {
    "capacity_wh": (1, 100000),
    "initial_wh": (0, 100000),
    "reserve_pct": (0, 100),
    "charge_limit_w": (0, 50000),
    "discharge_limit_w": (0, 50000),
    "charge_eff_permille": (500, 1000),
    "discharge_eff_permille": (500, 1000),
    "policy": (0, 1),
    "precharge": (0, 1),
}
PROFILE_FIELDS = (
    "solar_w",
    "wind_w",
    "critical_w",
    "flexible_w",
    "grid_limit_w",
    "battery_available",
)


@dataclass(frozen=True)
class Settings:
    """Finite controls: Wh capacity, percent reserves/start, 0/1 policy and feeder top-up."""

    scenario: str = "feeder-outage"
    policy: int = 1
    capacity: int = 20000
    reserve: int = 25
    initial: int = 50
    precharge: int = 0

    def __post_init__(self) -> None:
        """Reject unknown scenarios, booleans-as-integers and unsupported finite controls."""
        if (
            not isinstance(self.scenario, str)
            or self.scenario not in CASES
            or any(
                type(getattr(self, key)) is not int or getattr(self, key) not in values
                for key, values in CHOICES.items()
            )
        ):
            raise ValueError("Unsupported experiment setting")


def catalog() -> dict[str, Any]:
    """Expose finite labels and defaults without executable, upload or remote-source options."""
    return {"cases": CASES, "choices": CHOICES, "defaults": asdict(Settings())}


def configuration(settings: Settings) -> dict[str, Any]:
    """Construct a fictional 48-hour station; hourly average watts integrate to Wh over each slot."""
    solar_day = (
        0,
        0,
        0,
        0,
        0,
        0,
        200,
        1000,
        3000,
        6000,
        9000,
        11000,
        12000,
        11000,
        9000,
        6000,
        3000,
        1000,
        200,
        0,
        0,
        0,
        0,
        0,
    )
    profile = []
    for hour in range(48):
        local = hour % 24
        solar = solar_day[local]
        wind = (900, 1500, 2100, 1200, 600, 1800)[hour % 6]
        critical = 3000 + (500 if 8 <= local < 18 else 0)
        flexible = 3500 if 8 <= local < 20 else 1800
        grid = 8000
        available = True
        if settings.scenario in ("feeder-outage", "battery-trip") and 16 <= hour < 36:
            grid = 0
        if settings.scenario == "winter-drought":
            solar //= 8
            wind //= 4
            if 12 <= hour < 42:
                grid = 0
        if settings.scenario == "load-surge" and 14 <= hour < 30:
            grid = 1000
            if 20 <= hour < 25:
                critical *= 3
        if settings.scenario == "battery-trip" and 20 <= hour < 28:
            available = False
        if settings.scenario == "zero-demand":
            critical = flexible = 0
        profile.append(
            dict(
                zip(PROFILE_FIELDS, (solar, wind, critical, flexible, grid, available), strict=True)
            )
        )
    config = {
        "capacity_wh": settings.capacity,
        "initial_wh": settings.capacity * settings.initial // 100,
        "reserve_pct": settings.reserve,
        "charge_limit_w": 5000,
        "discharge_limit_w": 5000,
        "charge_eff_permille": 950,
        "discharge_eff_permille": 900,
        "policy": settings.policy,
        "precharge": settings.precharge,
    }
    return {
        "schema": 1,
        "name": settings.scenario,
        "provenance": "Invented hourly research-station profile by Jason Stys; not measured weather, facility telemetry or a forecast.",
        "config": config,
        "profile": profile,
    }


def validate(data: Any) -> dict[str, Any]:
    """Enforce exact schemas, finite integer ranges and compatible energy state before dispatch."""
    if (
        not isinstance(data, dict)
        or set(data) != {"schema", "name", "provenance", "config", "profile"}
        or type(data["schema"]) is not int
        or data["schema"] != 1
    ):
        raise ValueError("Invalid input schema")
    if not isinstance(data["name"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,47}", data["name"]
    ):
        raise ValueError("Invalid scenario name")
    if not isinstance(data["provenance"], str) or not 1 <= len(data["provenance"]) <= 240:
        raise ValueError("Missing or excessive provenance")
    config, profile = data["config"], data["profile"]
    if not isinstance(config, dict) or set(config) != set(CONFIG_RANGES):
        raise ValueError("Invalid configuration fields")
    for key, (low, high) in CONFIG_RANGES.items():
        if type(config[key]) is not int or not low <= config[key] <= high:
            raise ValueError("Parameter outside supported range")
    if config["initial_wh"] > config["capacity_wh"]:
        raise ValueError("Initial energy exceeds capacity")
    if not isinstance(profile, list) or not 1 <= len(profile) <= 168:
        raise ValueError("Profile must contain 1..168 hourly slots")
    for row in profile:
        if (
            not isinstance(row, dict)
            or set(row) != set(PROFILE_FIELDS)
            or type(row["battery_available"]) is not bool
        ):
            raise ValueError("Invalid hourly profile fields")
        if any(
            type(row[key]) is not int or not 0 <= row[key] <= 50000 for key in PROFILE_FIELDS[:-1]
        ):
            raise ValueError("Invalid hourly average power")
    return data


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys rather than silently taking the last interpretation."""
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Duplicate JSON key")
        out[key] = value
    return out


def load_input(path: Path) -> dict[str, Any]:
    """Read at most 64 KiB of explicit local JSON; no scripts, remote URLs or browser uploads."""
    with path.open("rb") as stream:
        body = stream.read(65537)
    if len(body) > 65536:
        raise ValueError("Input file too large")
    try:
        return validate(json.loads(body.decode("utf-8"), object_pairs_hook=unique_object))
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ValueError("Malformed JSON") from error
