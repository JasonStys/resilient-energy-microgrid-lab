# User guide and troubleshooting

## First experiment

Launch the extracted application or `python -m gridlab serve`. The browser opens an ephemeral `127.0.0.1` port. No login, subscriptions, external scripts or Internet access are required at runtime. Keep the console open; Ctrl+C stops the server. For a fixed local port use `serve --port 8946 --no-browser`, then open its printed URL.

Start with feeder outage. Change capacity, initial energy, reserve percentage, policy or feeder top-up; **Compare policies** recomputes both policies from the same initial state/profile. Old evidence is hidden immediately on control changes. Green means internal accounting/reference checks passed, not real-system safety. The comparison table exposes tradeoffs rather than a winner label. Use the hour slider to inspect generation, imports, battery flows, served/unserved loads, curtailed generation and losses. Charts share a capacity scale; shaded storage-chart slots have zero feeder availability. Dashed horizontal line is the flexible-load reserve, not a guaranteed state minimum.

Try winter drought: zero final battery energy with top-up off is intentional; connected feeder serves demand before battery and only renewable surplus charges. Enable feeder top-up and compare imports/recovery. Try battery trip and inspect hour22: no battery flows even if stored energy exists. Zero-demand coverage is “Not applicable,” not 100%.

## Downloads and custom data

JSON contains full input, both traces and checks. CSV has 96 rows for a 48-slot profile, distinguished by `policy`; it includes every hourly ledger field. HTML is escaped/script-free evidence. INPUT is editable strict JSON accepted by CLI; there is intentionally no browser upload.

```text
python -m gridlab export --format input --output editable.json
# Edit your synthetic profile with a text editor; preserve the strict schema.
python -m gridlab export --input editable.json --output replay.json --history history.sqlite3
python -m gridlab export --input editable.json --format html --output replay.html
```

Files are create-only; choose another path if it exists. Custom input accepts 1..168 hourly slots, integer bounded values and provenance, no units inferred from strings. CLI custom reports have `settings:null`; the source input is their full configuration. See [API/schema](API.md). Histories are local unencrypted SQLite, append-only/idempotent within this application and capped at100 unique reports. At capacity choose a new file; the application never prunes automatically. OS-level access can still alter/delete your local files.

## Common problems

- **No verified evidence:** retry; check console and finite inputs. No stale chart is treated as current.
- **Missing built UI:** source users run `npm ci` and `npm run build` from repository root.
- **Input rejected:** exact field names/types, no duplicate keys, ≤64KiB, UTF-8, no URL. Use a fresh exported INPUT as a template.
- **Forbidden origin:** use the exact printed `http://127.0.0.1:PORT/` address, not an external hostname, iframe or proxy.
- **App fails after moving executable:** extract/retain the whole folder including `_internal`; executable alone is insufficient.
- **OS security warning:** this portfolio build is unsigned. Verify checksums/source and follow your platform/organization's policy; do not disable security controls.
- **Browser/table on mobile:** responsive browser layout is supported, but distributed native binaries target desktop OS/architecture only. Focus/scroll the named comparison region to view all columns.

Help: [issues](https://github.com/JasonStys/resilient-energy-microgrid-lab/issues) and [Jason Stys](https://github.com/JasonStys). Do not include sensitive facility data, account details or secrets in issues. Consult qualified engineers for real electrical systems; this simulator is not an operational instrument.
