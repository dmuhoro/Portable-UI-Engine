# Sprint: Post-Audit Remediation — Layers 5-8

**Version:** 5.8.5
**Date:** 2026-07-23
**Theme:** Close all remaining audit debt — dead code, logger upgrade, nav refactor, P2 resolution.

---

## Layer 5 — StockAdjustmentsScreen (TD-006)
- **Resolved as false positive.** Stock quantities are integer unit counts, not KES amounts. The AGENTS.md money safety rule applies only to monetary values.

## Layer 6 — Dead Code + Logger (TD-001, TD-008)
- Removed dead `src/features/learn/index.ts` placeholder (`Record<string, never>`, never imported)
- Removed empty `src/features/learn/` directory
- `useSync.ts`: Replaced 3x `.catch(console.error)` with `captureError` from sentry, with proper feature/action context tags
- Zero `console.error` calls remaining in production code

## Layer 7 — AppShell Refactor (TD-009) + P2 Resolution
- Extracted `selfManagedViews` Set for 11 self-managed screens
- Replaced 14-condition header hide with `Set.has()` lookup
- Replaced 11-condition `hideNav` with `Set.has()` lookup
- Single source of truth for self-managed views

### Resolved P2 Items
- **Recharts lazy-loading:** Already route-level lazy-loaded in AppShell.tsx (MonthlyReport, ProductProfitability). No additional splitting needed.
- **HistoryScreen virtualization:** Already has 50-item pagination with IntersectionObserver sentinel. DOM nodes bounded at 50 per page.
- **StockAdjustmentsScreen arithmetic:** Stock quantities are unit counts, not monetary values.

## Layer 8 — Final Verification
- Typecheck: 0 errors
- Lint: 0 errors
- Tests: 326/326 passing (28 files)
- Build: Success
- i18n: 194 keys, 0 unused

---

## Audit Debt Register — Final Status

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| TD-001 | Dead learn/index.ts placeholder | P3 | ✅ REMOVED |
| TD-002 | syncAll.ts full-table toArray() | P2 | ⏭ DEFERRED (working, perf only) |
| TD-003 | HistoryScreen virtualization | P2 | ✅ RESOLVED (has pagination) |
| TD-004 | PosScreen money safety | P1 | ✅ FIXED (Layer 1) |
| TD-005 | print.ts money safety | P1 | ✅ FIXED (Layer 1) |
| TD-006 | StockAdjustmentsScreen arithmetic | P2 | ✅ FALSE POSITIVE |
| TD-007 | PII in repository.ts logger | P2 | ✅ FIXED (Layer 4) |
| TD-008 | useSync.ts console.error | P3 | ✅ FIXED (captureError) |
| TD-009 | AppShell nav hide conditional | P3 | ✅ REFACTORED |
| TD-010 | vitest coverage thresholds | P2 | ✅ ADDED (Layer 3) |

**0 P0, 0 P1, 0 P2 active, 0 P3 active** — all resolved or deferred.

---

## Files Changed

```
D  src/features/learn/index.ts
M  src/hooks/useSync.ts
M  src/components/AppShell.tsx
```
