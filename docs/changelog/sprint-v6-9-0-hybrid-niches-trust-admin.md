# Sprint v6.9.0 — Hybrid Niches + Receiving Accounts + CEO Dashboard + Scale Hardening

**Status:** Completed — all gates green.

## Objective

Deliver the approved owner-vision audit (v6.8.0) in four implementation corridors:
(1) hybrid multi-niche module, (2) receiving-account trust foundation, (3) Admin CEO
dashboard with realistic server-side metrics, (4) sync scale hardening — all on top of
four live migrations pushed to `rjedivbpldkroffswoyb`, with docs, CHANGELOG and a 6.9.0
version bump.

## Work completed

### Hybrid multi-niche (L1/L2)
- `daftari_businesses` gains `categories`, `subcategories`, `receiving_accounts` jsonb columns
  (migration `20260923000000`, idempotent, pushed live).
- Data model: `Business` gains the three fields end-to-end (`db.ts`, `store.ts`, `businessId.ts`
  `mapBusinessToStore`), shared `asJsonString()` (JSONB→string), pull-side `normalizeRemoteBusiness`
  in `syncAll.ts`, and the same normalization on realtime business upserts in `realtimeApply.ts`.
- `businessCategories.ts` aggregation layer: `resolveActiveCategories`, `resolveActivePairs`,
  `aggregateIncomeCategories`, `aggregateTemplateProducts` (dedupe, legacy fallback). Wired into
  `RecordSale` (income category selector) and `ProductCatalogScreen` (template products).
- Onboarding keeps a per-category primary while persisting full `categories`/`subcategories`
  arrays. 18 unit tests for the hybrid module (mocks updated across feature tests).

### Receiving accounts (L3)
- `receivingAccount.ts` per-method validation contract (`cash`/`card_pos` exempt; phone
  (M-Pesa/Airtel), pochi, till, paybill, bank rules) + 8 unit tests. Fail-closed: methods that need
  an account always surface an error when it is missing.
- Onboarding **Step 7** "Where will customers send money?": one receiving account per selected
  method, submit disabled until every account-requiring method is valid; push-permission step
  renumbered to 8.
- Settings payment-methods row un-gated from `VITE_ADMIN_USER_ID` (was a bug: only impostor
  "admins" saw it); `PaymentMethodsScreen` now loads/saves `receiving_accounts`; verified
  receiving-account display added to `BusinessProfileScreen`.
- **Sync correctness fix**: `repository.updateBusiness` now sets `synced: 0` so business edits
  re-upload (silent-local-divergence bug) — updated existing test.

### Admin CEO dashboard (L4)
- Migrations `20260923000001` (tables + `is_admin()` security-definer + `admin_metrics()` RPC +
  RLS policies for `daftari_presence`, `daftari_payment_confirmations`) and `20260923000003`
  (paged `admin_businesses()` RPC + `record_presence()` heartbeat) — pushed live.
- `src/lib/admin.ts` fail-closed RPC client: admin, metrics, businesses, presence. Any error → not
  admin / empty data; never wide-open.
- Role is **server-authoritative**: `App.tsx` resolves it via `is_admin()` on session (never the
  client env flag); store role reset to `user` on sign-out.
- `AdminScreen` rewritten off the RPCs (revenue, profit, businesses, online-now via
  `daftari_presence`, 7d chart, paged "Load more"/`admin_businesses`), heartbeat via
  `usePresenceHeartbeat` (60s + visibility change), Settings admin row gated on role.
- `AdminScreen.test.tsx` (4 tests) proves the server gate and paging path; role guard remains
  fail-closed ("Not authorized", no data fetched).

### Scale hardening (L5)
- Migration `20260923000002`: indexes on transactions/presence/payment-confirmations + realtime
  publication self-heal.
- `syncAll.ts` push: chunked bulk upserts (50/batch, concurrency 4) with per-row fallback when the
  atomic statement fails — preserves record-level accounting; `onConflict: local_id` keeps retries
  idempotent. Pull: prefetch-into-Map newest-wins + `bulkPut` (was O(n) row-by-row
  where.first() walks). `syncAll.test.ts` updated to assert the batched calls.

## Final gate state (v6.9.0)

typecheck ✅ · lint ✅ · check-i18n ✅ (306 keys) · test:run ✅ 50 files / 490 · build ✅ ·
migrations pushed ✅ (local == remote, 15/15)

## Notes

- Daraja STK/C2B remains deferred; the trust-engine foundation ships as the receiving-account
  contract + `daftari_payment_confirmations` ledger (schema only).
- Admin seeding is a one-liner the owner runs in the SQL editor:
  `insert into public.daftari_admin_users (user_id) values ('<owner-auth-uid>');`
  (owner UUID is not present in the repo, by design).
- `scripts/load-test.js` (k6) remains authored but not runnable locally — k6 is not installed.