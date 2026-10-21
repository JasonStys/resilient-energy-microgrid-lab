# Local API and input contract

The read-only IPv4 loopback service exposes `GET /api/health`, `/api/catalog`, `/api/run`, `/api/report`. All state-changing HTTP methods and HEAD are405. Exact Host `127.0.0.1:PORT`, absent/same Origin and non-cross-site fetch metadata are required; CORS is not enabled. Unknown/duplicate query fields reject400; maximum8 fields and1024 request-target characters. Static routes are `/`, `/index.html`, and exact built `/assets/NAME` with allowlisted suffixes, confined after symlink resolution. Source, dotfiles and arbitrary filesystem paths are not routes.

Run query defaults: `scenario=feeder-outage&policy=1&capacity=20000&reserve=25&initial=50&precharge=0`. Catalog supplies six scenario IDs and finite choices: policy0/1, capacity10000/20000/40000Wh, reserve0/25/50%, initial25/50/75%, precharge0/1. `/api/report` adds `format=json|csv|html|input` and returns a fixed attachment name. `format` is invalid on `/api/run`. Responses are no-store with CSP, no framing, nosniff and no-referrer. Invalid experiments400, forbidden origin403, path414, unknown route404 and internal verification/resource failure500 have generic messages and no traceback/partial evidence.

## CLI JSON exact schema

Root: exactly `schema` (integer1), `name` (1..48 lowercase ASCII alphanumeric/hyphen, starts alphanumeric), `provenance` (1..240 characters), `config`, `profile`. No extra keys, coercion, duplicate keys or code execution. Read≤65536bytes; malformed UTF/nesting/JSON rejects. Objects follow this example; a complete editable48-hour input is `examples/station.json`.

```json
{
  "schema": 1,
  "name": "example",
  "provenance": "Invented demonstration, not measured data",
  "config": {
    "capacity_wh": 20000,
    "initial_wh": 10000,
    "reserve_pct": 25,
    "charge_limit_w": 5000,
    "discharge_limit_w": 5000,
    "charge_eff_permille": 950,
    "discharge_eff_permille": 900,
    "policy": 1,
    "precharge": 0
  },
  "profile": [
    {
      "solar_w": 0,
      "wind_w": 900,
      "critical_w": 3000,
      "flexible_w": 1800,
      "grid_limit_w": 0,
      "battery_available": true
    }
  ]
}
```

Configuration exact integer bounds: capacity1..100000Wh; initial0..capacityWh; reserve0..100%; charge/discharge limits0..50000W; efficiencies500..1000permille; policy/precharge0..1. `profile` is1..168 exact hourly objects; the five power fields each integer0..50000W, `battery_available` strictly boolean. Booleans are not accepted for integer fields.

## Evidence

JSON includes schema, author, scenario name, optional GUI settings, full input, `selected`, `comparison`, method/limits and SHA-256`id`. Each policy includes rows, summary and reference/ledger status/tolerances. Rows include source/demand/split-service energies, battery availability and start/end, charge inputs, curtailed/unserved energies, losses and three residuals. All energy fields are Wh. Policy comparison is the opposite dispatch flag only; input is unchanged. CSV starts with policy then every hourly field for selected followed by comparison. Summary definitions and nullable fields are in [MODEL](MODEL.md). Identity hashes canonical finite sorted JSON excluding`id`; it is not a signature. Browser shape validation does not authenticate arbitrary responses or replace backend verification.
