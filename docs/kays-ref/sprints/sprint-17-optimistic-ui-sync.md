# Sprint 17 — Optimistic UI Sync, Client-Side Fault Visibility & Frontend Resilience

## Objective
Bring hardened back-end resilience directly to the user interface so that non-technical clinic staff experience a seamless, lightning-fast application regardless of local network fluctuations. Refactor client-side submission handlers with optimistic updates, create a global network status indicator with queue telemetry, and add frontend-focused integration tests.

## Deliverables

### 1. Enhanced Optimistic UI Mutations (`src/hooks/useLeads.ts`)
- **`useUpdateLead`** — `onMutate` updates the React Query cache immediately (optimistic). `onSuccess` fires a Sonner `toast.success` with the field name and new value. `onError` rolls back to previous cache state and fires `toast.error` with a descriptive message. `onSettled` cleans up and invalidates the query. Tracks `mutatingIds: Set<number>` for per-row visual feedback.
- **`useDeleteLead`** — Same optimistic pattern: `onMutate` removes the row from cache, `onSuccess` toasts, `onError` rolls back with restore message. Also exposes `mutatingIds`.

### 2. Optimistic Booking Submissions (`src/hooks/useClinicOSSubmit.ts`)
- `submit()` now tracks `pendingOptimistic` entries via `getOptimisticLeads()` — a module-level `Map<id, { name, status }>` where status cycles through `"saving"` → `"sent"` | `"failed"`. Entries auto-expire after 3 seconds.
- The `finalizeOptimistic` callback runs in all three paths: online submit, DB unavailable queue, and catch error queue.

### 3. Global Network Status Component (`src/components/NetworkStatus.tsx`)
- Reusable, responsive, accessible component showing connection state with animated LED indicator (green for online, red ping for offline).
- Dropdown panel with queue telemetry: last sync time, dispatch failure count, sync status ("Idle"/"Syncing...").
- "Sync Now" button to manually trigger `triggerQueueProcessing`.
- Self-dismissing overlay click-to-close pattern.
- Styled for admin header integration — compact on mobile (`hidden sm:inline`).

### 4. Network Status + Queue Telemetry Hook (`src/hooks/useNetworkStatus.ts`)
- Tracks `navigator.onLine` via browser `online`/`offline` events.
- Polls `triggerQueueProcessing` every 30 seconds.
- Returns `{ online, queueStats, isSyncing, triggerSync }`.
- Silently catches polling errors — queue telemetry is best-effort.

### 5. Triage Console Updates (`src/routes/admin/triage.tsx`)
- Replaced local `SyncIndicator` with `NetworkStatus` component in the header.
- Per-row loading indicator: spinning `RefreshCw` icon on the lead name when `allMutating.has(lead.id)`.
- Delete button shows a `Loader2` spinner while the mutation is in flight.
- Removed redundant `useEffect`/`useState` for online tracking (now in `useNetworkStatus`).
- Removed unused `Wifi`, `WifiOff`, `useNavigate`, `useEffect` imports.

### 6. Diagnostics Panel Updates (`src/routes/admin/diagnostics.tsx`)
- New "Notification Queue Telemetry" panel showing last sync time and dispatch failure count.
- "Trigger Queue Processing" button that calls `triggerSync()` from `useNetworkStatus`.
- Added `Bell`, `Loader2`, `useNetworkStatus` imports.

### 7. Module Changes Summary

| File | Change |
|---|---|
| `src/hooks/useLeads.ts` | **Enhanced** — Optimistic toasts, per-row `mutatingIds`, rollback with restore message |
| `src/hooks/useClinicOSSubmit.ts` | **Enhanced** — `getOptimisticLeads()`, `finalizeOptimistic` callback, `STORAGE_KEY_EXPORTED` |
| `src/hooks/useNetworkStatus.ts` | **New** — Online state + queue polling + triggerSync |
| `src/components/NetworkStatus.tsx` | **New** — Network status indicator with queue telemetry dropdown |
| `src/routes/admin/triage.tsx` | **Updated** — `NetworkStatus` header, per-row mutation indicators, removed old SyncIndicator |
| `src/routes/admin/diagnostics.tsx` | **Updated** — Queue telemetry panel, `NetworkStatus` in header |
| `src/__tests__/optimistic-updates.test.ts` | **New** — 6 tests: `LEADS_QUERY_KEY`, triage priority, sanitize input, telemetry shape, optimistic leads |
| `src/__tests__/network-status.test.ts` | **New** — 1 test: component export assertion |

### 8. Test Results
- 41 tests pass (34 existing + 7 new).
- Build succeeds cleanly (client + SSR + Nitro/Vercel).

## Key Design Decisions
- **Sonner toasts on mutation success, not just error** — Staff need positive confirmation their change was persisted, not just absence of error.
- **`mutatingIds` tracked per-lead, not globally** — Enables fine-grained UI feedback (spinner on the specific row being changed) without re-rendering the entire table.
- **`getOptimisticLeads` as module-level Map** — Avoids the overhead of React context for a transient visual state that self-cleans after 3 seconds.
- **Queue polling every 30s, not real-time** — Reduces server function call volume. Staff can click "Sync Now" for immediate processing.
- **No jsdom/happy-dom for component tests** — Tests assert against pure functions (`sanitizeInput`, `computeTriagePriority`, `LEADS_QUERY_KEY`, `getOptimisticLeads`). Component rendering is validated via the production build.

## Retrospective

### What went well
- The existing `onMutate`/`onError` pattern in `useLeads.ts` was already structurally sound — adding Sonner toasts and `mutatingIds` was a clean extension with no refactoring.
- Separating `useNetworkStatus` as its own hook keeps the network concern portable across admin pages.
- Pure-function tests (`computeTriagePriority`, `sanitizeInput`) are fast and stable — no React runtime needed.

### What could be improved
- `isAuthenticated`, `PasscodeGate`, and `CheckLabel` in `diagnostics.tsx` are still unresolved at the type level — they appear to be injected by the Lovable.dev build plugin. A proper import would make the type checker happy.
- The `useNetworkStatus` hook uses dynamic `import()` for `triggerQueueProcessing`, which works but adds a small async overhead on each poll cycle.
- Per-row mutation indicators only show a spinner — adding a brief green checkmark animation on success would improve the tactile feel.

## Known Issues
- `mutatingIds` uses `useState` inside the custom hook — each component instance gets its own set. This works correctly for the triage page (single instance) but would need a context if multiple components needed shared mutation state.
- No `happy-dom` added to the test suite — component rendering tests require jsdom/happy-dom setup which is deferred to a future sprint.
