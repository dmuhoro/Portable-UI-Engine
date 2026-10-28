# Sprint 29 — Outbound Webhook Dispatcher, Bi-Directional Messaging Ledger, Financial Export Mappers, Calendar Sync Streams, Developer Audit Panel

**Theme:** External communications and interoperability: outbound webhook dispatcher with
HMAC-SHA256 payload signing, bi-directional WhatsApp/SMS message ledger, QuickBooks/Xero
financial export mappers with multi-currency support, secure iCal calendar sync feeds,
and a developer webhook audit logs dashboard.

## Pillars

### 1. Multi-Tenant Outbound Webhook Dispatcher
- `src/lib/webhooks.server.ts` — Full webhook lifecycle:
  - `generateWebhookSecret()` — Cryptographically secure 64-char hex secret.
  - `signPayload(payload, secret)` — HMAC-SHA256 signature generation.
  - `verifyWebhookSignature(payload, signature, secret)` — Timing-safe signature verification with `sha256=` prefix support.
  - `registerWebhook(orgId, url, events)` — Stores endpoint config with auto-generated secret.
  - `removeWebhook(orgId, webhookId)` — Soft-delete by org + id.
  - `getWebhooks(orgId)` — List all registered endpoints.
  - `dispatchWebhook(orgId, eventType, payload)` — Async dispatch to all matching endpoints:
    - Filters by subscribed events or wildcard `*`.
    - `X-Clinic-Signature: sha256=<hmac>` header on every delivery.
    - `X-Clinic-Event` and `X-Clinic-Delivery` headers for idempotency.
    - 10s timeout via `AbortSignal.timeout()`.
    - 5xx responses trigger retry queue; 4xx failures are final.
  - `recordDelivery()` / `updateDeliveryStatus()` — Delivery lifecycle tracking.
  - `getWebhookDeliveries(orgId, options)` — Paginated delivery history with status/event filters.
  - `getDeliveryStats(orgId)` — Aggregated success/failed/pending counts.
  - `retryPendingDeliveries(orgId)` — Exponential backoff retry processor (up to max_retries).

### 2. Bi-Directional Messaging & WhatsApp/SMS Ledger Engine
- `src/lib/messaging.server.ts` — Message ledger for audit and patient timeline:
  - `logMessage(input)` — Inserts into `message_ledger` with channel, direction, addresses, body, metadata.
  - `getMessagesForLead(orgId, leadId, options)` — Paginated lead message history.
  - `getMessagesByChannel(orgId, channel, options)` — Channel-specific queries with direction filter.
  - `getMessageStats(orgId)` — Aggregated inbound/outbound/whatsapp/sms counts.
  - `updateMessageStatus(messageId, status, externalId?)` — Status tracking for outbound delivery confirmations.
  - `maskAddress(address)` — PII masking for logging (shows first 3 + last 2 chars).
  - `formatMessagePreview(body, maxLen)` — Truncation with ellipsis for UI previews.
- **DB Schema** — `message_ledger` table with columns: organization_id, lead_id, channel (whatsapp/sms),
  direction (inbound/outbound), from_address, to_address, body, status, external_id, metadata (JSONB).

### 3. Universal Accounting Financial Export Engine
- `src/lib/financial-exports.server.ts` — Multi-format financial record export:
  - `getFinancialRecords(orgId, startDate?, endDate?)` — Joins invoices + payments + leads.
  - `convertCurrency(amount, from, to)` — KES/USD/EUR/GBP conversion with defined rates.
  - `mapToQuickBooks(records, currency)` — Maps to QuickBooks Invoice JSON format:
    - TxnDate, DocNumber, CustomerRef, Line items, CurrencyRef, TotalAmt, Balance, TxnTaxDetail.
  - `mapToXero(records, currency)` — Maps to Xero Invoice JSON format:
    - InvoiceNumber, Contact (Name/Email), LineItems with TaxType/AccountCode, CurrencyCode, Total, AmountDue.
  - `exportQuickBooksCsv(records, currency)` — QuickBooks-compatible CSV with flattened dot-notation headers.
  - `exportXeroCsv(records, currency)` — Xero-compatible CSV with LineItems dot-notation headers.
  - `exportFinancialJson(records, format, currency)` — JSON output for either format.
  - Tax mapping: `tax_amount > 0` → `TxnTaxDetail.TotalTax` (QB) / `TaxType: "OUTPUT"` (Xero).
  - Status mapping: paid→PAID, void→VOIDED, issued→AUTHORISED (Xero); paid→Balance=0 (QB).

### 4. Real-Time Clinic Calendar Sync Streaming
- `src/routes/api/calendar-sync.ts` — Secure iCal feed endpoint:
  - `GET /api/calendar-sync?token=<hex>` — Returns `.ics` file with `Content-Disposition: attachment`.
  - Token lookup via `webhook_configs.secret` (reuse existing secret infrastructure).
  - `buildICalContent(events, orgName)` — RFC 5545 compliant VCALENDAR generation:
    - VEVENT with UID (SHA-256 hash), DTSTART/DTEND, SUMMARY, DESCRIPTION, LOCATION, ATTENDEE.
    - Escaped special characters (`\n`, `;`, `,`, `\\`).
    - Carriage return line endings (`\r\n`) per iCal spec.
  - `getUpcomingAppointments(orgId, providerId?)` — Future appointments with provider/room joins.
  - `escapeIcalText(text)` — iCal-safe text escaping.
  - `formatIcalDate(dateStr)` — ISO-to-iCal date formatting (`YYYYMMDDTHHMMSSZ`).
  - `generateUid(event)` — Deterministic UID from lead+timestamp+org hash.
  - 200 event limit, ordered by appointment_timestamp ASC.

### 5. Developer Webhook Audit Logs View
- `src/routes/admin/settings/developer.tsx` — `/admin/settings/developer` dashboard:
  - Three-tab interface: **Webhook Endpoints** | **Delivery Log** | **Statistics**.
  - **Webhook Endpoints tab**: Lists registered URLs with active status, subscribed events, creation date.
  - **Delivery Log tab**: Paginated delivery history with:
    - Status filter buttons (All, success, failed, retrying, pending).
    - Expandable rows showing payload JSON and error messages.
    - Response code badges (green <300, red ≥300), response time display.
    - "Retry Pending" button for manual retry trigger.
    - Prev/Next pagination (20 per page).
  - **Statistics tab**: Four metric cards (Total, Successful, Failed, Pending/Retrying).
  - Follows existing admin settings patterns (TanStack Router, glass morphism cards).

### 6. DB Schema Additions
- `src/lib/db.server.ts` — Three new tables in `ensureSchema()`:
  - `webhook_configs` — organization_id, url, secret, events (JSONB), active, timestamps. Indexed on (org, active).
  - `webhook_deliveries` — organization_id, webhook_config_id (FK), event_type, payload (JSONB), status, response_code, response_time_ms, error_message, retry_count, max_retries, next_retry_at. Indexed on (org, created_at DESC) and (status, next_retry_at).
  - `message_ledger` — organization_id, lead_id (FK), channel, direction, from_address, to_address, body, status, external_id, metadata (JSONB). Indexed on (lead_id, created_at DESC) and (org, created_at DESC).

## File Changes

| File | Change |
|------|--------|
| `src/lib/webhooks.server.ts` | **New** — Outbound webhook dispatcher with HMAC signing, dispatch, retry, delivery tracking |
| `src/lib/messaging.server.ts` | **New** — Bi-directional message ledger with channel/direction queries, PII masking |
| `src/lib/financial-exports.server.ts` | **New** — QuickBooks/Xero CSV+JSON mappers with multi-currency and tax mapping |
| `src/routes/api/calendar-sync.ts` | **New** — iCal feed endpoint with token auth and RFC 5545 generation |
| `src/routes/admin/settings/developer.tsx` | **New** — Developer webhook audit panel with deliveries, stats, retry |
| `src/lib/db.server.ts` | **Updated** — Added webhook_configs, webhook_deliveries, message_ledger tables |
| `src/routeTree.gen.ts` | **Updated** — Auto-generated route tree includes calendar-sync and developer routes |
| `src/__tests__/webhooks.test.ts` | **New** — 16 tests for signing, verification, registration, delivery lifecycle, stats |
| `src/__tests__/messaging.test.ts` | **New** — 12 tests for message logging, queries, stats, address masking, preview |
| `src/__tests__/financial-exports.test.ts` | **New** — 16 tests for currency conversion, QB/Xero mapping, CSV/JSON export |
| `src/__tests__/calendar-sync.test.ts` | **New** — 4 tests for module structure, GET handler export |

## Results
- **352 tests** passing (up from 302, +50 new tests)
- **40 test files** passing (up from 36)
- Build: zero errors (only pre-existing `use client` warnings from deps)
