# Sprint v4.0.0 — Inventory & Procurement OS

**Date:** 2026-07-19  
**Version:** 4.0.0  
**Status:** Completed ✅

## Objective
Transform Daftari into a complete inventory and procurement operating system for physical goods businesses. Add supplier management, purchase order workflow, stock adjustment auditing, and batch transaction entry.

## Scope

### Supplier Management
- **Suppliers table** in Dexie (schema v6): `name`, `phone`, `email`, `address`, `notes`
- **SuppliersScreen**: full CRUD list with search, add/edit modal, delete with confirmation
- **Settings link**: "Supplier Management" in Data & Reports section
- Supplier data synced to Supabase via sync queue

### Purchase Orders
- **PurchaseOrdersScreen**: list of all POs with status badges (draft/pending/partial/received/cancelled), date, supplier, total
- **Create PO flow**: select supplier (or none), add line items from product catalog, set quantity + unit cost + quantity received, auto-calculate totals
- **Receive PO flow**: tap a pending/partial PO → confirm receipt → stock auto-increments for each product → status updates to partial/received
- **PO Items stored as JSON** in the `items` field for multi-item orders
- Migration from v5 single-product POs to v6 multi-item POs

### Stock Adjustments
- **StockAdjustmentsScreen**: log all stock changes with reason codes
- **Adjustment reasons**: restock, wastage, spoilage, damage, theft, count correction, return, other
- **Free-text notes** for each adjustment
- **Audit trail**: every stock change recorded with timestamp, product, reason, quantity change
- Stock adjustments update actual product stock in the business products array

### Batch Entry Mode
- **BatchEntryScreen**: record multiple income or expense transactions without returning to the add screen
- Type selector (income/expense), amount, description fields
- Counter showing number of recorded transactions
- Quick successive recording — stays on the same form after each save

### Data Model (Schema v6)
- `suppliers` table: `local_id`, `business_id`, `name`, `phone`, `email`, `address`, `notes`, `created_at`, `updated_at`, `synced`
- `stock_adjustments` table: `local_id`, `business_id`, `product_id`, `product_name`, `quantity_change`, `reason`, `reason_text`, `notes`, `created_at`, `synced`
- `purchase_orders` redesigned: `items` (JSON array of PurchaseOrderItem), `status`, `supplier_id`, `supplier_name` — replaces single-product v5 schema
- Migration from v4→v5→v6: purchase_orders items converted from single fields to JSON array

### i18n
- 58 new keys across sw.json and en.json for suppliers, POs, stock adjustments, batch entry, inventory management

## Files Created
- `src/screens/SuppliersScreen.tsx` — supplier CRUD list
- `src/screens/PurchaseOrdersScreen.tsx` — PO list + create + receive flow
- `src/screens/StockAdjustmentsScreen.tsx` — stock adjustment with reasons
- `src/screens/BatchEntryScreen.tsx` — batch transaction entry

## Files Modified
- `src/lib/db.ts` — schema v6: suppliers, stock_adjustments, purchase_orders redesign, upgrade migration
- `src/components/AppShell.tsx` — added suppliers, purchase-orders, stock-adjustments, batch-entry routes
- `src/screens/SettingsScreen.tsx` — Inventory Management section with all 4 new links
- `src/i18n/sw.json` — 58 new keys
- `src/i18n/en.json` — 58 new keys
- `CHANGELOG.md` — v4.0.0 section
- `docs/changelog/sprint-v4-0-0-inventory-procurement-os.md` — this file

## Verification
- [x] TypeCheck: 0 errors
- [x] Tests: all pass
- [x] i18n linter: keys match 1:1
- [x] Build: succeeds, PWA generates
- [x] CHANGELOG.md updated
- [x] Sprint file created
- [x] Git: committed and pushed

## Dependencies
- Sprint v3.0.0 (multi-business, product profitability, sync all tables)
- Sprint v1.4.0 (inventory foundation, stock fields, customers)

## Next
- Receipt PDF generation + Bluetooth thermal printer support
- Barcode scanning for product lookup
- Cash flow forecasting and budgeting
- Multi-user / team access with roles
