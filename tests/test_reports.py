"""Inert exports, immutable local SQL and CLI behavior by Jason Stys. Index: docs/CODE_INDEX.md."""

import csv
import io
import json
import sqlite3
from contextlib import closing

import pytest

from gridlab.__main__ import main
from gridlab.engine import analyze, build_run, canonical
from gridlab.model import Settings, configuration
from gridlab.reports import export_report, save_history


def test_exports():
    """JSON replays, CSV preserves both policies, HTML escapes provenance and unknown formats fail."""
    data = configuration(Settings())
    data["provenance"] = '<img src=x onerror="alert(1)"><script>bad</script>'
    run = analyze(data)
    assert json.loads(export_report(run, "json")[0]) == run
    assert json.loads(export_report(run, "input")[0]) == data
    rows = list(csv.DictReader(io.StringIO(export_report(run, "csv")[0].decode())))
    assert len(rows) == 96
    assert {r["policy"] for r in rows} == {"0", "1"}
    assert float(rows[0]["start_wh"]) == 10000
    body = export_report(run, "html")[0]
    assert b"<script>" not in body and b"<img " not in body and b"&lt;img" in body
    with pytest.raises(ValueError):
        export_report(run, "exe")


def test_immutable_history(tmp_path):
    """Identity is verified before storage; rows are idempotent, immutable and capped without pruning."""
    path = tmp_path / "private.sqlite3"
    run = build_run(Settings())
    save_history(path, run)
    save_history(path, run)
    with closing(sqlite3.connect(path)) as db, db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1
        assert json.loads(db.execute("SELECT report_json FROM runs").fetchone()[0]) == run
        for sql in ("DELETE FROM runs", "UPDATE runs SET report_json='{}'"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql)
        for i in range(99):
            db.execute(
                "INSERT INTO runs(id,report_json) VALUES(?,?)",
                (f"{i:064x}", canonical(run).decode()),
            )
    other = build_run(Settings(scenario="clear-day"))
    with pytest.raises(ValueError, match="History full"):
        save_history(path, other)
    run["author"] = "altered"
    with pytest.raises(ValueError, match="identity"):
        save_history(path, run)
    path.unlink()  # proves the Windows SQLite connection was closed


def test_cli_exports_and_errors(tmp_path, monkeypatch):
    """Explicit local output is create-only; input/errors never execute or overwrite data."""
    path = tmp_path / "evidence.json"
    assert (
        main(["export", "--output", str(path), "--history", str(tmp_path / "history.sqlite3")]) == 0
    )
    assert main(["export", "--output", str(path)]) == 1
    data = configuration(Settings(scenario="zero-demand"))
    source = tmp_path / "input.json"
    source.write_bytes(canonical(data))
    replay = tmp_path / "replay.json"
    assert main(["export", "--input", str(source), "--output", str(replay)]) == 0
    assert json.loads(replay.read_bytes())["selected"]["summary"]["critical_service_pct"] is None
    assert (
        main(["export", "--input", str(tmp_path / "absent"), "--output", str(tmp_path / "no.json")])
        == 1
    )
    monkeypatch.setattr("gridlab.__main__.ROOT", tmp_path)
    assert main(["serve", "--no-browser"]) == 1
