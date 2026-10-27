# Owner Vision Audit — v6.8.0 (2026-09-23)

Audit against the 6 owner questions. Evidence is file:line cited. No code was
changed during this audit. **Report back to owner before iterating.**

---

## Q1 — Can users tick off/add products & services they sell; onboarding fits their use-case?

**Status: LARGELY DONE (small gap).**

Evidence:
- `src/screens/ProductCatalogScreen.tsx:52-101` — users add products manually (name,
  price, unit, initial stock, low-stock alert), add category template products in one tap,
  restock, delete.
- `src/screens/OnboardingScreen.tsx:349-431` — onboarding picks category → subcategory;
  templates + expense/income categories are personalized per subcategory
  (`src/lib/businessCategories.ts` stores `templateProducts`, `expenseCategories`,
  `incomeCategories` per subcategory).
- `src/features/transactions/RecordSale.tsx:62-76` — quick-add buttons render the user's
  saved products; income category `service` exists (`RecordSale.tsx:40-42`), so services
  sell fine through the same path.

Gap (small): no product/service type distinction (a "service" is just an unfitted product);
`barcode` field exists in code but no UI to enter it (`ProductCatalogScreen.tsx:18`);
`cost_price` exists in store type (`store.ts:20`) but no catalog UI for it → Product
Profitability screen is under-fed. 

## Q2 — Hybrid/dynamic business (e.g. retail shop + cyber-cafe, multiple niches)?

**Status: PARTIAL — UI hints, data model is single-category.**

Evidence:
- Onboarding allows MULTI-select of categories into `selectedCategories`
  (`OnboardingScreen.tsx:81,369-394`), but `handleSubmit` only persists
  `selectedCategories[0]` as `category` and only stores `subcategory` when exactly one
  category is chosen (`OnboardingScreen.tsx:127-141`). The other categories are dropped.
- Data model is one `category` + one `subcategory` per business (`types.ts:88-116`;
  `db.ts:45-46`). ADR-005 documents single-category architecture.
- Multi-business is supported (`activeBusinessId`, `businesses[]`,
  `businessId.ts` resolve) — separate entities per user, not one hybrid entity.

So a retail-shop-cyber-cafe owner cannot represent both niches in one business: only the
first category's templates/expense categories apply.

## Q3 — Receiving-account stage (where customers send money) AFTER selecting methods, tied to the business; Daraja integration; circuit must not break in the real world.

**Status: UNBUILT — the single biggest market-blocking gap.**

Evidence:
- `PaymentMethodsScreen.tsx:12-55` is a bare checkbox toggle of enum labels saved as a
  JSON string on the business. There is NO field for the business's Till/Paybill/Pochi/
  Airtel/Bank account number anywhere — grepping for `account_number|till_number value|
  receiving` matches only a comment in `constants.ts:58`.
- No Daraja: `types.ts:71` `'daraja' // reserved — not built yet`. ADR-004 explicitly
  defers Daraja to Phase 2 (SMS paste is today's "confirmation"). The only Supabase Edge
  Function is `send-daily-close-push` — no STK/C2B push, no callback/webhook, no
  payment-confirmation circuit.
- Even subscription payments show a placeholder receiving number:
  `constants.ts:58-59` `MPESA_PAYMENT_NUMBER: 'YOUR_MPESA_NUMBER_HERE'`;
  `UpgradeScreen.tsx:196-215` tells users to send to that placeholder and self-report.
- SMS parsing (`features/sms/parseMpesa.ts`) is a *manual paste* path — it proves nothing
  upstream and can be broken by real-world SMS variants (best-effort regex).

## Q4 — Payment method detail: mpesa send-money→pochi, till, airtel money, paybill, bank transfer.

**Status: ALL LABELS EXIST → the "bank transfer missing" impression is a case of
labels-with-no-details.**

Evidence:
- Full enum: `types.ts:73-82` = cash, mpesa_send_money, pochi_la_biashara, till_number,
  paybill, airtel_money, bank_transfer, card_pos. So **bank_transfer and airtel_money DO
  exist** in code and render in RecordSale (`RecordSale.tsx:24-26`) and onboarding
  (`OnboardingScreen.tsx:34-35`).
- What's missing is per-method ACCOUNT DETAIL (which till number, which paybill account,
  which bank/account name) — same underlying gap as Q3. M-PESA send-money → "Pochi La
  Biashara" routing is just a tag; nothing routes to a real account.

## Q5 — Handle 100–1000 active users without crashing.

**Status: DEFENSIBLE ARCHITECTURE, UNPROVEN + known weaknesses.**

Evidence (positive):
- Supabase + RLS tenant isolation on every table
  (`20260722000000_create_missing_tables.sql:24-31` etc.).
- Offline-first Dexie reduces server load; paginated remote pull (PAGE_SIZE 500,
  `syncAll.ts:208-237`); per-user realtime postgres_changes with RLS-scoped filter
  (`useRealtimeSync.ts:34-53`).

Evidence (weak):
- `pullFromSupabase` writes remote rows one-by-one with an `await` per row
  (`syncAll.ts:246-249`) — O(n) round-trips to Dexie for large tenants.
- `syncAllTables` / `upsertToRemote` is sequential per record (`syncAll.ts:35-49`).
- `AdminScreen` loads ALL businesses + ALL transactions into memory and renders all
  (`AdminScreen.tsx:17-47`) — fine on a dev phone, not a 1000-user CEO view.
- Live migrations NOT applied to project `rjedivbpldkroffswoyb` (incl. realtime publica-
  tion `20260905210000_enable_realtime_tables.sql`) — realtime may not actually be live.
- k6 load script (`scripts/load-test.js`) only hammers the static landing shell; never
  exercises auth/sync; k6 not installed locally so it has never run.

## Q6 — Admin dashboard, CEO view: see users + real-time metrics.

**Status: SHELL EXISTS BUT UNREACHABLE + NOT REAL-TIME + CLIENT-LOCAL.**

Evidence:
- `AdminScreen.tsx` renders Revenue, Profit, Active Users, Revenue-7d, a bar chart, and a
  per-business list — the UI concept is there.
- **Unreachable:** role defaults to `'user'` (`store.ts:66`); nothing in production code
  ever calls `setRole('admin')` (only `AdminScreen.test.tsx:62`), and no view routes to
  `'admin'` (no `onNavigate('admin')`/`setView('admin')` anywhere — AppShell lists `admin`
  in `selfManagedViews` but nothing navigates to it).
- **Not real-time / not server-wide:** it computes from the *device's* local Dexie
  (`getAllBusinesses`/`getAllTransactions`, `AdminScreen.tsx:19-47`) — the admin's phone
  cache, updated only on load; no presence, no server aggregate, no streaming.

---

## Honest gap summary

| Q | What the owner expects | Current reality | Gap size |
|---|---|---|---|
| Q1 | Tick/add products & services; onboarding fits | Products+services+onboarding DONE | Small |
| Q2 | Hybrid retail+cyber etc. one entity | Single category only | Medium |
| Q3 | Receiving account tied to business + Daraja, circuit that won't break | Nothing built; placeholder number | **Large — market blocker** |
| Q4 | mpesa/pochi/till/airtel/paybill/bank | All labels exist; no account details | Small (detail capture = Q3) |
| Q5 | 100–1000 users without crashing | Offline-first + RLS, but unproven; sync is row-by-row; migrations unapplied | Medium (hardening) |
| Q6 | CEO dashboard: users + real-time metrics | Unreachable, client-local, static | **Large** |

## 80/20 plan (start with the two that unblock the owner's pitch)

1. **Receiving-account model + onboarding/settings stage (Q3-data + Q4-details).**
   Add per-payment-method account fields (Till #, Paybill account, Pochi #, Airtel #, M‑PESA
   #, bank name/account) on the Business. New onboarding step after method selection that
   asks "where will customers send money?"; show it on the business profile. ~1 focused,
   isolated change; unblocks trust immediately. **≈4h.**
2. **Daraja confirmation circuit (Q3-auto).** STK or C2B callback via a Supabase Edge
   Function; reconcile against the account details from #1 so the record is tied to the
   business's real receiving account; keep manual SMS paste as fallback so the circuit never
   breaks. Requires Safaricom developer registration. **≈18–24h** (server work; can be a
   follow-up sprint while #1 ships).
3. **Make Admin real (Q6).** Add an `is_admin` claim (RLS-checked), a navigation entry,
   and replace device-local aggregation with a Supabase SQL view/RPC (aggregates server-side
   + a `presence`/`last_seen` marker from realtime heartbeats). **≈8–12h.**
4. **Hybrid business (Q2).** Persist the multi-category selection as an array; show all
   selected categories' templates & expense categories; keep backward compat.
   **≈6–10h.**
5. **Scale hardening (Q5).** Batch Dexie bulkPut in pull/sync; lock Admin list rendering to
   pagination; apply live migrations; add a real sync-path load test (Vercel + Supabase
   budget permitting). **≈8–12h.**
6. **Q1 polish (cost price, barcode, service flag).** **≈4–6h.**

Recommended first cut = **#1 (receiving account + stage) → #3 (admin reachable)**, which
together turn the stock product into one an owner can demo to a business owner today.
Daraja (#2) is the real revenue-trust engine and should follow immediately in its own
sprint because it needs external registration lead time.

**Open questions for the owner (no iteration until answered):**
- Priority order: ship #1 first, or wait to pair #1+#2 in one release?
- For Daraja: STK-push (business initiates from Daftari) vs C2B callback (customer pays to
  the given number and Daftari reconciles the message)? Affects onboarding copy + flow.
- Confirm live migrations can be applied to `rjedivbpldkroffswoyb` so realtime + schema are
  production-true.