# Sprint: Surgical Fix — Restore Integrity

**Version:** 5.7.0 → 5.8.0  
**Date:** 2026-07-22  
**Theme:** Fix what is broken. Add nothing new. Restore what was removed.

---

## SECTION A — Fix the Red Build

### A1 — Fix lint errors
- **referral.test.ts**: Replaced `any[]` with `unknown[]` in mock args
- **backup.test.ts**: Removed unused eslint-disable directives

### A2 — Pin tsx in devDependencies
- Installed `tsx` as devDependency for stable i18n CI
- Added `"check:i18n": "tsx scripts/check-i18n.ts"` to package.json scripts

### A3 — Remove 5 unused i18n keys
Keys removed from both `sw.json` and `en.json`:
- `change_category`
- `user_profile`
- `account_created`
- `last_sign_in`
- `signed_in_as`

Result: 197 → 192 keys in use, 0 unused.

### A4 — RecordSale.test.tsx
Already committed. No action needed.

---

## SECTION B — Fix the Supabase Schema Gap

### B1 — Schema audit documented
Created `docs/schema-audit.md` mapping all 8 Dexie tables to their Supabase equivalents, identifying 5 missing migrations and 3 missing push sync paths.

### B2 — Complete missing migrations
Created `supabase/migrations/20260722000000_create_missing_tables.sql`:
- `daftari_businesses` — proper CREATE TABLE (was only ALTER'd)
- `daftari_daily_closes` — new table with RLS
- `daftari_customers` — new table with RLS
- `daftari_suppliers` — new table with RLS
- `daftari_purchase_orders` — new table with RLS
- `daftari_stock_adjustments` — new table with RLS

All tables include: `local_id` unique constraint, `owner_id` UUID FK, RLS policies, proper indexes.

### B3 — syncAllTables() extended
Extended `syncAllTables()` in `src/lib/syncAll.ts` to push all 7 entity types:
- Previously pushed: transactions, businesses, daily_closes, customers (4/7)
- Now also pushes: **suppliers, purchase_orders, stock_adjustments** (7/7)

### B4 — Sync coverage documented
Created `ARCHITECTURE.md` with sync coverage matrix table showing all 7 entity types with push/pull/RLS status.

---

## SECTION C — Restore Type Safety

### C1 — Restore branded ID types
Added to `src/lib/types.ts`:
- `Brand<T, B>` generic type
- `TransactionId`, `BusinessId`, `UserId`, `LocalId` branded types
- `asLocalId()` helper

### C2 — Restore full money.ts
Expanded `src/lib/money.ts` from 2-line stub to full interface:
- `KES` branded type (prevents raw arithmetic on amounts)
- `KES_ZERO` constant
- `toKES()` — create branded KES value
- `kesAdd()` — safe addition
- `kesSubtract()` — safe subtraction
- `kesSum()` — sum array of KES amounts
- `formatKES()` — format as "KES 1,500"
- `formatKESCompact()` — compact format "KES 1.5k"
- `parseKESInput()` — parse user input, returns null if invalid
- `isProfit()` / `isLoss()` — business logic helpers

money.test.ts expanded from 3 tests to **30 tests** covering all functions and edge cases.

### C2 — AGENTS.md updated
Added `npm run check:i18n` to Commands section.

---

## SECTION D — Feature Freeze (Navigation Only)

### D1 — Settings screen reorganized
Replaced flat "Inventory Management" + "Data & Reports" sections with collapsible **"Zana za Biashara" / "Business Tools"** section:
- Default: **COLLAPSED**
- Contains: Suppliers, Purchase Orders, Stock Adjustments, Batch Entry, POS, Monthly Report, Product Profitability, CSV Export, Backup, Restore, Sync
- Core navigation (Business, My Products, Appearance) remains always visible

### D2 — ROADMAP.md created
Created `ROADMAP.md` with:
- North star metric
- Phase gates (Pilot Validation → Prove Retention → Monetize → Scale)
- Feature backlog (all advanced features listed, waiting for Phase 2+)

---

## CI Gate Results

| Stage | Status |
|-------|--------|
| `npm run typecheck` | ✅ 0 errors |
| `npm run lint` | ✅ 0 errors (1 warning) |
| `npm run test:run` | ✅ 285/285 passing (22 files) |
| `npm run check:i18n` | ✅ 0 unused keys (194 in use) |
| `npm run build` | ✅ 40 entries precached |

**Test growth:** 258 → 285 tests (+27 money.ts tests)

---

## Files Changed

```
A  ARCHITECTURE.md
A  ROADMAP.md
A  docs/schema-audit.md
A  supabase/migrations/20260722000000_create_missing_tables.sql
M  AGENTS.md
M  package.json                              (tsx, check:i18n script)
M  src/i18n/sw.json                          (-5 unused, +2 business_tools keys)
M  src/i18n/en.json                          (-5 unused, +2 business_tools keys)
M  src/lib/money.ts                          (2 → 69 lines, full interface)
M  src/lib/money.test.ts                     (3 → 30 tests)
M  src/lib/types.ts                          (+branded ID types)
M  src/lib/syncAll.ts                        (+3 entity push paths)
M  src/lib/referral.test.ts                  (lint fix)
M  src/lib/backup.test.ts                    (lint fix)
M  src/screens/SettingsScreen.tsx            (collapsible Business Tools)
```
