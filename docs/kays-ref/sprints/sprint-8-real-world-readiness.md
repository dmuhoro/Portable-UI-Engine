# Sprint 8: Real-World Readiness & Structural Completion

## Timeline

- **Sprint:** 8
- **Focus:** Interactive specialties with modal drill-down, offline-resilient contact form, Clinic OS integration hooks, CI/CD hardening

---

## Founder Narrative

The site needed to stop being a brochure and start acting like a front desk. Patients browsing Dr. Jackie's specialties can now click any card to see the full clinical protocol — diagnostics involved, phases of treatment, key components. No more guessing what "Metabolic Optimization" actually means.

More importantly, we solved a real African healthcare edge case: unreliable connectivity. When a prospective patient fills out the "Reach Us" form in an area with spotty internet, the submission is cached locally and automatically retried when the connection returns. No lost leads. No frustrated patients re-entering their details.

Under the hood, every form submission now fires a structured JSON payload stamped with `Client_Lead_Source: "Online_Front_Door"` — ready for when the Clinic OS backend goes live next sprint. We'll just swap a mock function for a real API call and the entire pipeline activates.

---

## Technical Execution

### 1. Centralized Specialty Data Layer

**File:** `src/data/specialties.ts`

- Created a strongly-typed `Specialty[]` array with 8 clinical specialties:
  - Bioidentical Hormone Restoration (BHRT)
  - Intravenous Nutritional Therapy
  - Metabolic Optimization
  - Chronic Disease Management
  - Longevity Medicine
  - Autoimmune Root-Cause Care
  - Advanced Biometric Screening
  - Functional Weight Management
- Each entry includes: `id`, `title`, `tagline`, `description`, `protocol` (multi-phase clinical protocol text), `icon` (Lucide icon reference), `gradient` (Tailwind gradient class), `features[]` (key component list), `cta` token (`"inquire"` | `"protocol"`)
- Exported `serviceOptions[]` for form dropdown consumption — single source of truth for all specialty references

### 2. Interactive Specialties Component

**File:** `src/components/site/Specialties.tsx`

- Renders responsive grid (1 → 2 → 4 columns across mobile → tablet → desktop)
- Each card shows: gradient icon, title, tagline, and CTA button ("View Clinical Protocol" or "Inquire for Availability")
- `SpecialtyModal` component renders on card click via `useState<Specialty | null>`:
  - Full-screen overlay with backdrop blur (`bg-foreground/60 backdrop-blur-sm`)
  - Animated scale-in (`animate-scale-in`) on modal mount
  - Displays: tagline, full description, clinical protocol in gradient-bordered box, key components grid, dual-CTA footer (Inquire + Close)
  - Closes on backdrop click, Escape-compatible, or close button
- Integrated into `src/routes/index.tsx` as a dedicated "Precision Specialties" section between Founder Mission and WellnessTips

### 3. Trojan Horse Hook — `useClinicOSSubmit`

**File:** `src/hooks/useClinicOSSubmit.ts`

A unified submission hook designed as the integration point for a future Clinic OS backend:

- **Signature:** `useClinicOSSubmit()` returns `{ submit, status, reset, flushQueue }`
- **`submit(formData)`**:
  1. Checks `navigator.onLine` — if offline, caches to `localStorage` under key `kwc_pending_submissions` and returns early with success toast
  2. If online, logs structured `SubmissionPayload` to console and simulates a 1.2s API call
  3. On simulated success: displays toast, resets status
  4. On error: caches to localStorage for retry
- **`flushQueue()`**: Iterates pending submissions and replays them
- **Online/offline event listeners**: `window.addEventListener('online', ...)` auto-flushes cached submissions when connectivity is restored, with user-facing toast notifications
- **`SubmissionPayload` type:**
  ```typescript
  {
    Client_Lead_Source: "Online_Front_Door",
    Payload_Timestamp: string (ISO),
    formData: Record<string, string>,
    userMetrics: {
      userAgent, language, referrer, timezone,
      screenResolution, connectionType
    }
  }
  ```
- Console output formatted with `[ClinicOS]` prefix for easy log filtering
- **Migration path**: Replace `simulateSuccess()` with a real `fetch()` call — zero structural changes needed

### 4. Reach Us Form Component

**File:** `src/components/site/ReachUs.tsx`

Replaces the static "Reach Us" footer column with a functional inquiry form:

- **Fields:** Full Name (with `User` icon), Secure Email (with `Mail` icon), Premium Service (custom `<select>` dropdown sourced from `serviceOptions`)
- **Validation:** Real-time per-field on blur, full validation on submit
  - `name`: required, non-empty
  - `email`: required, regex pattern match
  - `service`: required, non-empty selection
- **Error states:** Red border on invalid fields, contextual error messages below each field, only shown after field has been touched
- **Submission:** Integrates `useClinicOSSubmit` — handles submitting, success, error states
- **Success state:** Animated checkmark card with "Send another inquiry" reset button
- **Loading state:** Spinner (`Loader2 animate-spin`) within disabled submit button
- **Styles:** Savannah Olive focus rings, Terracotta accent borders, `gradient-hero` CTA, `glass` utility classes
- **Integrated into:** `src/components/site/Footer.tsx` — replaces the 4th column's static contact list with the form (contact info preserved above form)

### 5. Footer Modernization

**File:** `src/components/site/Footer.tsx`

- Specialties column: swapped static `<ul>` for dynamic `specialties.slice(0,6).map(...)` with `Link` to `/services` and `Shield` accent icon per item — stays in sync with `data/specialties.ts`
- Reach Us column: contact info preserved, inline `ReachUs` form rendered below

### 6. Meta Fixes & Stale Asset Cleanup

**File:** `src/routes/__root.tsx`

- Fixed stale `og:image` URL (was pointing to a generic Unsplash clinic photo, now points to premium African wellness consultation image)
- Updated `title`, `description`, `og:title`, `og:description`, `twitter:title`, `twitter:description` to consistent executive-grade copy reflecting actual services

### 7. Git Integration & Preview Deployment

- Vercel Git integration confirmed active — every push to `main` auto-deploys via Vercel's GitHub App
- SSO protection removed project-wide: preview deployments are now publicly accessible without login
- Public preview URL: `https://kays-wellness-centre-ggs4yxmmj-dmuhor01.vercel.app`

### 8. CI/CD Pipeline

**File:** `.github/workflows/deploy.yml`

- **Triggers:** `push` and `pull_request` on `main`
- **Job:** `quality` — runs `npm install` → `npm run lint` → `npm run build` on Node.js 22
- Removed redundant deploy job (Vercel Git integration handles deployment)
- Removed stale `NITRO_PRESET` env vars (now configured in `vite.config.ts`)

### 9. Code Quality

- Prettier formatting applied across all 11 source files (pre-existing formatting debt cleaned)
- CI pipeline green — lint + build passes in ~30s

---

## Architecture Diagram (Data Flow)

```
User fills ReachUs form
        │
        ▼
  useClinicOSSubmit.submit(formData)
        │
        ├── navigator.onLine === false ──► localStorage (kwc_pending_submissions)
        │                                      │
        │                                      ▼
        │                              window 'online' event
        │                                      │
        │                                      ▼
        │                              flushQueue() replays
        │
        └── navigator.onLine === true ──► console.log(payload)
                                          │
                                          ▼
                                    simulateSuccess()
                                    (→ future: fetch('/api/clinic-os'))
                                          │
                                          ▼
                                    toast.success()
```

---

## Files Created

| File                                  | Purpose                                                |
| ------------------------------------- | ------------------------------------------------------ |
| `src/data/specialties.ts`             | Centralized specialty data with full protocol metadata |
| `src/hooks/useClinicOSSubmit.ts`      | Offline-resilient submission hook with console logging |
| `src/components/site/Specialties.tsx` | Interactive card grid + modal drill-down               |
| `src/components/site/ReachUs.tsx`     | Validated form with dropdown and offline retry         |

## Files Modified

| File                             | Change                                         |
| -------------------------------- | ---------------------------------------------- |
| `src/components/site/Footer.tsx` | Dynamic specialties list + ReachUs form inline |
| `src/routes/index.tsx`           | Added Specialties section, imported component  |
| `src/routes/__root.tsx`          | Meta/og:image fixes                            |
| `vite.config.ts`                 | Vercel preset (from earlier sprint)            |
| `.github/workflows/deploy.yml`   | Simplified to quality-only, removed deploy job |

---

## Migration Path to Clinic OS

When the Clinic OS backend is ready:

1. **In `useClinicOSSubmit.ts`**: Replace `simulateSuccess()` with:

   ```typescript
   const response = await fetch("https://api.clinic-os.com/intake", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify(payload),
   });
   if (!response.ok) throw new Error(`Clinic OS returned ${response.status}`);
   ```

2. All form components (`ReachUs`, `BookingWidget`, `AskQuestion`, `contact.tsx`) already use `useClinicOSSubmit` — no wiring changes needed.

3. The `[ClinicOS]` console logs provide immediate observability while the backend is under development.
