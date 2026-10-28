# Sprint 39 — Live Client Events (SSE Real-Time Subscriptions)

**Theme:** Close release-readiness row #56 — SSE delivering to the browser was "UNVERIFIED". The
server push was in place, but no client actually subscribed: the triage desk and billing ledger
polled every 30s instead. This sprint ships the real-time wiring end-to-end (server protocol +
client hook + UI subscriptions) and proves it with real-path tests.

**Result: 730 tests / 69 files green. `tsc --noEmit` exit 0. ESLint 0 errors on touched files.**

## Summary

| Before | After |
|--------|-------|
| Server pushed frames with an `event:` prefix + JSON payload; client had no consumer | Every frame is a uniform `id:` + `data:` pair; `eventType` lives in the payload; one `onmessage` handles all events |
| Triage + billing ledger polled the DB every 30s (`refetchInterval`) | Both subscribe via `useLiveEvents` → TanStack Query invalidation on the exact server event |
| SSE resume on reload only worked by trusting browser defaults | `Last-Event-ID` auto-resume + `?lastEventId=` query param backed by `sessionStorage` |
| No test exercised the browser-facing protocol | Real-path tests: protocol consumer, hook behavior, and full-suite green |

## Part 1 — SSE protocol: uniform frames (the fix underneath)

`server/routes/api/streams/live-updates.ts` previously enqueued lines like
`event: lead:updated\n` before the `data:` line. The new client relies on the DOM
`MessageEvent` — which ignores `event:`-typed frames unless an `addEventListener(type)` handler
exists for that exact type. Switching to a **single `onmessage` handler** required removing the
`event:` prefix; the event type now travels inside the JSON payload exactly as the rest of the
world emits it (matching `publishEvent(eventType, ...)` call sites):

- `send(data, id?)` enqueues one chunk: `id: <eventId>\n` + `data: <json>\n`. `eventType` moved
  into the payload. The `connected` frame is a plain data frame with `eventType: "connected"`
  (no id — resume sends it back as a server event).
- Poll loop passes `evt.id` → `id: 41`.
- Resume on reconnect: browser sends `Last-Event-ID` on the auto-reconnect; on a fresh page load
  `sessionStorage.kwc_sse_last_event_id` becomes the `?lastEventId=` query param.

No change to `publishEvent` or `event-bus.server.ts` — only the wire format that browsers
actually parse.

## Part 2 — `useLiveEvents` hook (client)

New `src/hooks/useLiveEvents.ts` (`SSE_ENDPOINT = "/api/streams/live-updates"`):

- `useLiveEvents(eventTypesToKeys: Record<string, readonly SSEQueryKey[]> = {}, onEvent?)`
- `SSEQueryKey = readonly unknown[]` — matches TanStack Query key tuples (`["leads"]`,
  `[["invoices"], ["payments"]]`).
- On `onmessage`: parse JSON, ignore frames without `eventType`, persist `id` to sessionStorage,
  map `eventType` → query keys → `queryClient.invalidateQueries({ queryKey, exact: false })`,
  then fire `onEvent(payload)`.
- Reconnect: `onerror` closes the source and retries with capped exponential backoff
  (max 5, `2000 * attempt` ms). Effect deps are `[queryClient]`; `keyMapRef`/`onEventRef` keep
  subscription intent stable so re-mounts don't churn connections.
- Browser-only guard (`typeof EventSource === "undefined"` → no-op SSR-safe).

## Part 3 — Wiring into the two screens that used to poll

### Triage desk (`src/routes/admin/triage.tsx`)

- `LEAD_LIVE_EVENTS`: `lead:acquired`, `lead:stage_changed`, `lead:updated` → `[LEADS_QUERY_KEY]`.
- `useLiveEvents(LEAD_LIVE_EVENTS, event => { if (event.eventType === "interaction:created") void refreshPendingReplies(); })`
  — pending replies refresh immediately when a new interaction lands (previously waited for the
  next 30s tick).
- `useLeads.ts`: `refetchInterval: 30_000` **removed**; `staleTime: 10_000` kept so manual refetches
  stay cheap.

### Billing ledger (`src/components/finance/BillingLedger.tsx`)

- `BILLING_LIVE_EVENTS`:
  - `invoice:created` → `[["invoices"]]`
  - `payment:recorded`, `stk_push:paid`, `reconciliation:matched` → `[["invoices"], ["payments"]]`
- `useLiveEvents(BILLING_LIVE_EVENTS)` mounted inside `BillingLedger()`; `refetchInterval` on the
  `["invoices"]` query **removed**.

### Left deliberately in place

- `usePendingReplies` (`src/hooks/usePipelineActivity.ts`) keeps its own 30s `setInterval` as a
  resilience fallback behind the SSE push (its interval refreshes the desk, not a TanStack query).
- diagnostics 15s polls are out of scope for this sprint.

## Part 4 — Tests (real path, per Constitution Article V)

| File | Env | Count | What it proves |
|------|-----|-------|----------------|
| `live-updates-endpoint.test.ts` | node | 4 | Calls the **actual** h3 `GET` handler with a real `H3Event`-shaped request: 401 when no session org; SSE response headers + `connected` frame **with zero `event:`-prefixed lines**; polled row delivered as `id: 41` + `data: {"eventType":"lead:updated"...}` after the 3s poll fires, resuming from the `Last-Event-ID` header (asserts `poll("org-1", 41)`); query-param fallback `?lastEventId=9` → `poll("org-1", 9)`. |
| `use-live-events.test.tsx` | happy-dom | 4 | Drives the **real hook** in a **real `QueryClient`** via a fake `EventSource`: subscribes and invalidates only mapped keys (unmapped `webhook:delivered` is ignored); `connected` frame doesn't refetch; persists `lastEventId` on every frame and resumes via `?lastEventId=` from sessionStorage; reconnects with backoff (`2000ms` first retry) after a network error. |

No assertion weakened (AGENTS.md rule 4); the STK UI test now renders `BillingLedger` with the SSE
hook mounted and stays green.

## Files Changed

- `server/routes/api/streams/live-updates.ts`: uniform `send(data, id?)`, `eventType` in payload,
  `Last-Event-ID` header → then `?lastEventId=` fallback (commit `8f60cab`).
- `src/hooks/useLiveEvents.ts`: new `onmessage`-based hook (commit `5a9237b`).
- `src/hooks/useLeads.ts`: drop 30s lead polling (commit `44eb06e`).
- `src/routes/admin/triage.tsx`: `LEAD_LIVE_EVENTS` + `useLiveEvents` + instant pending-reply
  refresh on `interaction:created` (commit `44eb06e`).
- `src/components/finance/BillingLedger.tsx`: `BILLING_LIVE_EVENTS` + `useLiveEvents`; drop 30s
  invoice polling (commit `c8e1dea`).
- `src/__tests__/live-updates-endpoint.test.ts`, `src/__tests__/use-live-events.test.tsx`: new
  tests (commit `7503205`).
- Docs: `docs/release-readiness.md` (row #56 → PASS), `docs/sprint-cross-reference.md`,
  `docs/evidence/2026-08-28_sse_live_client_events.md`, `CHANGELOG.md`.

## Commits

1. `8f60cab` `fix(sse)`: emit uniform id+data frames — drop `event:` prefix, resume via
   `Last-Event-ID` header or query param
2. `5a9237b` `feat(sse)`: onmessage-based `useLiveEvents` hook — eventType-in-payload
   invalidation + resume
3. `44eb06e` `feat(sse)`: subscribe triage desk to live lead/interaction events — drop 30s lead
   polling
4. `c8e1dea` `feat(sse)`: subscribe billing ledger to live invoice/payment events — drop 30s
   invoice polling
5. `7503205` `test(sse)`: real-path endpoint protocol test + fake-EventSource hook test

All commits SSH-signed (key `SHA256:DLbAPxmdnlUiUmhUucu73oek6xR6aYKJ7W1rGvHu2ko`), every
`%G?` = `G`.

## Status

- [x] SSE frames are uniform `id`+`data` (no `event:` prefix) — verified by test
- [x] Triage desk live-subscribes to lead + interaction events; 30s lead polling removed
- [x] Billing ledger live-subscribes to invoice/payment/STK/reconciliation events; 30s polling removed
- [x] Resume works via `Last-Event-ID` header and `?lastEventId=` query param
- [x] 730 tests / 69 files green, `tsc --noEmit` exit 0, ESLint 0 errors on touched files
- [x] release-readiness row #56 → **PASS** (with cited tests)

## Owner Follow-ups

- Tier 2 backlog: notifications live (SSE) channel for WhatsApp *delivery* events without a page
  reload; consider a `useLiveEvents`-driven toast/toast-center next.
- Optional live smoke (already covered by automated tests): two-tab lead update in production.