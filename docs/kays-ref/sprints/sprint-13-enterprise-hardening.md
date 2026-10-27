# Sprint 13: Enterprise Hardening — PostgreSQL, TanStack Query, Degradation Resilience

## Timeline
- **Sprint:** 13
- **Focus:** Fault-tolerant DB layer, TanStack Query mutations with optimistic UI, cold-start degradation, Vercel BOA v3 cleanup

---

## Founder Narrative

The system graduated from a webhook proxy to a first-class PostgreSQL persistence layer. When `DATABASE_URL` is configured, every lead submission writes directly to `clinic_leads` via a TanStack Start server function with Zod validation. If the database is unreachable at cold start or during a connection blip, the system degrades gracefully — submissions queue to localStorage, the admin panel shows an amber "No Database Connection" banner instead of crashing, and retry is automatic.

On the triage side, `/admin/triage` was rebuilt on TanStack Query with `useSuspenseQuery`, 30s polling, and `useMutation` for every priority change, status update, and lead deletion — all with optimistic updates that roll back on server error. A new `/admin/diagnostics` engineering panel lets operators test the write path, inspect the offline queue, and verify degradation behaviour without touching production data.

---

## Section 1: Database Bootstrap Resilience

### `src/lib/db.server.ts` — Zero-Trust Cold-Start Singleton

- `getDb()` lazily initialises a `postgres` singleton on first call. If `DATABASE_URL` is missing or the connection fails, it sets `dbAvailable = false` and throws — but consumers are expected to use the guard functions, not catch the throw.
- `isDbAvailable()` and `getConnectionError()` let any caller probe state before touching the pool.
- `withDb<T>(fn, fallback)` wraps an arbitrary DB operation: on success it returns `fn(db)`; on any error it logs, sets `dbAvailable = false`, and calls `fallback()`.
- `ensureSchema()` runs the `CREATE TABLE IF NOT EXISTS clinic_leads` migration and returns `false` on failure instead of throwing.

**Table schema:**
```sql
CREATE TABLE IF NOT EXISTS clinic_leads (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(50) NOT NULL DEFAULT '',
  email VARCHAR(255) NOT NULL DEFAULT '',
  service VARCHAR(100) NOT NULL DEFAULT '',
  channel VARCHAR(50) NOT NULL DEFAULT '',
  priority VARCHAR(20) NOT NULL DEFAULT 'medium',
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  raw_payload JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `src/lib/api/leads.server.ts` — Server Functions with Discriminated Returns

| Function | Method | Zod Input | Return Type | Degradation |
|----------|--------|-----------|-------------|-------------|
| `submitLead` | POST | `{ name, phone?, email?, service?, channel?, priority?, raw_payload? }` | `{ id, status: "created" \| "db_unavailable" }` | Returns `db_unavailable` when DB down — caller queues for retry |
| `fetchLeads` | GET | — | `{ rows: LeadRow[]; source: "db" }` or `{ rows: []; source: "offline"; reason }` | Discriminated union lets UI distinguish "no data" from "DB offline" |
| `updateLead` | POST | `{ id, status?, priority? }` | `{ status: "updated" \| "db_unavailable" \| "noop" }` | Returns `db_unavailable` on failure |
| `deleteLead` | POST | `{ id }` | `{ status: "deleted" \| "db_unavailable" }` | Returns `db_unavailable` on failure |

Zod schema hardened in this sprint:
- `email`: now validates format with `.email("Enter a valid email address")`
- `phone`: capped to 50 chars
- `name`: min 1 char with clear error message
- `service` / `channel`: max-length bounded

---

## Section 2: State Mutations with TanStack Query

### `src/hooks/useLeads.ts` — Query + Mutation Hooks

**`useLeads()`** — `useSuspenseQuery<FetchLeadsResult>`:
- Query key `["leads"]`
- Auto-refetch every 30s (`refetchInterval`)
- 10s stale time

**`useUpdateLead()`** — `useMutation` with optimistic update:
- On mutate: cancel in-flight queries, snapshot current cache, apply update optimistically
- On error: roll back to snapshot
- On settled: invalidate query key to force server sync

**`useDeleteLead()`** — same pattern with optimistic removal from array.

All mutations guard on `data.source === "db"` before applying optimistic updates — no corrupt state when DB is offline.

### `src/hooks/useClinicOSSubmit.ts` — Cache Invalidation on Write

- Removed dead `submitLeadViaWebhook` import (function still exported for future use but no longer imported by the hook).
- After a successful `submitLead()` call, calls `queryClient.invalidateQueries({ queryKey: ["leads"] })` so the triage panel reflects the new lead immediately (instead of waiting up to 30s).
- After `flushQueue` drains all pending entries, also invalidates the query key.

---

## Section 3: Hydration & Rendering Safety

### `src/routes/admin/triage.tsx` — Rewritten for Hydration Consistency

**Hydration mismatch fixes:**
- `formatDate` switched from `toLocaleDateString("en-KE", ...)` (server/client ICU mismatch risk) to `date-fns` `format(new Date(iso), "d MMM, HH:mm")` — deterministic output across runtimes.
- `useOnlineStatus` replaced with proper `useEffect` that initialises state on mount (not in the initialiser) and registers `online`/`offline` event listeners.

**Polling / drop-down stability:**
- `InlineSelect`, `MetricsBar`, `QueueTable` all wrapped with `React.memo` to prevent re-render churn when background refetch returns the same data reference.

**Metadata banners (3 distinct states):**
| Data Source | Banner |
|-------------|--------|
| `source === "db"` + rows > 0 | Green "Live Database Active — Displaying N leads from PostgreSQL" |
| `source === "db"` + rows === 0 | Blue "Database Connected — No Leads Yet" |
| `source === "offline"` | Amber "No Database Connection — Set DATABASE_URL..." |
| Query error | Red "Query Failed" with inline retry |
| `pendingCount > 0` | Blue "Offline Queue Active — N submissions pending" |

**Recovered unused code removed:** `priorityDot`, `statusStyle`, `ClinicOSLeadPacket` import, `isLoading` destructuring.

---

## Section 4: Cold-Start & Degradation Verification

### `src/routes/admin/diagnostics.tsx` — Engineering Diagnostics Panel

Protected by same passcode gate (`0726`, 1h sessionStorage TTL). Four panels:

1. **Runtime Status** — checks browser env, network connectivity (`navigator.onLine`), DB reachability (via `getServerStatus` server fn), offline queue emptiness.
2. **Degradation Simulation** — documents every code path when `isDbAvailable()` returns `false`, confirming the ErrorBoundary is NOT triggered.
3. **Write-Path Verification** — one-click buttons to call `submitLead` and `fetchLeads` directly, displaying the raw JSON response.
4. **Offline Queue State** — renders the full `localStorage` queue as formatted JSON.

The `getServerStatus` server function (`src/lib/api/diagnostics.server.ts`) returns `{ dbAvailable, dbError, nodeEnv, region }` — this avoids importing `isDbAvailable()` directly from a page component, which would leak `postgres` imports into the client bundle.

---

## Section 5: Vercel Deployment Configuration

### `vercel.json` — Hardened for BOA v3

Before:
```json
{
  "cleanUrls": true,
  "rewrites": [{ "source": "/((?!api/|assets/|.*\\..*$).*)", "destination": "/index.html" }]
}
```

After:
```json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
    },
    {
      "source": "(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

- Removed `cleanUrls` and `rewrites` — unused with Build Output API v3; Nitro generates `.vercel/output/config.json` which takes precedence for routing.
- Added security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
- Asset caching header matches the immutable asset route from Nitro's BOA config.

### `.server.ts` Isolation Verified

- `postgres` module appears only in `__server.func/_libs/postgres.mjs` — verified zero occurrences in client-facing chunks.
- `diagnostics.server.ts` compiled to a separate server chunk (`_ssr/diagnostics.server-*.mjs`).
- `db.server.ts` never imported directly from any page component (`diagnostics.tsx` uses the `getServerStatus` server function instead).

---

## System Audit

| Check | Result |
|-------|--------|
| `npm run build` | ✅ ~9.5s, 0 errors |
| `postgres` isolated from client bundle | ✅ Server-only chunk |
| `date-fns` format deterministic across runtimes | ✅ No `toLocaleString` in render path |
| `InlineSelect` drop-down stable during background poll | ✅ `React.memo` applied |
| `submitLead` invalidates `["leads"]` query cache | ✅ |
| `flushQueue` invalidates cache on full drain | ✅ |
| Optimistic update rolls back on mutation error | ✅ `onError` restores `context.previous` |
| DB-offline returns `{ source: "offline" }` not throw | ✅ |
| ErrorBoundary NOT triggered by DB-offline | ✅ |
| `admin/diagnostics` page builds without pulling `postgres` into client | ✅ |
| Security headers set in `vercel.json` | ✅ |
| Admin passcode gate with 1h TTL | ✅ |

---

## Environment Variable Reference

| Variable | Scope | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | Server only | PostgreSQL connection string for `postgres` singleton |
| `NEXT_PUBLIC_CLINIC_OS_WEBHOOK_URL` | Client | Optional fallback webhook; if set, `useClinicOSSubmit` fires `fetch()` to this URL instead of the server fn |

---

## Files Changed

| File | Change |
|------|--------|
| `src/lib/db.server.ts` | Added `isDbAvailable()`, `getConnectionError()`, `withDb()`; graceful connection failure handling |
| `src/lib/api/leads.server.ts` | Zod validation hardened (email format, length bounds); `fetchLeads` returns `FetchLeadsResult` discriminated union; added `updateLead`, `deleteLead` |
| `src/lib/api/diagnostics.server.ts` | **New** — `getServerStatus` server fn |
| `src/hooks/useLeads.ts` | Rewritten for `FetchLeadsResult`; optimistic updates guard on `source === "db"` |
| `src/hooks/useClinicOSSubmit.ts` | Removed `submitLeadViaWebhook` import; added `useQueryClient()` + query invalidation on success/flush |
| `src/routes/admin/triage.tsx` | `date-fns` format; `useEffect` for online/offline; `React.memo`; 3-state metadata banners; removed dead code |
| `src/routes/admin/diagnostics.tsx` | **New** — passcode-gated diagnostics panel with write-path tests, degradation docs, queue inspector |
| `src/components/ui/error-boundary.tsx` | **New** (previous sprint) — class-based ErrorBoundary with fallback UI |
| `vercel.json` | Replaced `cleanUrls`+`rewrites` with security headers + asset cache |
