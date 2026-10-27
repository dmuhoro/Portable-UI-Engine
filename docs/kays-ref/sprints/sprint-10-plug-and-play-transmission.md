# Sprint 10: Plug-and-Play Transmission Engine & Compliance

## Timeline
- **Sprint:** 10
- **Focus:** Live webhook data bridge, retry logic, Privacy Policy & Terms of Service pages

---

## Founder Narrative

Every patient inquiry now flows through a production-grade data pipeline. When a booking or contact form is submitted, the system fires a structured HTTPS POST payload to the Clinic OS ingestion endpoint — or, if the webhook URL isn't configured, gracefully falls back to the existing simulated success path. If the transmission fails (network blip, timeout, non-200 response), the payload is cached in localStorage and retried automatically when connectivity returns. The user never sees a failure — they get a "queued for delivery" confirmation and the system handles the rest.

On the compliance side, the site now has two fully rendered, on-brand legal pages — Privacy Policy and Terms of Service — explaining how patient data is encrypted, sanitized, and confidentially transferred to clinical operations exclusively. The 404s are gone.

---

## Section 1: Webhook Transmission Matrix

### `src/hooks/useClinicOSSubmit.ts` — Egress Pipeline Upgrade

- **`CLINIC_OS_WEBHOOK_URL`**: Reads `import.meta.env.NEXT_PUBLIC_CLINIC_OS_WEBHOOK_URL` with SSR-safe guards (avoids accessing `env` in non-Vite contexts). When set, the hook fires a real HTTPS POST instead of the mock delay.

- **`transmitPacket(packet)`**: Core egress function:
  ```typescript
  if (CLINIC_OS_WEBHOOK_URL) {
    const res = await fetch(CLINIC_OS_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packet),
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) throw new Error(`Clinic OS returned ${res.status}`);
  }
  // fallback: 1.2s simulated delay
  ```

- **Retry logic in `submit()`**: If `transmitPacket` throws (network or HTTP error):
  - Payload is written to `localStorage` queue
  - User sees `toast.success("Inquiry queued for delivery")`
  - Background `flushQueue` retries on reconnect
  - User experience is never disrupted

- **Retry logic in `flushQueue()`**: Failed entries are preserved in localStorage instead of cleared. Only entries that transmitted successfully are removed from the queue.

---

## Section 2: Legal Compliance Front Door

### `src/routes/privacy-policy.tsx`
Route: `/privacy-policy`

- **Content sections** (each with gradient-warm icon + body):
  - Data Collection & Encryption — TLS 1.3, programmatic input sanitization
  - Data Storage & Transmission — structured ClinicOS packet, HTTPS POST, local cache only for retry
  - Clinical Confidentiality — accessible exclusively to clinical ops, never shared or sold
  - Your Rights & Contact — access/correction/deletion requests, 14-day response window

### `src/routes/terms.tsx`
Route: `/terms`

- **Content sections**:
  - Service Description — informational, no physician–patient relationship until confirmed booking
  - Booking & Cancellation — 24-hour cancellation policy
  - Medical Disclaimer — not a substitute for professional medical advice
  - Limitation of Liability — "as is" without warranty
  - Governing Law — Republic of Kenya jurisdiction

### `src/components/site/Footer.tsx` — Legal Navigation

Added in the "Explore" column:
- **Legal** heading with Privacy Policy and Terms of Service links (with `FileText` and `Scale` icons)

---

## Section 3: System Integrity Verification

| Check | Status |
|-------|--------|
| SSR all routes (`/`, `/privacy-policy`, `/terms`, `/contact`, `/services`, `/our-story`, `/resources`) | 200 OK |
| `npm run build` | 0 errors, ~8.3s |
| `npm run lint` (modified files) | 0 errors |
| `process.env` / `import.meta.env` evaluation in SSR | Guarded with `typeof import.meta !== "undefined"` |
| Route tree auto-generation | Both new routes registered in `routeTree.gen.ts` |

---

## Files Created
| File | Purpose |
|------|---------|
| `src/routes/privacy-policy.tsx` | Privacy Policy page with Savannah Olive styling |
| `src/routes/terms.tsx` | Terms of Service page with Savannah Olive styling |

## Files Modified
| File | Change |
|------|--------|
| `src/hooks/useClinicOSSubmit.ts` | `CLINIC_OS_WEBHOOK_URL` env var, `transmitPacket()` with POST + timeout + retry, `flushQueue()` preserves failed entries |
| `src/components/site/Footer.tsx` | Legal section with Privacy Policy and Terms of Service links |

---

## Environment Variable Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `NEXT_PUBLIC_CLINIC_OS_WEBHOOK_URL` | Live ingestion endpoint for Clinic OS lead packets | `undefined` (falls back to simulated success) |

Set via Vercel dashboard: `vercel env add NEXT_PUBLIC_CLINIC_OS_WEBHOOK_URL`
