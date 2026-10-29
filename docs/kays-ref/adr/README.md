# ADR Index

> Architectural Decision Records for the Kay's Wellness Centre engine.
> Decisions D1–D12 live in `docs/decisions.md` (pre-ADR). Formal ADRs start at 013.

| # | Title | Status |
|---|-------|--------|
| 013 | Engine consolidation — kays-wellness-centre is the single engine | Accepted |
| 014 | M-Pesa STK Push adoption (greenleaf as schema donor) | Accepted |
| 015 | PII encryption wired into write/read paths (D11 reversal) | Accepted |
| 016 | Pilot deployment topology | Accepted |

## Linking Convention

- ADRs reference each other and decisions.md entries.
- A change that contradicts an ADR must supersede it in the same commit.
- The `docs/decisions.md` doc is the legacy log; new decisions use `docs/adr/`.