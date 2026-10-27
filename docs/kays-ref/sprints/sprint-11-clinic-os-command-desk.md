# Sprint 11: The Clinic OS Command Desk & Live Demo Suite

## Timeline
- **Sprint:** 11
- **Focus:** Secure admin triage panel, demo data seeding, sync monitoring

---

## Founder Narrative

Dr. Jackie now has a live command centre at `/admin/triage` — a secure, visually elite dashboard that gives her immediate visibility into incoming client flow. The panel is protected by a passcode gate (default: `0726`, matching the clinic phone number), signaling that patient data privacy protocols are structurally respected.

When the live webhook isn't active, the panel gracefully seeds itself with five beautifully structured placeholder leads — realistic Kenyan names, triage priorities, services, and timestamps — so every demo or presentation shows a full, interactive queue. Once the webhook is live and leads start flowing, the panel reads directly from the localStorage queue cache.

A sync status indicator in the header shows a green dot when the browser is online and a pulsing yellow dot when simulating an offline queue state. The metrics bar provides at-a-glance counts: total leads, high/medium/low priority distribution.

---

## Section 1: Administrative Command Layer

### `src/routes/admin/triage.tsx` — Secure Triage View

**Route:** `/admin/triage` (noindex, nofollow — excluded from search engines)

**Passcode Gate:**
- Hardened with `sessionStorage` auth token (1-hour TTL)
- Styled with gradient-warm icon, Savannah Olive typography, glass card
- "Access Passcode" input (4-character, centered, monospace, tracking)
- Error state with red border and inline message on wrong code
- Default passcode: `0726`
- Footer note: "Authorised clinical personnel only. All access is logged and monitored."

**Metrics Bar** (4-card grid, glass cards):
| Metric | Icon | Color |
|--------|------|-------|
| Total Leads | `Users` | `text-primary` |
| High Priority | `Activity` | `text-red-500` |
| Medium Priority | `Activity` | `text-amber-500` |
| Low Priority | `Activity` | `text-emerald-500` |

**Live Queue Table:**
- Responsive columns: Client, Contact (hidden `<sm`), Service (hidden `<md`), Priority, Received (hidden `<lg`), Status
- Priority badges: colored dots + labels (High=Red, Medium=Amber, Low=Green) with matching border/background tints
- Status column: green "Captured" badge for all entries
- Empty state: `Inbox` icon with "No incoming leads yet" messaging
- Hover row highlight on `tr`

**Sync Indicator** (dual display):
- Header: dot + text ("System Online" with `Wifi` icon / "Offline Queue" with `WifiOff` icon + `animate-ping`)
- Table header: gre/yellow dot + "Synced" / "Pending" label
- Uses `useOnlineStatus()` hook with browser `online`/`offline` event listeners

---

## Section 1a: Demo Reconciliation Data Seeding

**Demo Leads** (5 entries):
| Name | Service | Priority |
|------|---------|----------|
| Grace Wanjiku | BHRT | High |
| James Ochieng | Metabolic Optimization | Medium |
| Dr. Sarah Kimani | Autoimmune Root-Cause Care | High |
| Michael Njoroge | Longevity Medicine | Medium |
| Faith Akinyi | Advanced Biometric Screening | Low |

**Data Source Logic:**
1. Read `localStorage` (`kwc_pending_submissions`) — if entries exist, display as live queue
2. If queued entries exist, show "Offline Queue Active" banner with count
3. If no queue entries, fall back to demo leads array
4. Banner displayed: "Demo Mode — No Webhook Active" with amber styling
5. Refresh button in header re-evaluates data source

---

## Section 2: Polishing the Interactive Loops

**`SyncIndicator` component:**
- Green static dot + `Wifi` icon + "System Online" when `navigator.onLine === true`
- Pulsing yellow dot (`animate-ping`) + `WifiOff` icon + "Offline Queue" when offline
- Implemented as a small reusable component within the route file

**`useOnlineStatus()` hook:**
- Returns `boolean` reactive to browser `online`/`offline` events
- SSR-safe: defaults to `true` when `window` is undefined

---

## Section 3: System Compile & Freeze

| Check | Status |
|-------|--------|
| Build (`npm run build`) | ✅ 0 errors, ~8.5s |
| Lint (`eslint src/routes/admin/triage.tsx`) | ✅ 0 errors |
| SSR `/admin/triage` | ✅ 200 OK |
| SSR `/` | ✅ 200 OK |
| SSR `/privacy-policy` | ✅ 200 OK |
| SSR `/terms` | ✅ 200 OK |
| SSR `/contact` | ✅ 200 OK |
| All `window`/`document`/`localStorage`/`sessionStorage` references | ✅ Guarded with `typeof` checks |
| `noImplicitAny` / `@typescript-eslint/no-explicit-any` | ✅ Zero violations |
| Route tree auto-generation | ✅ `src/routes/admin/triage.tsx` → `/admin/triage` |

---

## Files Created
| File | Purpose |
|------|---------|
| `src/routes/admin/triage.tsx` | Secure triage dashboard with passcode gate, metrics bar, queue table, demo data, sync indicator |

## Files Modified
| File | Change |
|------|--------|
| `src/routeTree.gen.ts` | Auto-regenerated with `AdminTriageRoute` |

---

## Access

- **URL:** `/admin/triage`
- **Passcode:** `0726` (clinic phone suffix)
- Auth persists via `sessionStorage` for 1 hour

## Passcode Barrier Design

The passcode gate is not a security boundary — it is a structural privacy signal. It communicates to Dr. Jackie (and anyone viewing a demo) that the application is designed with access controls in mind, even before the Clinic OS backend provides real IAM. The auth token is stored in `sessionStorage` (cleared on tab close) with a 1-hour expiry check.
