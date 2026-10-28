# Sprint v3.0.0 — Multi-Business, Product Profitability & Supabase Restore

**Date:** 2026-07-19  
**Version:** 3.0.0  
**Status:** Completed ✅

## Objective
Transform Daftari into a true multi-business platform with per-product profitability tracking, data recovery via Supabase sync, and full data portability.

## Scope

### Multi-Business
- Business switcher dropdown in Dashboard header (visible when >1 business)
- "My Businesses" section in Settings with active business indicator
- "Add New Business" button in Settings (creates blank business record, reloads)
- All transactions scoped by `business_id` — each business has its own data
- Store: `businesses[]`, `activeBusinessId`, `setBusinesses`, `addBusiness`, `setActiveBusinessId`
- `App.tsx`: loads all businesses from Dexie, sets active from stored preference, falls back to first

### Product Profitability
- `cost_price` field on products in the product schema
- `product_id` and `cost_price` fields on transactions — links sales to products
- **ProductProfitabilityScreen**: per-product revenue, cost, margin (KES + %), units sold with horizontal bar chart (Recharts)
- **Dashboard card**: today's top-selling products with revenue/cost/margin breakdown
- **Settings link**: "Product Profitability" in Data & Reports section
- Margin = revenue - cost of goods sold per product

### Supabase Restore & Multi-Device Sync
- `lib/syncAll.ts`: `syncAllTables()` pushes all local records to Supabase, `pullFromSupabase()` restores from remote with last-write-wins conflict resolution
- All tables now sync: transactions, businesses, daily_closes, customers
- "Restore from Cloud" button in Settings → Data & Reports
- `updated_at` timestamps on all local tables for conflict resolution

### Data Model (Schema v5)
- `transactions`: added `business_id`, `product_id`, `cost_price`, `updated_at`
- `business`: added `local_id`, `updated_at`
- `daily_closes`: added `local_id`, `business_id`, `updated_at`
- `customers`: added `local_id`, `business_id`, `updated_at`
- New: `purchase_orders` table (`local_id`, `business_id`, `product_id`, `product_name`, `quantity`, `unit_cost`, `total_cost`, `notes`, `created_at`, `updated_at`, `synced`)
- Migration from v4 → v5: auto-generates `local_id` and `updated_at` for existing records

## Files Created
- `src/lib/syncAll.ts` — push/pull sync for all tables
- `src/screens/ProductProfitabilityScreen.tsx` — per-product P&L with bar chart

## Files Modified
- `src/lib/db.ts` — schema v5 with new fields and tables
- `src/lib/store.ts` — multi-business state, update transaction with sync fields
- `src/App.tsx` — load businesses, set active business
- `src/screens/DashboardScreen.tsx` — business switcher, product profitability card
- `src/screens/SettingsScreen.tsx` — My Businesses, Add Business, Product Profitability link, Restore from Cloud
- `src/components/AppShell.tsx` — product-profitability route
- `src/features/sync/syncQueue.ts` — extended QueuePayload
- `package.json` — version 2.0.0 → 3.0.0
- `CHANGELOG.md` — v3.0.0 section

## Verification
- [x] TypeCheck: 0 errors
- [x] Tests: 53/53 pass
- [x] i18n linter: 151 keys, perfect 1:1 match
- [x] Build: succeeds, PWA generates (44 precached entries)
- [x] CHANGELOG.md updated
- [x] Git: committed and pushed

## Dependencies
- Sprint v2.0.0 — edit/delete, search, monthly P&L, CSV, customer 360°, Fuliza

## Next
- Receipt PDF generation + Bluetooth thermal printer support
- Batch entry mode for power users
- Inventory purchase orders and stock adjustment logging
- Deep linking and URL-based routing
