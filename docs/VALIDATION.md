# Validation strategy and evidence

## Gates and scope

The production algorithm and separate rational implementation are compared field-by-field on **every report**, for both policies. Independent energy audits and analytical cases test the shared model assumptions. This proves internal model consistency within tolerance, not calibration against real electrical equipment. No measured dataset or hardware was used.

Python tests cover all648 finite settings,100 deterministic Hypothesis profiles, schema/type/range/file-size/duplicate/UTF/nesting rejection, exact reserve/rate/loss/headroom examples, feeder top-up/battery trip, nullable zero-demand/recovery, oracle/audit fault injection, both-policy exports, SQL immutability/idempotence/cap/connection close, CLI create-only replay, real HTTP headers/method/origin/traversal/query/error routes. Branch-inclusive coverage gate is90%; tests and warnings are strict. Case contracts freeze all summaries for six default paired scenarios in `reports/benchmark.json`; deliberate model changes require numerical review before regeneration. This baseline is a regression contract, not external truth.

Browser tests exercise actual production-built UI in Chromium/Firefox/WebKit: real reports/charts, control invalidation/counterfactual/download settings, all four real downloads, no-demand case, tripped-hour inspection, failed/malformed responses, stale responses, inert hostile provenance, keyboard/mobile layout, axe WCAG2A/AA/2.1AA checks and API security rejections. Automated accessibility does not replace a manual assistive-technology audit. Responsive layout is not a native mobile installer claim.

## Local checkpoint

Windows, Python3.14.6 / Node24.18.1: **784 Python tests passed**, **96.26% branch-inclusive coverage**, **43 browser-unit tests passed**, strict mypy passed, **30/30 real browser tests passed** (10 each in Chromium, Firefox and WebKit), including zero detected axe violations in the tested mobile state. Both dependency audits reported no known vulnerabilities. Local frozen Windows executable passed actual CLI/export/replay/SQL/notices/HTTP smoke checks. Six paired benchmark contracts passed in **0.207s**, peak **435036 bytes** tracked Python allocation for that run; not total process RSS or a cross-machine speed guarantee. Exact hosted/release results are published in release notes only after completion. No real infrastructure integration, physical uncertainty analysis or real-time performance certification was performed.

## Hosted matrix

Validation: four model jobs (Ubuntu Python3.12/3.14, Windows/macOS Python3.14), one Linux three-browser job and three native portable build/smoke jobs. CodeQL: Python and JavaScript/TypeScript security-and-quality queries; inspect open findings separately from upload/job status. Dependency audits and lock/hash install are required. Portable release: exact-commit successful Validation+CodeQL gate then three OS builds/smokes, uploading ZIPs/checksums to a **draft Release**, not Actions artifacts. Default permissions read-only; only release jobs get contents-write and CodeQL security-events-write. Action refs are pinned SHA, credential persistence/caches disabled, no artifact uploads.

## Reproduce

Run README commands. `python -m tools.benchmark` checks contracts and prints informational time/allocation. `--write` deliberately regenerates baselines; inspect numerical changes, never auto-accept drift in CI. `python tools/verify_repo.py --write` regenerates exact-line/file indexes; CI checks for drift without writing. `python tools/package_app.py` builds/smokes the actual executable before ZIP creation.

The first local HTTP test attempt failed in a test helper because `HTTPConnection` is not a context manager. It was corrected to explicit `contextlib.closing`; the full suite then passed without changing HTTP safeguards. Review also caught automatic JSON encoding detection inconsistent with the documented UTF-8-only input; decoding is now explicit and a UTF-16 regression test rejects it. A168-slot boundary/zero-rate/unity-efficiency test was added. No coverage exclusions, skipped platforms or relaxed security tests were added to hide failures.

## Release acceptance

Require successful exact-SHA8 Validation jobs and2 CodeQL jobs, zero reviewed open findings, then4 release jobs. Download all three ZIPs/checksums, verify GitHub asset digest and checksum, CRC and confined ZIP members/notices/assets; execute the downloaded Windows app, replay input and run three-browser acceptance against it. Linux/macOS actual execution occurs on their CI runners; local Windows is not claimed as manual testing on those OSes. Record IDs/SHA/digests/results in release notes before publishing. Unsigned releases remain subject to OS warnings. Public Actions logs carry test output; no private account/cache/run data is copied into the repo.
