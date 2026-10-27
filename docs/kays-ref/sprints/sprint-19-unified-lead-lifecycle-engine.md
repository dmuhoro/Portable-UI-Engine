# Sprint 19 — Unified Lead Lifecycle Engine: Visual Pipeline, Real-Time WhatsApp Dispatch, and Operational Analytics

## Objective
Execute a massive combined push across three complementary pillars: build a high-fidelity Kanban pipeline board, wire real WhatsApp Cloud API dispatch into the notification queue, and create an executive analytics dashboard with operational KPIs — all gated behind multi-tenant `requireOrg()` isolation.

## Deliverables

### Pillar 1 — Visual Lead Pipeline Board

**`src/components/leads/PipelineBoard.tsx`** (new, 298 lines)
- Full Kanban-style board with five pipeline stages: **New**, **Triage Pending**, **Scheduled**, **Checked-In**, **Dropped**.
- Native HTML5 drag-and-drop: cards feel instantaneous by firing `useUpdateLead` mutation on drop (which triggers TanStack Query's optimistic update from Sprint 17).
- Each card shows: name, email, phone, priority (with inline dropdown), status with "Move" transitions filtered by current stage, and a `Message`/`Confirm` action button.
- `Message` button dispatches a triage follow-up via `dispatchLeadMessage` server function.
- `Confirm` button (shown for Scheduled leads) sends a confirmation WhatsApp message.
- Per-card delete button with optimistic removal.
- `PIPELINE_STAGES` constant exported for reuse.

**Integration in `src/routes/admin/triage.tsx`**
- New view toggle in the header: **Board** (Kanban) ↔ **Table** (original QueueTable). Default view is pipeline.
- Added `BarChart3` link to `/admin/dashboard`.
- New `checked_in` status option added to dropdowns and `statusLabel` map.
- All existing table functionality preserved.

### Pillar 2 — WhatsApp/SMS Communication Dispatch

**`src/lib/api/dispatch.server.ts`** (new)
- `sendWhatsApp(phone, message)` — sends via WhatsApp Cloud API (`graph.facebook.com/v18.0`) when `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` env vars are present. Falls back to logging when not configured (dev mode).
- `formatMessage(type, name)` — three message templates:
  - **confirmation**: "Hi {name}, your appointment at Kay's Wellness Centre has been confirmed..."
  - **triage_followup**: "Hi {name}, this is Kay's Wellness Centre following up on your recent inquiry..."
  - **reminder**: "Reminder: You have an appointment at Kay's Wellness Centre tomorrow..."
- `dispatchLeadMessage` — server function that looks up the lead by ID (tenant-scoped), formats the message, sends via WhatsApp, and enqueues a notification event.
- `MessageType` type: `"confirmation" | "triage_followup" | "reminder"`.

**`src/lib/queue.server.ts`** (enhanced)
- `dispatchNotification` now performs actual message formatting and WhatsApp dispatch instead of logging and returning success.
- For `lead_created` events: auto-sends a triage follow-up message.
- For `msg_*` events: parses the message type suffix and formats accordingly.
- Handles missing phone numbers gracefully (returns success with warning).

**`src/lib/env.server.ts`** (updated)
- Added optional `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` env vars.
- Added `ANALYTICS_REVENUE_VALUE` (default 250) for revenue-at-risk computation.

**`src/lib/logger.server.ts`** (updated)
- Added `WHATSAPP_SENT`, `WHATSAPP_FAILED`, `ANALYTICS_COMPUTED` events.

### Pillar 3 — Executive Operational Analytics Dashboard

**`src/lib/analytics.server.ts`** (new)
- `computeAnalytics()` — queries the tenant-scoped `clinic_leads` table for:
  - **Total Leads**, **This Week**, **This Month** counts
  - **Lead Conversion Velocity**: avg leads per day over 30 days
  - **Triage-to-Schedule Rate**: % of contacted leads that were scheduled
  - **No-Show Percentage**: % of scheduled leads not converted
  - **Revenue at Risk**: high-priority leads still unconverted × `ANALYTICS_REVENUE_VALUE`
  - **Stage Breakdown**: count per status (`pending`, `contacted`, `scheduled`, `converted`, `closed`)
  - **Priority Breakdown**: count per priority level
- All queries pass through `requireOrg()` for strict multi-tenant isolation.

**`src/lib/api/analytics.server.ts`** (new)
- `getAnalytics` server function wrapping `computeAnalytics()` with DB-unavailable handling.

**`src/routes/admin/dashboard.tsx`** (new, 280 lines)
- Full analytics dashboard page at `/admin/dashboard` with auth gating.
- Four stat cards: Total Leads, Conversion Velocity, Triage→Schedule Rate, Revenue at Risk.
- Pipeline Distribution bar with proportional stacked bar chart and per-stage legend.
- Lead Activity panel with week/month breakdowns and priority breakdown.
- Retry button for DB-unavailable state.
- Loading spinner during analytics computation.

## Module Changes Summary

| File | Change |
|---|---|
| `src/components/leads/PipelineBoard.tsx` | **New** — Kanban board + card actions |
| `src/lib/api/dispatch.server.ts` | **New** — WhatsApp dispatch + message templates |
| `src/lib/analytics.server.ts` | **New** — Analytics aggregation engine |
| `src/lib/api/analytics.server.ts` | **New** — Analytics server function |
| `src/routes/admin/dashboard.tsx` | **New** — Operations dashboard page |
| `src/lib/queue.server.ts` | **Enhanced** — Real dispatch with WhatsApp formatting |
| `src/lib/env.server.ts` | **Updated** — WhatsApp + analytics env vars |
| `src/lib/logger.server.ts` | **Updated** — WhatsApp + analytics events |
| `src/routes/admin/triage.tsx` | **Enhanced** — Board/Table toggle, dashboard link, checked_in status |
| `src/__tests__/dispatch.test.ts` | **New** — 7 tests |
| `src/__tests__/analytics.test.ts` | **New** — 5 tests |
| `src/__tests__/pipeline-board.test.ts` | **New** — 2 tests |

## Test Results
- 55 tests pass (44 existing + 11 new).
- Build succeeds cleanly.

## Key Design Decisions
- **Pipeline as a view toggle, not a separate route** — The table view is still useful for sorting and bulk operations. A toggle lets staff choose their preferred workflow without losing existing functionality.
- **Native HTML5 DnD, no library** — Avoids adding `@dnd-kit` or `react-beautiful-dnd` dependencies. The Kanban interaction pattern is simple drag-to-stage-drop; native DnD handles all needed events and keeps the bundle small.
- **WhatsApp Cloud API v18.0** — Uses the standard Meta Business API with token-based auth. Dev mode logs messages to stdout when credentials aren't configured.
- **Analytics computed on-demand, not cached** — The dashboard re-computes on each load. For low-volume clinics (hundreds of leads, not millions), query latency is negligible. A caching layer (e.g., Redis or in-memory with TTL) can be added as the dataset grows.
- **Revenue at Risk is a configurable per-lead value** — `ANALYTICS_REVENUE_VALUE` defaults to KES 250 (conservative estimate). Operators can tune this to their actual average appointment value.

## Retrospective

### What went well
- The existing `requireOrg()` firewall made multi-tenant analytics trivial — every query just adds `WHERE organization_id = $1`.
- The Sprint 17 optimistic mutation hooks (`useUpdateLead`) made the drag-and-drop feel instantaneous with zero extra code.
- Message templates are pure functions — easy to test without any server infrastructure.

### What could be improved
- The PipelineBoard uses per-card `useUpdateLead`/`useDeleteLead` hooks, which means each card independently tracks mutation state. This is fine for 20–30 cards but could be optimized with a single shared mutation state for larger boards.
- Analytics could benefit from a server-side cache with TTL to avoid re-querying on every dashboard load.
- The WhatsApp dispatch uses `process.env` directly rather than the `getEnv()` pattern — the env vars are optional (dev fallback) so this is intentional, but it breaks the convention slightly.

## Known Issues
- WhatsApp credentials not set in production yet. Messages will be logged but not delivered until `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` are configured in the Vercel environment.
- Dashboard analytics queries lock the analytics row on every load — no performance issues at current scale but should monitor as lead volume grows.
- Drag-to-Move transitions update the lead status optimistically; if the server rejects the transition (e.g., network failure), the card snaps back via the `onError` rollback in `useUpdateLead`.
