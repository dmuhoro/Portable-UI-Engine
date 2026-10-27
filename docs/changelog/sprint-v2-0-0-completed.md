# Sprint v2.0.0 — Business OS: Edit/Delete, Search, Monthly P&L, CSV Export, Customer 360°, Fuliza Tracking

**Date:** 2026-07-19  
**Version:** 2.0.0  
**Status:** Completed ✅

## Objective
Transform Daftari from a basic data-entry ledger into a business intelligence tool. Give SME owners the power to correct mistakes, find transactions, understand monthly profitability, export data, manage customers, and track Fuliza debt.

## Scope

### Pillar 1 — Data Control
- **Edit/Delete Transactions**: Hover/reveal edit and delete buttons on every row. Edit sheet allows changing amount, description, category, date, and time. Delete shows confirmation dialog with 4-second undo snackbar.
- **Smart Search + Filters**: Search across amount, description, category, and M-Pesa sender. Filter drawer with type chips (sales/expenses/withdrawals), category dropdown, payment method dropdown, and date range picker (from/to).
- **Infinite Scroll Pagination**: 50 transactions loaded at a time via Intersection Observer. No more freezing on busy dukas with thousands of transactions.
- **CSV Export**: Download all transactions as CSV from both HistoryScreen toolbar and SettingsScreen "Export CSV" row. Compatible with Excel/Google Sheets.

### Pillar 2 — Business Intelligence
- **Monthly P&L Report**: Dedicated screen with month navigator (prev/next), profit card with prior-month comparison %, daily profit bar chart (Recharts), and category breakdown donut charts for both revenue and expenses.
- **Enhanced Fuliza Dashboard**: Running total debt with estimated interest (5%), total taken vs. repaid breakdown, today's estimated Fuliza cost.

### Pillar 3 — Customer Operations
- **Customer 360° Detail Screen**: Tap any customer to see full transaction history, total spent, visit count, last visit date. Phone dial and WhatsApp buttons. Manual customer creation with name and phone number.
- **Add Customer Modal**: Quick-add form in CustomersScreen with name + optional phone.

## Data Layer
- `store.ts`: Added `updateTransaction` and `deleteTransaction` Zustand actions. Both write to Dexie, enqueue to Supabase sync queue, and optimistically update in-memory store. Delete supports undo via `undoDataRef`.
- `csv.ts`: New utility for generating CSV from transactions array and triggering download.

## Files Created
- `src/screens/MonthlyReportScreen.tsx` — monthly P&L with Recharts (bar + pie charts)
- `src/screens/CustomerDetailScreen.tsx` — customer 360° with transaction history and actions
- `src/lib/csv.ts` — CSV generation and download utility

## Files Modified
- `src/screens/HistoryScreen.tsx` — complete rewrite: edit/delete, search, filters, pagination, export
- `src/screens/DashboardScreen.tsx` — Fuliza section expanded with running balance, interest, cost
- `src/screens/CustomersScreen.tsx` — tappable rows navigate to CustomerDetailScreen, add-customer modal
- `src/screens/SettingsScreen.tsx` — new "Data & Reports" section with Monthly Report link and CSV export
- `src/components/AppShell.tsx` — added `monthly-report` route
- `src/lib/store.ts` — updateTransaction and deleteTransaction actions
- `src/i18n/sw.json` — 2 new keys (`monthly_report`, `transaction_deleted`)
- `src/i18n/en.json` — 2 new keys (`monthly_report`, `transaction_deleted`)
- `package.json` — version 1.5.0 → 2.0.0
- `CHANGELOG.md` — v2.0.0 section

## Verification
- [x] TypeCheck: 0 errors
- [x] Tests: 53/53 pass
- [x] i18n linter: 151 keys, perfect 1:1 match
- [x] Build: succeeds, PWA generates (41 precached entries)
- [x] CHANGELOG.md updated
- [x] Git: committed and pushed

## Dependencies
- Sprint v1.5.0 completed (auth polish, beta prep)

## Next
- Product-level profitability (link transactions to products for per-margin analysis)
- Receipt PDF generation and Bluetooth thermal printer support
- Multi-business switching
- Supabase pull-to-restore for data recovery
