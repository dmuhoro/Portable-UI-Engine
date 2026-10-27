# Sprint 25 — Real-Time SSE Sync, Inbound Media Storage, Granular RBAC, and Pre-Flight Hydration Fixtures

**Theme:** Enterprise finalization sweep: live Web-Socket/SSE push events, WhatsApp media attachment ingestion, role-based access controls with UI guards, and production seed fixtures.

## Pillars

### 1. Real-Time SSE Stream (`/api/streams/live-updates`)
- `src/lib/event-bus.server.ts` — DB-backed `live_events` table with `publishEvent`, `pollLiveEvents`, `cleanLiveEvents`, and `ensureLiveEventsSchema`. No in-memory state (survives serverless cold starts).
- `src/routes/api/streams/live-updates.ts` — SSE endpoint using h3 `eventHandler` + `ReadableStream`. Requires `getCurrentOrgId()` session. Polls every 3 s for new events, sends heartbeats every 30 s, cleans stale events every 5 min.
- **Integration points:**
  - `leads.server.ts` — publishes `lead:updated` on status change.
  - `interactions.server.ts` — publishes `interaction:created` on every `recordInteraction`.
  - `billing.server.ts` — publishes `invoice:created` and `payment:recorded`.
  - `routes/api/webhooks/whatsapp.ts` — publishes `interaction:created` on inbound messages/media.
- **Tenant isolation:** All queries scoped by `tenant_id`. SSE endpoint rejects if no org in session.

### 2. Media & Intake Attachment Storage
- `src/lib/storage.server.ts` — abstract file storage layer with org-isolated paths (`org-{orgId}/{type}/{uuid}-{filename}`). Supports `storeFile`, `readFile`, `deleteFile`, `fileExists`.
- Local filesystem backend under `STORAGE_ROOT` (default `./.storage`).
- Validated types: `image`, `document`, `audio`, `diagnostic`.
- **WhatsApp webhook expansion** (`src/routes/api/webhooks/whatsapp.ts`):
  - Detects `image`, `document`, `audio`, `video`, `sticker` message types via `extractMedia()`.
  - Downloads media from WhatsApp Cloud API using `WHATSAPP_ACCESS_TOKEN`.
  - Stores via `storeFile()` and records `media_shared` interaction.
  - Checks media captions for cancellation keywords.
  - Gracefully degrades if access token is not configured.

### 3. Granular Role-Based Access Controls (RBAC)
- `src/lib/permissions.server.ts` — role constants (`SUPER_ADMIN`, `CLINIC_OWNER`, `CLINIC_STAFF`), `roleAtLeast()`, `requireRole()`, and capability helpers (`canAccessFinance`, `canAccessDataExport`, `canDeleteData`, `canAccessAdminSettings`).
- **Server-side guards:**
  - `billing.server.ts`: `generateInvoiceForCheckedIn`, `fetchInvoices`, `addPayment` — require `SUPER_ADMIN` or `CLINIC_OWNER`; return `{status: "forbidden"}` on failure.
  - `leads.server.ts`: `deleteLead` — requires `SUPER_ADMIN` or `CLINIC_OWNER`.
  - `exports.server.ts`: `generateExport` — checks `canAccessDataExport()`.
- **UI guards:**
  - `/admin/finance` — renders restricted-access page for `CLINIC_STAFF`.
  - `/admin/settings/data` — redirects `CLINIC_STAFF` to a lock page.
  - `/admin/dashboard` — hides Financial KPIs and Revenue Per Resource sections for `CLINIC_STAFF`.

### 4. Production Pre-Flight Hydration & Seed Fixtures
- `src/lib/seed.server.ts` — validated seed data:
  - 12 medical services (BHRT, IV Therapy, Ozone, Chelation, Functional Medicine, etc.) with codes, prices, and durations.
  - 6 triage scripts (initial contact, follow-up, appointment reminder, post-visit, no-show recovery, cancellation retention).
  - 5 message templates (welcome, lab order, payment reminder, treatment plan, referral).
- `src/scripts/db-hydrate.ts` — standalone CLI script that runs schema setup, validates seed data, and hydrates all registered organizations with resources, availability, and clinic configuration.
- `"db:hydrate": "tsx src/scripts/db-hydrate.ts"` added to `package.json`.
- `hydrateOrganization()` is also callable from server code for post-registration hydration.

## File Changes

| File | Change |
|------|--------|
| `src/lib/event-bus.server.ts` | **New** — DB-backed event bus (live_events table, publish/poll/clean) |
| `src/routes/api/streams/live-updates.ts` | **New** — SSE endpoint with org-scoped polling |
| `src/lib/storage.server.ts` | **New** — Abstract file storage with org-isolated paths |
| `src/lib/permissions.server.ts` | **New** — RBAC constants, requireRole(), capability helpers |
| `src/lib/seed.server.ts` | **New** — Medical services, triage scripts, message templates + hydrateOrganization |
| `src/scripts/db-hydrate.ts` | **New** — CLI hydration command |
| `src/routes/api/webhooks/whatsapp.ts` | **Updated** — Media message detection, WhatsApp media download, storeFile, SSE publish |
| `src/lib/api/leads.server.ts` | **Updated** — SSE publish on lead update; RBAC on deleteLead |
| `src/lib/api/billing.server.ts` | **Updated** — SSE publish on invoice/payment; RBAC on all endpoints |
| `src/lib/api/interactions.server.ts` | **Updated** — SSE publish on recordInteraction |
| `src/lib/exports.server.ts` | **Updated** — RBAC check in generateExport |
| `src/lib/db.server.ts` | **Updated** — live_events table added to ensureSchema |
| `src/lib/logger.server.ts` | **Updated** — 7 new EVENTS |
| `src/lib/session.server.ts` | **No changes needed** — role already in SessionPayload |
| `src/routes/admin/finance.tsx` | **Updated** — RBAC UI guard with lock page |
| `src/routes/admin/settings/data.tsx` | **Updated** — RBAC UI guard, auth redirect |
| `src/routes/admin/dashboard.tsx` | **Updated** — Financial KPIs hidden for STAFF |
| `src/__tests__/permissions.test.ts` | **New** — 19 tests for role constants, helpers, canAccess* |
| `src/__tests__/storage.test.ts` | **New** — 8 tests for validateFileType, generateStoragePath |
| `src/__tests__/seed.test.ts` | **New** — 15 tests for seed data validation |
| `src/__tests__/event-bus.test.ts` | **New** — 5 tests for publish/poll/ensure/clean |
| `src/__tests__/webhook-media.test.ts` | **New** — 5 tests for media types and webhook exports |
| `package.json` | **Updated** — db:hydrate script, tsx devDependency |

## Results
- **206 tests** passing (up from 148)
- **26 test files** passing
- Build: zero errors (only pre-existing `use client` warnings from deps)
