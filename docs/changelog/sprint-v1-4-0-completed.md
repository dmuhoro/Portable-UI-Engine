# Sprint v1.4.0 — Digital Receipts, Customers, WhatsApp, Inventory

**Date:** 2026-07-19  
**Version:** 1.4.0  
**Status:** Completed ✅

## Objective
Add digital receipts with WhatsApp sharing, build a customer intelligence system, and introduce inventory management — turning Daftari from a simple ledger into a business operations tool.

## Scope

### Digital Receipt System
- Auto-generated receipt IDs (`RCT-XXXXXX`) per income transaction via `receiptId.ts`
- Receipt modal (`Receipt.tsx`) shown after every sale — business name, date, amount, receipt ID, item
- "Share via WhatsApp" button on receipt modal
- `receipt_id` stored on transactions in Dexie
- Unit tests for receipt ID generation

### Customer Intelligence
- New `customers` Dexie table (schema v4): `name`, `phone`, `total_visits`, `total_spent`, `last_visit`, `created_at`
- Auto-save customer from M-Pesa SMS sender on every transaction (deduplication by phone)
- Customer stats accumulate: visit count, total spent, last visit date
- Manual customer creation in `CustomersScreen`

### Customers Screen
- Searchable customer list with all saved customers
- Sort by total spent (highest first)
- Per-customer stats row: total visits, total spent, last visit
- Tappable rows (placeholder for Customer 360° in v2.0.0)
- Dashboard customer count card

### WhatsApp Sharing
- `whatsapp.ts` utility: constructs `wa.me` deep links with pre-filled message body
- Receipt modal "Share via WhatsApp" sends formatted receipt text
- Daily close summary can be shared as WhatsApp message
- Architecture Decision Record: `ADR-009-whatsapp-sharing.md`

### Inventory Management
- Stock fields (`stock`, `low_stock_threshold`) on every product
- Stock auto-decrements when a sale is recorded from a product chip
- Low-stock alert banner on ProductCatalogScreen (stock ≤ threshold)
- Restock dialog with quantity input
- Dashboard low-stock warning pill

### Data Model
- DB v4: `customers` table, `receipt_id` on transactions
- Indexed by `&name`, `phone` on customers

### i18n
- 18 new keys across sw.json and en.json (receipt, share_whatsapp, customers, customer_saved, inventory, stock, low_stock, restock, total_visits, total_spent)

## Files Created
- `src/components/Receipt.tsx` — receipt modal component
- `src/screens/CustomersScreen.tsx` — customer list with search/sort
- `src/lib/receiptId.ts` — receipt ID generator
- `src/lib/receiptId.test.ts` — receipt ID unit tests
- `src/lib/whatsapp.ts` — WhatsApp deep link utility
- `docs/adr/ADR-009-whatsapp-sharing.md` — WhatsApp architecture

## Files Modified
- `src/lib/db.ts` — schema v4 (customers table, receipt_id)
- `src/lib/store.ts` — receipt_id on addTransaction
- `src/lib/constants.ts` — new table name constants
- `src/lib/types.ts` — receipt_id + customer fields
- `src/screens/ProductCatalogScreen.tsx` — stock, restock, low-stock alerts
- `src/screens/DashboardScreen.tsx` — customer count, low-stock card
- `src/screens/HistoryScreen.tsx` — receipt view per transaction
- `src/components/AppShell.tsx` — customers route
- `src/components/SuccessFlash.tsx` — receipt preview after sale
- `src/features/transactions/RecordSale.tsx` — auto-save customer, decrement stock
- `src/features/sms/SMSParser.tsx` — extract sender for customer creation
- `src/features/sync/syncQueue.ts` — receipt_id in queue payload
- `.github/workflows/ci.yml` — workflow refactored
- CHANGELOG.md, README.md — updated

## Verification
- 24 files changed, 877 insertions, 169 deletions
- Receipt ID generation tested with unit tests
- SMS parser extracts sender for customer auto-creation
- Stock decrements correctly on product-linked sales
- WhatsApp deep links open correct chat with pre-filled message
- i18n: 18 new keys in both languages
- DB migration v3→v4: customers table + receipt_id migration

## Dependencies
- Sprint v1.3.0 (CI/CD, SMS parser hardening, engineering standards)
- Sprint v1.2.0 (business categories, product catalog, personalized dashboard)

## Next
- Sprint v1.5.0: Auth polish, Sentry, analytics, beta prep
