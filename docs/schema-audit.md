# Daftari — Supabase Schema Audit
Audited: 2026-07-22

## Dexie v7 Tables (local, all users have these)
| # | Dexie Table | Supabase Table | Migration Exists | RLS | Synced |
|---|---|---|---|---|---|
| 1 | transactions | daftari_transactions | ✅ 20260606100433 | ✅ | ✅ Push + Pull |
| 2 | business | daftari_businesses | ⚠️ ALTER only (20260618000000) | ✅ | ✅ Push + Pull |
| 3 | daily_closes | daftari_daily_closes | ❌ Missing | ❌ | ✅ Push + Pull |
| 4 | customers | daftari_customers | ❌ Missing | ❌ | ✅ Push + Pull |
| 5 | suppliers | daftari_suppliers | ❌ Missing | ❌ | ❌ Push / ✅ Pull |
| 6 | purchase_orders | daftari_purchase_orders | ❌ Missing | ❌ | ❌ Push / ✅ Pull |
| 7 | stock_adjustments | daftari_stock_adjustments | ❌ Missing | ❌ | ❌ Push / ✅ Pull |
| 8 | sync_queue | (local only) | N/A | N/A | N/A |

## syncAllTables() coverage (PUSH direction)
Currently pushes: transactions, businesses, daily_closes, customers (4/7)
Missing push: suppliers, purchase_orders, stock_adjustments (3/7)

## pullFromSupabase() coverage (PULL direction)
Pulls all 7 entity types: transactions, businesses, customers, daily_closes, suppliers, purchase_orders, stock_adjustments

## Risk Assessment
- **P0**: 5 tables exist in Dexie but have no Supabase migration — users who add suppliers, purchase orders, or stock adjustments will lose that data on device switch
- **P1**: daily_closes and customers have no RLS — any authenticated user could theoretically access another user's data if the table exists without RLS
- **P2**: businesses table was ALTER'd but never formally CREATE TABLE'd in migrations

## Resolution
Migration `20260722000000_create_missing_tables.sql` creates all 5 missing tables with proper RLS.
syncAllTables() extended to push all 7 entity types.
