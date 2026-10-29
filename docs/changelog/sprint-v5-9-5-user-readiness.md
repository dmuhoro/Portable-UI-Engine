# Sprint: User-Readiness — Close All 6 Business-Type Coverage Gaps

**Version:** 5.9.5
**Date:** 2026-08-24
**Theme:** Close the remaining business-type gaps so every target user (food vendor, shopkeeper, grocery, mobile accessories, repair, cyber cafe) can onboard and start tracking day one.

## Ground truth (before this sprint)
- 4 of 6 target business types were covered (`food_beverage`, `retail > kiosk_duka`); cereal/grocery and mobile accessories were only *partial* (via `electronics` / `kiosk_duka`), and **phone/computer repair** and **cyber cafes** were entirely **missing**.
- `daftari_push_subscriptions` was referenced by `src/lib/repository.ts` (`upsertPushSubscription` / `deletePushSubscription`) and `src/lib/pushNotifications.ts` but had **no Supabase migration** — cloud push-subscription storage would silently no-op.

## Layer 1 — Missing Supabase migration

### Added
- `supabase/migrations/20260824000000_create_push_subscriptions.sql`: creates `daftari_push_subscriptions` (`user_id` unique FK → `auth.users`, `subscription` text, `created_at`), RLS `owner_only_push_subscriptions` (owner_id = auth.uid()), index on `user_id`.

### Note (audit correction)
- `daftari_sync_queue` is a **local-only Dexie table** (queues upserts to the six entity tables). It does **not** require a Supabase table — the earlier audit claim that it needed a migration was incorrect and is not being actioned.

## Layer 2-4 — Business-type coverage (all 6 target types)

All changes are additive **subcategories** within the existing 7-category ADR-005 architecture (no icon/emoji/dashboard-label/type-union churn).

### retail
- **`grocery`** (Mboga na Nafaka / Grocery & Cereals): mchele, unga mahindi, unga ngano, maharage, njegere, mbaazi, cooking oil, sugar, salt, maji
- **`mobile_accessories`** (Vifaa vya Simu / Mobile Accessories): charger, earphones, case, screen guard, USB cable, power bank, bluetooth speaker, pouch

### services
- **`phone_computer_repair`** (Ukarabati wa Simu na Kompyuta / Phone & Computer Repair): screen replacement, battery, charging port, software install, unlock, computer repair, OS reinstall, format, backup, speaker fix
- **`cyber_cafe`** (Cyber / Intaneti / Cyber Cafe): browsing, B&W/colour printing, photocopy, scanning, typing/CV, lamination, passport photo, M-Pesa help

## Layer 5 — Evidence / tests

### Added
- `src/lib/businessCategories.test.ts`: 14 tests proving all 6 target types resolve to a category + subcategory and each has a non-empty, valid template-product list; plus category integrity (emoji + dashboard label present, `getCategoryLabels` parity).

## Layer 6 — Cloud-sync schema reconciliation (user_id ownership model)

Connecting the Supabase CLI exposed that the remote project's `daftari_businesses` / `daftari_transactions` (and the 5 business-scoped tables) carried a **legacy schema** (`owner_id`, `type`) that did not match what `syncAll.ts` writes (`user_id`, `category`, `products`, `payment_methods`, `business_id` = business `local_id`, ...). As a result, cloud upserts errored and businesses/transactions never backed up.

### Added
- `supabase/migrations/20260825000000_reconcile_user_id_schema.sql` — idempotent reconciliation:
  - Adds missing sync columns to `daftari_businesses` (user_id, owner_name, category, subcategory, payment_methods, products, updated_at, synced) and `daftari_transactions` (user_id, synced, payment_method, receipt_id, product_id, cost_price, updated_at).
  - Drops legacy `NOT NULL` on `owner_id` (app writes `user_id`) and `daftari_transactions.business_id` (app field is optional).
  - Rewrites RLS to the user_id model: `user_id = auth.uid()` for businesses/transactions/push_subscriptions; `business_id ∈ (user's business local_ids)` for customers, daily_closes, suppliers, purchase_orders, stock_adjustments.
  - Applied to the live project via the Supabase Management API; verified with functional insert tests (rolled back; no residue).

### Reconciles migration history
- Recorded all out-of-band-applied migrations into `supabase_migrations.schema_migrations` so future `supabase db push` sees a clean, in-sync state.

## Verification (all green)
- `npm run typecheck` ✅
- `npm run lint` ✅
- `npx tsx scripts/check-i18n.ts` ✅ (202/202)
- `npm run test:run` ✅ 362/362 (32 files; +14 new)
- `npm run build` ✅ (PWA, 42 precache entries)
- Remote schema: all 10 `daftari_*` tables present, RLS enabled, functional insert tests pass for all 7 sync tables.

## Deliverables
- `docs/changelog/sprint-v5-9-5-user-readiness.md`
- `CHANGELOG.md` — `[5.9.5] — 2026-08-24`
- `supabase/migrations/20260824000000_create_push_subscriptions.sql`
- `supabase/migrations/20260825000000_reconcile_user_id_schema.sql`
