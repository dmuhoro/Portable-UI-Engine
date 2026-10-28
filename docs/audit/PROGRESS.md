# PROGRESS – Task Queue

## Tasks

| ID | Title | Depends On | Acceptance Criteria | Verification Cmd | Files Likely Touched | Risk | Status |
|----|-------|------------|----------------------|------------------|----------------------|------|--------|
| T1 | Export `PaymentMethod` type and wire UI | none | `src/lib/types.ts` exports `PaymentMethod`; `src/screens/PaymentMethodsScreen.tsx` compiles and UI shows methods. | `npm run build` succeeds; UI renders without console errors. | `src/lib/types.ts`, `src/screens/PaymentMethodsScreen.tsx` | Low | TODO |
| T2 | Fix AdminScreen JSX parsing & add admin‑role guard | none | JSX parses, `npm run typecheck` passes, admin view only visible when `useStore.getState().role === 'admin'`. | `npm run typecheck` passes; manual dev check that non‑admin cannot access AdminScreen. | `src/screens/AdminScreen.tsx`, `src/lib/store.ts` | Medium | TODO |
| T3 | Commit clean state | T1,T2 | No modified files (`git status --porcelain` empty). | `git status --porcelain` shows nothing. | all modified files | Low | TODO |
| T4 | Write user guide | T3 | `docs/user-guide.md` exists, linked from README. | `cat docs/user-guide.md` shows content. | `docs/user-guide.md`, `README.md` | Low | TODO |
| T5 | Write deployment runbook | T3 | `docs/deployment-runbook.md` with backup/rollback steps. | `cat docs/deployment-runbook.md` shows content. | `docs/deployment-runbook.md` | Low | TODO |
| T6 | Lint & type‑check cleanup | T3 | `npm run lint` and `npm run typecheck` pass. | run both commands. | all source files | Low | TODO |
| T7 | Add admin‑role to store (if missing) | none | `useStore` includes `role` field default `'user'`. | `npm run typecheck` passes. | `src/lib/store.ts` | Low | TODO |
| T8 | Update CI to enforce lint/typecheck | T6 | GitHub Actions step runs lint & typecheck; local `npm run ci` (if script) passes. | run CI script. | `.github/workflows/*` | Low | TODO |
| T9 | Add unit test for payment method storage | T1 | Test inserts a method, reads back correctly. | `npm run test:run` passes new test. | `src/lib/paymentMethod.test.ts` | Low | TODO |
