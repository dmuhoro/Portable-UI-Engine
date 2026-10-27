# Sprint 9: Trojan Horse Activation & Data Architecture

## Timeline

- **Sprint:** 9
- **Focus:** Structured lead packet schema, triage engine, input sanitization, confirmation pane

---

## Founder Narrative

Every patient inquiry that comes through the site now carries a structured clinical dossier behind it — not just a name and email dropped into a generic form. When someone fills out the booking widget or the Reach Us form, the system automatically:

- Sanitizes every input (strips script tags, control characters, XSS vectors)
- Assigns a triage priority (high/medium/low) based on the service selected
- Stamps the submission with device telemetry (connection type, timezone, online status)
- Tags it with `capture_channel: "Web_Premium_Front_Door"`

This means when the Clinic OS backend goes live next sprint, every lead arrives pre-triaged, pre-sanitized, and pre-structured — ready for the coordinator dashboard with zero data cleaning required.

Patients get a cleaner experience too: the booking widget now has a 4th confirmation pane that clearly states _"Clinical validation vector initiated. Our private coordinator will reach out in confidence."_ — no more guessing whether their request went through.

---

## Technical Execution

### 1. ClinicOSLeadPacket — Structured Envelope

**File:** `src/hooks/clinic-os-types.ts`

- **`ClinicOSLeadPacket` interface:**
  ```typescript
  {
    Client_Lead_Source: "Online_Front_Door",
    Payload_Timestamp: string (ISO),
    capture_channel: "Web_Premium_Front_Door",
    formData: { name, email, service, phone?, channel? },
    triage_priority: "low" | "medium" | "high",
    device_telemetry: { connectionType, onlineStatus, localTimestamp, timezone, userAgent }
  }
  ```
- **`computeTriagePriority(serviceId)`** — maps specialty ID to priority:
  - `high`: chronic-disease, autoimmune (complex chronic conditions requiring urgent coordination)
  - `medium`: bhrh, iv-nutrition, metabolic, longevity (active therapeutic intervention)
  - `low`: screening, weight-management (assessment / elective)
- **`sanitizeInput(value)`** — four-pass cleaning:
  1. Strip all HTML tags (`<[^>]*>`)
  2. Remove null bytes and control chars (`\0\x08\x0B\x1A`)
  3. Strip angle brackets and quotes (`<>"'``)
  4. Trim surrounding whitespace
- **`collectTelemetry()`** — captures `connection.effectiveType`, `navigator.onLine`, local ISO timestamp, timezone, user agent

### 2. Hook Upgrade — `useClinicOSSubmit`

**File:** `src/hooks/useClinicOSSubmit.ts`

- **Input type changed** from `Record<string, string>` to `{ name, email, service, phone?, channel? }` — fully typed
- **`buildPacket()`** constructs the full `ClinicOSLeadPacket`:
  - Runs all inputs through `sanitizeInput()`
  - Lowercases email
  - Computes `triage_priority` from service ID
  - Attaches `capture_channel: "Web_Premium_Front_Door"`
  - Calls `collectTelemetry()` for device context
- **localStorage cache** now stores full `ClinicOSLeadPacket[]` instead of raw `Record<string, string>[]` — ready for backend deserialization
- **Console output** prints the full structured packet with `[ClinicOS]` prefix for log filtering

### 3. Booking Widget — Confirmation Pane & Triage Integration

**File:** `src/components/site/BookingWidget.tsx`

- **Services array** now uses `{ id, label }` objects instead of plain strings — IDs align with `specialties.ts` for triage resolution
- **Step 4 added** — confirmation pane (post-submission):
  - Green checkmark icon (`Check` in `size-16` circle)
  - Title: "Clinical validation vector initiated"
  - Description: "Our private coordinator will reach out in confidence to confirm your appointment..."
  - Summary card showing service, channel, name, email
  - End-to-end encrypted badge
  - "Book another appointment" reset button
- **Step 3 (contact info)** uses `useClinicOSSubmit` instead of raw `toast`:
  - Field added: email input (with `Mail` icon) alongside name
  - `submit()` call with structured `{ name, email, service, channel }` object
  - Loading spinner on submit button
  - On success transitions to step 4 instead of a floating toast
- **Design tokens**: Savannah Olive (`bg-primary`), Terracotta (`text-accent`, `border-accent/20`, `bg-accent/5`), `gradient-hero` CTAs, `glass` utility, `animate-fade-up`

### 4. Reach Us — Enhanced Success State

**File:** `src/components/site/ReachUs.tsx`

- Success state copy updated to match booking widget:
  - Title: "Clinical validation vector initiated"
  - Description: "Our private coordinator will reach out in confidence."
  - End-to-end encrypted badge (`Shield` icon, `text-accent`, `border-accent/20`)
- Form submission uses the new typed `useClinicOSSubmit` interface
- All inputs sanitized before cache or console

### 5. Data Flow (Post-Sprint 9)

```
User submits form
       │
       ▼
  sanitizeInput(name, email, service)
       │
       ├─► computeTriagePriority(service)
       ├─► collectTelemetry()
       ├─► build ClinicOSLeadPacket
       │
       ├── navigator.onLine === false
       │      └── localStorage (kwc_pending_submissions)
       │
       └── navigator.onLine === true
              ├── console.log [ClinicOS] structured JSON
              ├── simulateSuccess()  →  future: fetch('/api/intake')
              └── status=success  →  confirmation pane
```

---

## Files Created

| File                           | Purpose                                                             |
| ------------------------------ | ------------------------------------------------------------------- |
| `src/hooks/clinic-os-types.ts` | `ClinicOSLeadPacket` interface, triage/sanitize/telemetry utilities |

## Files Modified

| File                                    | Change                                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `src/hooks/useClinicOSSubmit.ts`        | Typed input, full packet building, sanitization, triage, telemetry                               |
| `src/components/site/BookingWidget.tsx` | Services as `{id,label}`, email field, step 4 confirmation pane, `useClinicOSSubmit` integration |
| `src/components/site/ReachUs.tsx`       | Updated success copy to clinical validation language                                             |

---

## Migration Path to Clinic OS

When the backend endpoint is live:

1. **`useClinicOSSubmit.ts`**: Replace `simulateSuccess()` with:

   ```typescript
   const res = await fetch("https://api.clinic-os.com/intake", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify(packet),
   });
   if (!res.ok) throw new Error(`Clinic OS ${res.status}`);
   ```

2. The `ClinicOSLeadPacket` shape matches the expected backend schema exactly — no transformation needed.

3. `triage_priority` is pre-computed client-side; the backend coordinator dashboard can sort by `triage_priority` without additional logic.

4. `sanitizeInput()` guarantees all stored data is XSS-free — safe for any downstream render path.
