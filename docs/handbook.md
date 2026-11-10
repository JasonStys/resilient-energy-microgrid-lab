# Resilient Energy Microgrid Lab · FIELDGRID handbook

By Jason Stys.

Compare synthetic energy dispatch, storage and outage scenarios with explicit load priorities, battery limits and balance checks. Use the model for software and planning demonstrations rather than physical grid control.

Rehearse full-window feeder loss, compare two dispatch policies and download the derived replay input through 1.1 portable apps.

Lets a reviewer investigate service/storage tradeoffs with the same original assumptions and independently checked energy accounting, using an extracted package rather than a development environment.

## Read the documentation

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions. The workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [MODEL](MODEL.md)

### Security and validation

- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`39a16658fbb68bc2558aea4bf60ab74253ef2aba`](https://github.com/JasonStys/resilient-energy-microgrid-lab/tree/39a16658fbb68bc2558aea4bf60ab74253ef2aba). The observed functional workflow baseline is `39a16658fbb68bc2558aea4bf60ab74253ef2aba`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_RELEASE_20261109.md)
- [Current Actions](https://github.com/JasonStys/resilient-energy-microgrid-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Synthetic hourly adequacy is not power flow, protection/transient behavior, a forecast or electrical safety.
- Stress removes supplied feeder availability across the whole window; it does not guarantee outage survival or optimize a real facility.
- Unsigned local portable desktop packages; no system installer, native mobile application or real infrastructure controls.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
