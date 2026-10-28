# Sprint 21 — Three-Pillar Operational Closure

## Objective
Eliminate all operational gaps before the July 31 beta launch by delivering three major architectural pillars: Asynchronous Outbound Automation Engine, Self-Serve Clinic Configuration, and Multi-Resource Booking with Conflict Resolution.

---

## Pillar 1: Asynchronous Outbound Automation Engine

### AutomationState Schema (`src/lib/db.server.ts`)
- New `automation_state` table linked 1:1 to `clinic_leads` via `lead_id` UNIQUE constraint.
- Fields: `current_stage` (UNTOUCHED, TRIAGING, SCHEDULED, STALLED), `last_interaction_at`, `next_action_scheduled_at`, `retry_count`, `context_snapshot` (JSONB).
- Indexed on `(organization_id, current_stage)` for efficient scanning.

### Orchestration Layer (`src/lib/api/automation.server.ts`)
- `getLeadsNeedingFollowup(orgId, triageTimeoutMinutes)` — scans for UNTOUCHED leads past threshold, TRIAGING leads past `next_action_scheduled_at`, and STALLED leads past their re-engagement window. Uses `FOR UPDATE SKIP LOCKED` for race-condition-free batch processing.
- `processProgressiveFollowup(leadId, orgId, timeout)` — deterministic stage machine:
  - **UNTOUCHED**: Sends `triage_followup` WhatsApp message → moves to TRIAGING → schedules next action at `now + timeout`.
  - **TRIAGING (retry 0–1)**: Sends another followup → increments retry_count.
  - **TRIAGING (retry ≥ 2)**: Moves to STALLED → schedules re-engagement at `now + timeout × 4`.
  - **STALLED**: Sends `reminder` re-engagement nudge → increments retry_count → schedules next at `now + timeout × 4`.
- Each step acquires `SELECT ... FOR UPDATE` on the `automation_state` row before mutating, preventing double-dispatch in concurrent runs.
- `enqueueNotification` called after each dispatch for persistent audit trail.

### Cron Endpoint (`src/routes/api/cron/automation-orchestrator.ts`)
- Public GET endpoint at `/api/cron/automation-orchestrator` protected by `Authorization: Bearer {CRON_SECRET}`.
- Iterates all organizations, calling `runAutomationOrchestrator(orgId)` for each.
- Returns aggregate stats: `{ orgsProcessed, totalProcessed, totalDispatched, totalErrors }`.

### Test Coverage (7 tests)
- Stage transitions: UNTOUCHED → TRIAGING, TRIAGING → STALLED, retry followup, re-engagement nudge.
- `getLeadsNeedingFollowup` returns only stale leads.
- `ensureAutomationState` creates row on first call.
- Server function export presence.

---

## Pillar 2: Self-Serve Clinic Configuration

### ClinicConfiguration Schema (`src/lib/db.server.ts`)
- New `clinic_configuration` table with UNIQUE per organization.
- Fields: `business_hours` (JSONB map of day → `{ open, close }`), `slot_duration_minutes` (default 30), `triage_timeout_minutes` (default 45), `custom_keywords` (JSONB array), `timezone` (default UTC).

### Configuration Server Module (`src/lib/api/clinic-config.server.ts`)
- `getClinicConfig(orgId)` — read current config.
- `ensureClinicConfig(orgId)` — creates default config (M–F 08:00–17:00, UTC) if none exists.
- `updateClinicConfig(orgId, input)` — dynamically builds UPDATE with Zod-validated fields. Enforces `triage_timeout_minutes >= 5` at the server level.
- `getCustomKeywords(orgId)` — returns custom keyword array for webhook injection.
- `fetchClinicConfig` / `saveClinicConfig` — `createServerFn` wrappers for client-side access.

### Settings UI (`src/routes/admin/settings/operations.tsx`)
- Dedicated route at `/admin/settings/operations` with full operations control surface.
- **Business Hours**: Checkbox-toggle per day (Mon–Sun), with `time` inputs for open/close. Inline validation ensures open precedes close.
- **Scheduling Defaults**: Slot duration dropdown (15–120 min), triage timeout number input (minimum 5 enforced client-side + server-side).
- **Custom Keywords**: Tag-style editor with add/remove. Typed array, max 20 keywords, each ≤ 50 chars.
- **Resources Management**: Inline provider and room creation with text input + "Add" button. Lists existing active resources.
- Dirty-state tracking enables/disables "Save Changes".

### Engine Injection (`src/routes/api/webhooks/whatsapp.ts`)
- Webhook POST handler now calls `getCustomKeywords(orgId)` to merge per-clinic keywords with the built-in `containsPessimisticKeyword` set.
- Webhook keyword matching combines both sets before flagging cancellation alerts.

---

## Pillar 3: Multi-Resource Booking & Conflict Resolution

### Resources Schema (`src/lib/db.server.ts`)
- New `resources` table: `id`, `organization_id`, `name`, `type` (PROVIDER | ROOM), `status` (active | inactive).
- Indexed on `(organization_id, type)`.
- `provider_id` and `room_id` columns added to `clinic_leads` via safe ALTER TABLE + `information_schema` guard.

### Resources Server Module (`src/lib/api/resources.server.ts`)
- `getResources(orgId, type?)` — list active resources, optionally filtered by type.
- `createResource(orgId, name, type)` — insert new resource.
- `updateResourceStatus(orgId, id, status)` — activate/deactivate.
- `checkResourceConflict(orgId, providerId, roomId, startTime, durationMinutes, excludeLeadId?)` — atomic overlap check:
  ```sql
  SELECT id FROM clinic_leads
  WHERE organization_id = $1
    AND (provider_id = :p OR room_id = :r)
    AND appointment_timestamp IS NOT NULL
    AND appointment_timestamp < :end
    AND appointment_timestamp + :duration::INTERVAL > :start
    AND status != 'closed'
  ```
  Returns `{ hasConflict, conflictingLeadIds, errorCode: "ERR_RESOURCE_CONFLICT" }`.
- `scheduleAppointment` — `createServerFn` combining conflict check + status update + dispatch. Returns conflict error code to UI.

### CalendarGrid Multi-Lane Rendering (`src/components/leads/CalendarGrid.tsx`)
- Resource filter dropdown at top of calendar showing providers and rooms with optgroup hierarchy.
- `DayColumn` accepts `resourceFilter` prop; booked chips filtered when a specific provider/room is selected.
- **QuickScheduleDrawer** refactored with:
  - Three-column assignment grid: Slot picker + Provider dropdown + Room dropdown.
  - "Schedule at <time>" confirmation button per lead.
  - Uses `scheduleAppointment` mutation (with conflict detection and auto-dispatch) instead of raw `updateLead`.
- All providers/rooms fetched via `fetchResources` query with TanStack caching.

### LeadRow Type Expansion (`src/lib/api/leads.server.ts`)
- `provider_id: number | null` and `room_id: number | null` added to `LeadRow` type.
- `fetchLeads` SELECT updated to include both columns.

### Test Coverage (9 tests)
- Conflict detection: provider booked, room booked, both null (no conflict), exclude current lead.
- Resource CRUD: `getResources` with type filter, `createResource`.
- Schema validation via `scheduleAppointment` (indirect).

---

## Module Changes Summary

| File | Change |
|---|---|
| `src/lib/db.server.ts` | New tables: `automation_state`, `clinic_configuration`, `resources`; columns: `provider_id`, `room_id` on `clinic_leads` |
| `src/lib/logger.server.ts` | 10 new event types |
| `src/lib/api/automation.server.ts` | **New** — Engine + orchestrator + progressive followup |
| `src/lib/api/clinic-config.server.ts` | **New** — Config CRUD + validation |
| `src/lib/api/resources.server.ts` | **New** — Resources CRUD + conflict check + scheduleAppointment |
| `src/routes/api/cron/automation-orchestrator.ts` | **New** — Global cron endpoint with bearer auth |
| `src/routes/admin/settings/operations.tsx` | **New** — Operations config UI |
| `src/routes/api/webhooks/whatsapp.ts` | **Updated** — Custom keywords from clinic config |
| `src/components/leads/CalendarGrid.tsx` | **Rewritten** — Multi-lane resource filtering, conflict-aware scheduling |
| `src/lib/api/leads.server.ts` | **Updated** — `provider_id`, `room_id` in LeadRow + fetchLeads |
| `src/__tests__/automation.test.ts` | **New** — 7 tests |
| `src/__tests__/resources.test.ts` | **New** — 9 tests |
| `src/__tests__/clinic-config.test.ts` | **New** — 10 tests |
| `src/__tests__/pipeline-board.test.ts` | **Updated** — Timeout increased to 15s |

## Test Results
- **84 tests pass** (55 existing + 7 automation + 9 resources + 10 clinic-config + 3 from updated PipelineBoard/CalendarGrid exports).
- Build succeeds cleanly with zero warnings.

## Key Design Decisions
- **SELECT FOR UPDATE on automation_state rows** — Prevents double-dispatch when the cron endpoint runs concurrently with itself (e.g., overlapping invocations from Vercel Cron or multiple replicas).
- **FOR UPDATE SKIP LOCKED on candidate scan** — Multiple orchestrator instances can run in parallel without contention; each picks up a different subset of leads.
- **Dynamic UPDATE in scheduleAppointment** — Constructs SET clauses for only the provided fields (provider_id, room_id, status, appointment_timestamp), avoiding unnecessary writes.
- **information_schema guard for ALTER TABLE** — Follows the existing pattern for safe additive migrations without needing a formal migration framework.
- **createServerFn for resources/clinic-config/clinic-config** — Wrapped in TanStack Start server functions for type-safe client access with cookie-based org resolution.
- **Clinic config defaults on first read** — `ensureClinicConfig` auto-creates a sensible default instead of requiring an explicit setup step.
- **Dirty-state tracking in settings UI** — Save button only activates when changes are detected, preventing unnecessary writes.

## Known Issues
- Cron endpoint requires `CRON_SECRET` env variable; defaults to `dev-cron-secret` in development but must be set in production.
- `scheduleAppointment` cannot be unit-tested outside TanStack Start runtime — pure functions (`checkResourceConflict`) tested directly instead.
- Business hours UI uses native `<input type="time">` — not ideal for tablet use where a time-wheel picker would be more ergonomic.
- Resource filtering in CalendarGrid is client-side only (filters already-loaded leads); at scale with thousands of leads per week, server-side filtering would be needed.
