# Sprint 12: Universal Cloud Integration & Live Pilot Hardening

## Timeline
- **Sprint:** 12
- **Focus:** Live cloud data bridge, admin GET consumption, error-boundary fallback chain

---

## Founder Narrative

The platform now speaks to the cloud in both directions. When a patient submits a booking or inquiry, `transmitPacket()` fires a structured HTTPS POST to the Clinic OS webhook endpoint — carrying name, sanitized contact, triage priority weight, and timestamp as a clean JSON envelope. If the endpoint is not yet configured, the system gracefully falls back to the simulated delay path.

On the admin side, `/admin/triage` now executes an authenticated HTTPS GET on mount against the `NEXT_PUBLIC_CLINIC_OS_QUERY_URL` endpoint. If the cloud responds, the dashboard renders live lead data with a green "Live Cloud Feed Active" banner. If the query fails (network timeout, non-200, DNS failure), the system catches the error transparently, shows a red "Cloud Query Failed" alert with a Retry button, and falls through to the localStorage queue or demo data — the dashboard never crashes.

---

## Section 1: The Synchronized Storage Bridge

### `src/hooks/useClinicOSSubmit.ts` — Outbound Emission Hardened

- **Shared utilities extracted**:
  - `readEnv(name)` — SSR-safe environment variable reader (repeated inline casts replaced with a single helper)
  - `getPending()` — now `export`ed so the admin panel reads from the same source
  - `STORAGE_KEY` and `CLINIC_OS_QUERY_URL` — `export`ed for cross-module use

- **`transmitPacket()`** (unchanged in signature, now explicitly documented):
  - Fires `POST ${CLINIC_OS_WEBHOOK_URL}` with `Content-Type: application/json`
  - Body: full `ClinicOSLeadPacket` JSON — includes `formData.name`, `formData.email`, `triage_priority`, `Payload_Timestamp`, `device_telemetry`
  - Falls back to 1.2s simulated delay when URL is undefined
  - 10s `AbortSignal.timeout` prevents hanging connections

**Outbound JSON structure:**
```json
{
  "Client_Lead_Source": "Online_Front_Door",
  "Payload_Timestamp": "2026-07-07T16:00:00.000Z",
  "capture_channel": "Web_Premium_Front_Door",
  "formData": {
    "name": "Grace Wanjiku",
    "email": "grace.w@example.com",
    "service": "bhrh",
    "phone": "+254722123456",
    "channel": "in-person"
  },
  "triage_priority": "high",
  "device_telemetry": {
    "connectionType": "4g",
    "onlineStatus": true,
    "localTimestamp": "2026-07-07T19:00:00.000Z",
    "timezone": "Africa/Nairobi",
    "userAgent": "Mozilla/5.0 ..."
  }
}
```

---

## Section 2: Administrative Backend Consumption

### `src/routes/admin/triage.tsx` — Live GET Fetch with Fallback Chain

**Data source priority:**
```
Mount → GET ${CLINIC_OS_QUERY_URL}
         ↓ success → "live" source (green "Live Cloud Feed Active" banner)
         ↓ failure → set queryError=true, fall through
       → localStorage (kwc_pending_submissions)
         ↓ entries found → "pending" source (blue "Offline Queue Active" banner)
         ↓ empty → demoLeads array → "demo" source (amber "Demo Mode" banner)
```

**Implementation details:**
- `useEffect` with an async `load()` function and `cancelled` flag (prevents state updates after unmount)
- 8s `AbortSignal.timeout` on the GET request
- Response validated: must be an array — single objects, null, or non-JSON are all caught
- `queryError` state tracked separately from `dataSource` so the retry banner persists across refresh cycles

**Error boundary UX:**
- Red `AlertCircle` banner: "Cloud Query Failed — Could not reach the Clinic OS data endpoint. Displaying cached or sample data."
- Inline Retry button that calls `refresh()` to re-run the full fetch chain
- The underlying components (`MetricsBar`, `QueueTable`) never see the error — they always receive a valid `leads` array from one of the three sources

**Passcode barrier unchanged** — `sessionStorage` auth with 1-hour TTL, passcode `0726`.

---

## Section 3: System Audit & Freeze

| Check | Result |
|-------|--------|
| `npm run build` | ✅ 0 errors, ~7.9s |
| `eslint` (useClinicOSSubmit.ts, triage.tsx) | ✅ 0 errors |
| SSR `/admin/triage` | ✅ 200 OK |
| SSR `/` | ✅ 200 OK |
| SSR `/privacy-policy`, `/terms`, `/contact` | ✅ 200 OK each |
| `window`/`localStorage`/`import.meta.env` guards | ✅ All SSR-safe |
| `getPending`/`STORAGE_KEY`/`CLINIC_OS_QUERY_URL` | ✅ Exported from shared module |
| Cancelled flag prevents stale state after unmount | ✅ |
| Demo fallback when no query URL + empty queue | ✅ |

---

## Environment Variable Reference

| Variable | Direction | Purpose |
|----------|-----------|---------|
| `NEXT_PUBLIC_CLINIC_OS_WEBHOOK_URL` | POST (outbound) | Ingestion endpoint for lead submissions |
| `NEXT_PUBLIC_CLINIC_OS_QUERY_URL` | GET (inbound) | Query endpoint for admin triage panel |

Both read via SSR-safe `readEnv()` helper — no `process.env` or bare `import.meta.env` access.

---

## Files Modified
| File | Change |
|------|--------|
| `src/hooks/useClinicOSSubmit.ts` | Extracted `readEnv()` helper; exported `getPending`, `STORAGE_KEY`, `CLINIC_OS_QUERY_URL` |
| `src/routes/admin/triage.tsx` | Added live GET fetch with 3-source fallback chain (cloud → localStorage → demo), error boundary with retry button, live/error banners |
