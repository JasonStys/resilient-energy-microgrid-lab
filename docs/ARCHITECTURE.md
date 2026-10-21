# Architecture and decisions

Jason Stys · status: implemented for bounded offline educational experiments.

```text
Local preset controls → strict Settings → synthetic hourly input
Explicit CLI JSON ─────────────────────→ strict schema
                                            ↓
                              source-first float dispatch
                              load-first Fraction reference
                                            ↓ every-field agreement
                            independent bus/store/system audit
                                            ↓
                          selected + opposite-policy evidence
                            ↙             ↓               ↘
                    TypeScript UI     inert exports     optional SQLite
```

## ADR 1: Python accounting and independent reference

Python makes energy equations/reviewable profile validation readable, with standard-library rational arithmetic, SQL, JSON, CSV and HTTP. Native optimization would add build complexity without need at 168 slots. Float production dispatch is O(n) time/O(n) stored trace space. Rational reference performs O(n) high-level operations, but arbitrary-precision arithmetic cost and denominator bit length can grow across intervals; it is not constant-cost O(n) in bit complexity. The strict 168-slot/range bound keeps validation practical, not a proof for unbounded input. Comparison evaluates two policies independently, not from a shared mutated state. Fraction arithmetic is an oracle for this model, not physical truth.

## ADR 2: TypeScript browser interface

Strict TypeScript guards response structure/finite values; HTML/CSS support accessible responsive UI; Canvas renders actual checked rows, not decorative curves. Numerical results use text nodes, not HTML interpolation. A generation counter prevents old responses from reviving stale evidence after controls change; invalid/failed results hide evidence/downloads. Exports are regenerated deterministically from the accepted settings. Browser view accepts only finite presets; custom input is CLI-only.

## ADR 3: Local read-only service and explicit persistence

HTTP binds only IPv4 loopback, rejects hostile Host/Origin/cross-site metadata, restricts routes/query size and never accepts uploads. SQL history is opt-in CLI only: bound parameters, content identity check, immutable update/delete triggers, 100-record cap, no automatic deletion. It is unencrypted and not an authentication system. Standard-library HTTP is for a single trusted local user, not a hardened public multiuser service or resource-exhaustion defense. Any local process/user already able to access this service may read synthetic results. No account is needed because no accounts or private data service are provided.

## ADR 4: Portable desktop ZIP and low-storage CI

PyInstaller onedir freezes CPython, reviewed source, built UI, SQL and runtime notices. Each supported OS builds and smokes its own native bundle. This is a portable local application using a browser UI, not a separately hosted website, signed installer or mobile app. Source setup is more complex but inspectable. Releases are draft-only until exact-commit Validation/CodeQL, open-findings review, release jobs, checksums and downloaded Windows/browser acceptance pass. Actions never upload artifacts/cache; releases store downloads separately. No credentials, user datasets or runtime histories enter Git.

## Extension seams and tradeoffs

Add a fictional scenario in `model`, adjusting tests/catalog/docs. Add physics only with explicit equations, new independent reference cases, validation data/provenance and narrower claims. Do not attach real control endpoints to this server. Adding forecasting/optimization requires explicit uncertainty/objectives, reproducible comparisons and different guarantees; naming a heuristic “optimal” is not a substitute. A live multiuser service would require a separate threat model, authentication, TLS, quotas and operational review.
