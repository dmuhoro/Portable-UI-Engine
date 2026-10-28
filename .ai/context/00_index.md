# KWC AI Context Index

> Machine-readable context for AI agents working in this repository.
> Each numbered file is a self-contained brief. Read `00_index.md` first, then the files relevant to
> the task. All claims are cross-checked against source as of the pilot-hardening sprint.

## Files

| # | File | Purpose |
|---|------|---------|
| 00 | `00_index.md` | This file. Navigation map. |
| 01 | `01_architecture.md` | System architecture, request lifecycle, server file map. |
| 02 | `02_system-map.md` | File locations, route structure, where code lives. |
| 03 | `03_domain-model.md` | Entities, tenant-scoping verdicts, money model. |
| 04 | `04_code-standards.md` | Conventions for server functions, SQL, Zod, tests. |
| 05 | `05_db-contracts.md` | Table contracts, tenant columns, writers, coupling risks. |
| 06 | `06_decisions.md` | ADR log (D1–D12+) and superseded decisions. |
| 07 | `07_release-readiness.md` | Go/no-go table for the pilot. Blocker list. |
| 08 | `08_security.md` | Security model, auth flow, tenant isolation invariants. |
| 09 | `09_security-subsystems.md` | Encryption, webhooks, rate limiting, fallback. |
| 10 | `10_roadmap.md` | Current layer, next layers, completion criteria. |
| 11 | `11_workflow-rules.md` | The Constitution + AGENTS.md rules condensed. |
| 12 | `12_evidence.md` | Evidence log index and how to record evidence. |

## Canonical Source

The single source of truth is `docs/` at the repository root. The `.ai/context/` files are
**summaries + pointers**, never standalone truth. If a summary contradicts `docs/`, the `docs/`
file wins and the `.ai/` summary should be corrected.

## Agent Boot Sequence

1. Read `00_index.md`
2. Read `11_workflow-rules.md` (rules that govern how you may act)
3. Read `01_architecture.md` + `02_system-map.md` (where things are)
4. For the specific task: read the relevant domain file (03/05/06/07/08/09)
5. Before touching tenant-scoping or money code, re-read the invariant sections in `08_security.md`