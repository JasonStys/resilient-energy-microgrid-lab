# Full-window feeder-loss validation — 2026-11-09

Windows / Python3.14.6:786 Python tests passed with96.33% combined statement/branch coverage. A hand-computed one-hour case shows zero initial storage/renewables and10W critical plus4W flexible demand: feeder loss adds exactly10Wh critical and4Wh flexible shortfall and removes14Wh import. All cases validate both stressed rational-reference/energy-audit traces, replay the exact derived input and prove original input immutability. No-demand coverage remains undefined.

Forty-three TypeScript tests, strict build and33 actual Chromium/Firefox/WebKit browser tests passed, including a real derived-input download, original-replay separation, both policies, accessibility, strict HTTP boundaries and failure/stale-response handling. Ruff, strict mypy, formatting/source indexes and six unchanged paired benchmark summaries pass. Locked advisory audits report no known Python vulnerabilities and zero npm vulnerabilities.

Stress changes only supplied hourly feeder availability; it is not a forecast or a guaranteed outage-survival result. Hourly adequacy does not establish power-flow/protection/transient or electrical safety. No infrastructure controls or real facility input are added. Parent handles review, remote Actions and cross-platform portable builds; this child did not push or trigger workflows.
