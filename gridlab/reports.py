"""Inert evidence exports and optional private history by Jason Stys.

Functions: export_report, save_history. Variables: columns, identity, bound SQL. Index: docs/CODE_INDEX.md.
No input code is executed; SQLite is local and unencrypted, never an account store.
"""

import csv
import hashlib
import html
import io
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from gridlab.engine import canonical


def export_report(run: dict[str, Any], format_name: str) -> tuple[bytes, str]:
    """Export full two-policy evidence, input, all hourly rows or escaped script-free HTML."""
    if format_name == "json":
        return canonical(run), "application/json"
    if format_name == "input":
        return canonical(run["input"]), "application/json"
    if format_name == "csv":
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        columns = list(run["selected"]["rows"][0])
        writer.writerow(["policy", *columns])
        for result in (run["selected"], run["comparison"]):
            for row in result["rows"]:
                writer.writerow([result["policy"], *(row[key] for key in columns)])
        return buffer.getvalue().encode(), "text/csv"
    if format_name != "html":
        raise ValueError("Unknown format")
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Energy evidence · Jason Stys</title><h1>Resilient Energy Microgrid Lab</h1><p>By Jason Stys. Synthetic hourly energy adequacy is not electrical safety, calibrated performance or guaranteed outage survival. No real infrastructure is controlled.</p><pre>'
        + html.escape(canonical(run).decode())
        + "</pre></html>"
    ).encode(), "text/html"


def save_history(path: Path, run: dict[str, Any]) -> None:
    """Verify report identity and create an immutable, idempotent local record; refuse auto-pruning."""
    body = dict(run)
    identity = body.pop("id", None)
    if not isinstance(identity, str) or hashlib.sha256(canonical(body)).hexdigest() != identity:
        raise ValueError("Report identity mismatch")
    schema = (Path(__file__).parent / "resources/history.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(schema)
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM runs WHERE id=?", (identity,)).fetchone():
            return
        if connection.execute("SELECT count(*) FROM runs").fetchone()[0] >= 100:
            raise ValueError("History full; choose a new local file")
        connection.execute(
            "INSERT INTO runs(id,report_json) VALUES(?,?)", (identity, canonical(run).decode())
        )
