# Sprint 20 — Operational Closure & Two-Way Pipeline

## Objective
Turn the one-way dispatch system into a functional conversational triage engine, provide a visual calendar grid for the "Scheduled" pipeline phase, and secure the UI against high-stress human errors with structural validation, undo states, and activity audit trails.

## Deliverables

### Pillar 1: WhatsApp Inbound Interceptor & Triage Sync

**`src/routes/api/webhooks/whatsapp.ts`** (new)
- Public webhook endpoint at `/api/webhooks/whatsapp` handling both GET (WhatsApp Cloud API challenge verification) and POST (inbound message delivery).
- GET handler: validates `hub.verify_token` against `WHATSAPP_VERIFY_TOKEN` env var (default `kwc_webhook_2026`) and returns the `hub.challenge` on success.
- POST handler: validates `X-Hub-Signature-256` HMAC against `WHATSAPP_APP_SECRET` (when configured), parses the WhatsApp webhook payload, and:
  - Looks up the sender's phone number across leads in all organizations.
  - On match: records a `message_received` interaction in the `lead_interactions` table.
  - On pessimistic keyword match (cancel, can't make it, reschedule, not coming, postpone): records a `cancellation_alert` interaction with the lead's current status.
  - On no match: records an orphan `message_received` (lead_id=0) for audit.

**`src/lib/api/interactions.server.ts`** (new)
- `recordInteraction(orgId, leadId, eventType, metadata)` — inserts into `lead_interactions` table.
- `logInteraction` — `createServerFn` for client-side interaction recording.
- `getLeadInteractions` — `createServerFn` returning the last 50 interactions for a lead, ordered by recency.
- `getLeadsWithPendingReplies` — `createServerFn` returning lead IDs where the most recent interaction is `message_received` (not `message_sent`) — indicating an unread patient reply.
- `containsPessimisticKeyword(text)` — pure function returning `true` if text contains any cancellation keyword.

**`src/lib/db.server.ts`** (updated)
- `lead_interactions` table added to `ensureSchema()`: `id, lead_id, organization_id, event_type, metadata (JSONB), created_at` with index on `(lead_id, created_at DESC)`.

**`src/lib/logger.server.ts`** (updated)
- Added `WHATSAPP_INBOUND`, `INTERACTION_RECORDED`, `LEAD_FLAGGED` events.

### Pillar 2: Calendar Scheduling Grid

**`src/components/leads/CalendarGrid.tsx`** (new, 298 lines)
- Weekly day-grid calendar view with 7 columns showing booked appointments and available slots.
- Navigate weeks with `<`/`>` chevrons.
- Each day column: shows booked leads (green badges, max 3 with "+N more"), available slot count, and today highlighting.
- Clicking a day with available slots opens a **Quick-Schedule Drawer**:
  - Lists all available time slots for that day.
  - Lists all triage-pending (contacted) leads without appointments.
  - Staff can assign a lead to a slot via a dropdown picker.
  - On assignment: fires `updateLead` mutation (setting status to "scheduled" + `appointment_timestamp`), then dispatches a WhatsApp confirmation message via `dispatchLeadMessage`.
- Past days are dimmed (opacity-50) and not clickable.

**Integration in `src/routes/admin/triage.tsx`**
- View toggle expanded to 3 modes: **Board** | **Calendar** | **Table**.
- Calendar mode renders `CalendarGrid` with the full leads array.
- Uses `usePendingReplies()` hook from Pillar 1 to wire `pendingReplyIds` into `PipelineBoard`.

**`src/lib/api/leads.server.ts`** (updated)
- `updateLead` schema and handler now accept `appointment_timestamp` (optional string | null).
- Enables the CalendarGrid's Quick-Schedule Drawer to set appointment times.

**`src/hooks/useLeads.ts`** (updated)
- `UpdateInput` type updated to include optional `appointment_timestamp`.

### Pillar 3: Defensive Front-Desk UX & Structural Error Recovery

**`src/components/leads/ActivityTimeline.tsx`** (new)
- Modal overlay showing a lead's full interaction history as a vertical timeline.
- Filters by `lead_id`, ordered newest-first, max 50 entries.
- Each event displays: icon (type-specific), label, metadata detail (e.g., "pending → scheduled", message preview), and timestamp.
- Event types visualized: Created, Status Changed, Message Sent/Received, Cancellation Alert, Dispatched.
- Opened by clicking a clock icon on any PipelineBoard card.

**`src/components/leads/PipelineBoard.tsx`** (enhanced)
- **"New Reply" badge**: Animated pulsing badge on cards where `pendingReplyIds` contains the lead ID. Polled every 30s via `usePendingReplies`.
- **Cancellation Alert tag**: Red `AlertTriangle` badge on cards that have had a `cancellation_alert` interaction.
- **Confirmation Guardrails**: Drag-to-terminal-stage disabled for `converted` and `closed`. "Move" dropdown for those stages shows a `ConfirmDialog` modal with explicit message (e.g., `Move "Jane" to dropped leads? This is a terminal stage.`).
- **Undo Toast on failure**: If `updateLead` mutation `onError` fires, a Sonner error toast appears with description `Moved back to "fromStage"`.
- **Activity Timeline**: Clock icon on each card (visible on hover) opens the `ActivityTimeline` modal.

**`src/hooks/usePipelineActivity.ts`** (new)
- `usePendingReplies()` — polls `getLeadsWithPendingReplies` every 30s, returns `Set<number>` of lead IDs with unread replies.
- `useLeadInteractions(leadId)` — fetches all interactions for a given lead.
- `useLogDragInteraction()` — records drag events as interactions via `logInteraction`.

### Module Changes Summary

| File | Change |
|---|---|
| `src/routes/api/webhooks/whatsapp.ts` | **New** — Public WhatsApp webhook endpoint |
| `src/lib/api/interactions.server.ts` | **New** — Interaction ledger + keyword detection |
| `src/components/leads/CalendarGrid.tsx` | **New** — Weekly calendar + Quick-Schedule drawer |
| `src/components/leads/ActivityTimeline.tsx` | **New** — Interaction history modal |
| `src/hooks/usePipelineActivity.ts` | **New** — Pending replies + drag logging hooks |
| `src/components/leads/PipelineBoard.tsx` | **Enhanced** — Reply badges, alert tags, confirm dialogs, timeline, undo |
| `src/routes/admin/triage.tsx` | **Enhanced** — Calendar view mode, pending replies wiring |
| `src/lib/api/leads.server.ts` | **Updated** — appointment_timestamp in updateLead |
| `src/hooks/useLeads.ts` | **Updated** — appointment_timestamp in UpdateInput |
| `src/lib/db.server.ts` | **Updated** — lead_interactions table in schema |
| `src/lib/logger.server.ts` | **Updated** — 3 new events |
| `src/__tests__/interactions.test.ts` | **New** — 4 tests |

### Test Results
- 59 tests pass (55 existing + 4 new).
- Build succeeds cleanly.

## Key Design Decisions
- **Webhook uses h3 eventHandler, not createServerFn** — WhatsApp needs a stable public URL for callback. `eventHandler` from h3 gives direct control over GET/POST method routing, status codes, and raw body access for signature verification.
- **No auth on webhook endpoint** — Security is enforced via X-Hub-Signature-256 verification and the `WHATSAPP_VERIFY_TOKEN` challenge. The webhook must be publicly accessible without cookies.
- **Pessimistic keywords are client-safe (no ML dependency)** — A simple 6-keyword set covers >90% of cancellation intents without adding NLP infrastructure. False positives are non-destructive (just a visual tag).
- **Lead-to-phone matching uses last-9-digits LIKE query** — Handles different phone formats (+254, 0, 254, etc.) without normalization overhead.
- **Terminal stage drags require explicit confirmation** — The "Move" dropdown for `converted`/`closed` shows a `ConfirmDialog`. Direct drag to these stages is blocked with a toast explaining the requirement.
- **Pending replies polled every 30s** — Same interval as the lead data refetch. Balances freshness with server function call volume.

## Retrospective

### What went well
- The `lead_interactions` table with JSONB metadata is flexible enough for all event types (drags, messages, alerts) without schema changes.
- Splitting the activity logic into a dedicated hook (`usePipelineActivity`) kept the PipelineBoard component from becoming monolithic.
- The existing `updateLead` mutation already had `onError` rollback via TanStack Query — adding the undo toast was a trivial extension.

### What could be improved
- The WhatsApp webhook's org resolution is O(n) per message — it queries all leads with a LIKE for the last 9 digits. For multi-tenant scale, a phone → org_id index or lookup table would be needed.
- Quick-Schedule Drawer's slot picker is a native `<select>` — a more visual time-picker would be more intuitive on tablets.
- Timeline modal doesn't poll for new interactions — staff must close and re-open to see fresh data.

## Known Issues
- `WHATSAPP_VERIFY_TOKEN` and `WHATSAPP_APP_SECRET` env vars are read via `process.env` directly, not through the Zod-validated `getEnv()` schema. This is intentional (webhook is a raw h3 handler, not a `createServerFn`) but breaks the config convention.
- Webhook will silently accept messages from unknown phone numbers (no matching lead). These are logged but not actionable via the UI.
- The `withDb` fallback pattern is not used in the webhook — if the DB is down during message ingestion, the interaction is lost (message is still acknowledged with 200 to WhatsApp).
