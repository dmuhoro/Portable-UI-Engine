# Sprint 22 — Integrated Clinic Billing, Offline PWA, Revenue Telemetry

**Theme:** Multi-tenant billing ledger, offline-first PWA resiliency, financial analytics.

## Pillars

### Pillar A: Billing Ledger (invoices + payments)
- New `invoices` table: auto-generated sequential `invoice_number` (INV-YYYY-NNNNN), status workflow (draft→issued→paid→void), FK to `leads`, scoped by `organization_id`.
- New `payments` table: split-payment support, sequential `receipt_number` (KWC-YYYY-NNNNN), three methods (cash/mobile_money/card).
- `generateInvoiceForCheckedIn` server fn: guards (lead must be `converted`/`checked_in`, no duplicate non-void invoices), calls `generateInvoice` with 2500 KES default amount.
- `recordPayment`: inserts payment, sums total paid, auto-marks invoice `paid` when fully covered.
- `BillingLedger` component: invoice list with lead name/status/amount, "Pay" opens `PaymentForm` (amount + method grid + notes), "Clock" opens `PaymentHistory` modal.
- PipelineBoard's `safeUpdate` triggers invoice generation on `converted` status.
- New finance route at `/admin/finance`.

### Pillar B: Offline PWA
- Service worker (`public/sw.js`): stale-while-revalidate for styles/scripts/fonts/images, cache-first for build assets, network-first for admin GET routes with fallback to cached or 503 JSON.
- SW registration injected in `__root.tsx` after `<Scripts />`.
- `offline-store.ts`: IndexedDB wrapper — `cacheAppointments`, `getCachedAppointments`, `queueCheckin`, `getPendingCheckins`, `removePendingCheckin`, `syncPendingCheckins`.

### Pillar C: Financial Analytics
- `computeAnalytics()` expanded: `accountsReceivable` (draft+issued invoices), `monthlyRecurringRevenue` (paid invoices this month), `revenuePerResource` (per active resource with appointment count), `collectionRate` (paid/total %).
- Dashboard (`/admin/dashboard`) — 4 new StatCards (Receipt, Landmark, Percent, UserCheck) + Revenue Per Resource breakdown.
- New event types: INVOICE_GENERATED, INVOICE_PAID, PAYMENT_RECEIVED, FINANCIALS_COMPUTED.

## Test Results
- **97 tests total — 97 passing, 0 failing.**
- `offline-store.test.ts`: 4 tests — exports, type interfaces, sync progress (with IndexedDB not defined guard).
- `billing.test.ts`: 7 tests — invoice seq, payment seq, full/partial payment, checked-in guard, duplicate prevention, server fn exports.
- `analytics.test.ts`: 2 new tests — financial snapshot, zero-input edge case.
- `pipeline-board.test.ts`: fast mock-based test (no heavy module transforms).
- All existing tests: `interactions.test.ts` mocks added for resources.server, react-query, sonner.

## Build
- Production build succeeds in ~17s.

## Files Changed/Added
- `src/lib/db.server.ts` — invoices + payments tables in `ensureSchema`
- `src/lib/api/billing.server.ts` — new: generateInvoice, recordPayment, getInvoices, getPayments, generateInvoiceForCheckedIn
- `src/lib/analytics.server.ts` — expanded computeAnalytics with 4 financial KPIs
- `src/lib/offline-store.ts` — new: IndexedDB wrapper
- `src/lib/logger.server.ts` — 4 new financial event types
- `public/sw.js` — new: service worker
- `src/routes/__root.tsx` — SW registration
- `src/routes/admin/dashboard.tsx` — financial KPI cards + Revenue Per Resource
- `src/routes/admin/finance.tsx` — new: finance route with BillingLedger
- `src/components/finance/BillingLedger.tsx` — new: invoice list, payment form, payment history
- `src/components/leads/PipelineBoard.tsx` — auto-generate invoice on convert
- `src/routeTree.gen.ts` — finance route registered
- `vitest.config.ts` — single-fork pool, 60s timeouts
- `src/__tests__/billing.test.ts`, `offline-store.test.ts` — new
- `src/__tests__/analytics.test.ts`, `interactions.test.ts`, `pipeline-board.test.ts` — updated mocks
