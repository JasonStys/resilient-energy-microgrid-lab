"""Input boundaries and complete finite control verification by Jason Stys. Index: docs/CODE_INDEX.md."""

import copy
import itertools
import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gridlab.engine import analyze, build_run
from gridlab.model import (
    CASES,
    CHOICES,
    CONFIG_RANGES,
    Settings,
    configuration,
    load_input,
    validate,
)


@pytest.mark.parametrize("values", list(itertools.product(CASES, *CHOICES.values())))
def test_every_control(values):
    """Both policy traces must pass the rational oracle and energy invariants for all 648 presets."""
    run = build_run(Settings(*values))
    for result in (run["selected"], run["comparison"]):
        assert result["verification"]["reference_verified"]
        assert result["verification"]["energy_ledgers_verified"]
        assert result["verification"]["max_residual_wh"] <= 1e-7
        assert len(result["rows"]) == 48


@pytest.mark.parametrize("key", CONFIG_RANGES)
@pytest.mark.parametrize("bad", [None, True, "1", 1.5, -1, 100001])
def test_config_rejections(key, bad):
    """Every scalar rejects wrong types and values rather than coercing ambiguous input."""
    data = configuration(Settings())
    data["config"][key] = bad
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("key", CHOICES)
def test_settings_reject_bool(key):
    """Boolean is not a supported integer control even though Python subclasses int."""
    with pytest.raises(ValueError):
        Settings(**{key: True})


@pytest.mark.parametrize("case", range(15))
def test_schema_rejections(case):
    """Exact objects, name/provenance bounds, profile size and primitive types are enforced."""
    data = configuration(Settings())
    if case == 0:
        data["extra"] = 1
    elif case == 1:
        data["schema"] = True
    elif case == 2:
        data["name"] = "../escape"
    elif case == 3:
        data["provenance"] = ""
    elif case == 4:
        data["provenance"] = "a" * 241
    elif case == 5:
        data["config"] = []
    elif case == 6:
        data["config"]["initial_wh"] = 50000
    elif case == 7:
        data["profile"] = []
    elif case == 8:
        data["profile"] *= 4
    elif case == 9:
        data["profile"][0] = []
    elif case == 10:
        data["profile"][0]["battery_available"] = 1
    elif case == 11:
        data["profile"][0]["solar_w"] = True
    elif case == 12:
        data["profile"][0]["solar_w"] = 50001
    elif case == 13:
        data["profile"][0].pop("wind_w")
    else:
        data = None
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("kind", ["size", "syntax", "utf8", "duplicate", "depth"])
def test_file_rejections(tmp_path, kind):
    """Bounded local input rejects oversized, malformed, ambiguous and deeply nested JSON."""
    payloads = {
        "size": b" " * 65537,
        "syntax": b"{",
        "utf8": b"\xff",
        "duplicate": b'{"x":1,"x":2}',
        "depth": b"[" * 2000,
    }
    path = tmp_path / "input.json"
    path.write_bytes(payloads[kind])
    with pytest.raises(ValueError):
        load_input(path)


def test_replay(tmp_path):
    """Canonical input can be edited locally and replayed without a browser or remote source."""
    data = configuration(Settings())
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_input(path) == data
    assert analyze(data)["input"] == data


def test_utf16_rejected(tmp_path):
    """The documented UTF-8-only format must not silently auto-detect other JSON encodings."""
    path = tmp_path / "utf16.json"
    path.write_bytes(json.dumps(configuration(Settings())).encode("utf-16"))
    with pytest.raises(ValueError, match="Malformed JSON"):
        load_input(path)


def test_maximum_profile_and_boundary_rates():
    """The supported 168-slot boundary works with zero and unity conversion/rate edges."""
    data = configuration(Settings())
    data["profile"] = (data["profile"] * 4)[:168]
    data["config"].update(
        charge_limit_w=0, discharge_limit_w=0, charge_eff_permille=1000, discharge_eff_permille=1000
    )
    run = analyze(data)
    assert len(run["selected"]["rows"]) == 168
    assert all(row["end_wh"] == data["config"]["initial_wh"] for row in run["selected"]["rows"])


@settings(max_examples=100, deadline=None, derandomize=True)
@given(
    st.lists(
        st.tuples(
            st.integers(0, 50000),
            st.integers(0, 50000),
            st.integers(0, 50000),
            st.integers(0, 50000),
            st.integers(0, 50000),
            st.booleans(),
        ),
        min_size=1,
        max_size=24,
    ),
    st.integers(1, 100000),
    st.integers(0, 100),
    st.integers(0, 100),
    st.integers(500, 1000),
    st.integers(500, 1000),
    st.integers(0, 50000),
    st.integers(0, 50000),
    st.integers(0, 1),
)
def test_generated_profiles(
    profile, capacity, initial, reserve, charge_eff, discharge_eff, charge, discharge, topup
):
    """Generated bounded profiles exercise both algorithms across efficiencies, rates and availability."""
    data = copy.deepcopy(configuration(Settings()))
    data["profile"] = [dict(zip(data["profile"][0], row, strict=True)) for row in profile]
    data["config"].update(
        capacity_wh=capacity,
        initial_wh=capacity * initial // 100,
        reserve_pct=reserve,
        charge_eff_permille=charge_eff,
        discharge_eff_permille=discharge_eff,
        charge_limit_w=charge,
        discharge_limit_w=discharge,
        precharge=topup,
    )
    assert analyze(data)["selected"]["verification"]["reference_verified"]
