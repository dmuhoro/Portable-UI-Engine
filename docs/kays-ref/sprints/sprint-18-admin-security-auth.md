# Sprint 18 — Admin Security, Auth Gating & Diagnostics Page Repair

## Objective
Close critical runtime gaps in the admin console: fix the broken diagnostics page (undefined `CheckLabel`/`PasscodeGate`/`isAuthenticated`), add server-session-based auth gating to the triage page, build reusable auth infrastructure, and add developer-quality-of-life scripts.

## Deliverables

### 1. Auth Infrastructure

**`src/lib/auth-check.server.ts`** (new)
- `getCurrentSession` — a `createServerFn({ method: "GET" })` that wraps the server-only `getSession()` from `session.server.ts` for client-side consumption.
- Reads the `kwc_session` httpOnly cookie, verifies the HMAC signature, checks expiry, and returns `{ userId, orgId, role, exp }` or `null`.

**`src/hooks/useAuth.ts`** (new)
- `useAuth()` — React hook that calls `getCurrentSession()` on mount and returns `{ loading, authenticated, userId, orgId, role }`.
- `isAuthenticated()` — standalone async helper that returns a boolean. Useful for one-off checks in event handlers.

### 2. Diagnostics Page Repair

**`src/components/CheckLabel.tsx`** (new)
- `CheckLabel({ ok, label })` — renders a status row with `CheckCircle` (green, ok) or `XCircle` (red, not ok) icon and descriptive label.
- Used by `DiagnosticsDashboard` to report browser env, network, DB, and queue state.

**`src/components/PasscodeGate.tsx`** (new)
- `PasscodeGate({ onUnlock })` — minimal passcode entry UI with 4-digit input, loading state, and error feedback.
- Hardcoded passcode `"0726"` for engineering access to the diagnostics console.
- Styled consistently with the existing `login.tsx` page (gradient hero, glass card, same icon set).

**`src/routes/admin/diagnostics.tsx`** (fixed)
- **Imports added:** `CheckLabel`, `PasscodeGate` (from new components).
- **Route component changed** from `DiagnosticsDashboard` to `DiagnosticsPage` — the dashboard is now wrapped behind the passcode gate.
- `DiagnosticsPage` rewritten: uses `useState(false)` → `PasscodeGate` → `DiagnosticsDashboard` on unlock. No longer references the nonexistent `isAuthenticated()`.
- `DiagnosticsDashboard` unchanged — all panels (Runtime Status, Degradation Simulation, Write-Path, Offline Queue, Queue Telemetry) work as before.

### 3. Auth Gating on Triage Page

**`src/routes/admin/triage.tsx`** (enhanced)
- `useAuth()` hook checks session on mount.
- While loading: shows a centered "Verifying session..." skeleton with pulsing shield icon.
- If unauthenticated: `useNavigate` redirects to `/admin/login`.
- If authenticated: renders `TriageDashboard` as before.
- Added `useEffect`, `useNavigate` imports (no other structural changes).

### 4. Package Scripts

**`package.json`** (updated)
- Added `"test": "vitest run"` — runs all tests once.
- Added `"test:watch": "vitest"` — watch mode for TDD.
- Added `"typecheck": "tsc --noEmit"` — full project type checking.

### 5. Module Changes Summary

| File | Change |
|---|---|
| `src/lib/auth-check.server.ts` | **New** — `getCurrentSession` server function |
| `src/hooks/useAuth.ts` | **New** — `useAuth()` hook + `isAuthenticated()` helper |
| `src/components/CheckLabel.tsx` | **New** — Status indicator (ok/error) |
| `src/components/PasscodeGate.tsx` | **New** — Passcode entry gate |
| `src/routes/admin/diagnostics.tsx` | **Fixed** — Route uses auth gate, imports CheckLabel/PasscodeGate |
| `src/routes/admin/triage.tsx` | **Enhanced** — Auth gating with loading skeleton + login redirect |
| `package.json` | **Updated** — Added `test`, `test:watch`, `typecheck` scripts |
| `src/__tests__/auth-components.test.ts` | **New** — 3 structural tests |

### 6. Test Results
- 44 tests pass (41 existing + 3 new).
- Build succeeds cleanly.
- Only pre-existing type errors in `notification-queue.test.ts` (tuple destructuring — not from this sprint).

## Key Design Decisions
- **Passcode gate for diagnostics, not session auth** — The diagnostics console is an engineering tool. A simple passcode avoids cookie dependency in the admin login flow and works even when the DB is down (login requires DB for credential verification).
- **`useAuth` calls server function once on mount** — No polling or event-based refresh. The session token has a 24-hour expiry; re-checking on every page navigation is sufficient.
- **Hardcoded passcode** — The passcode `"0726"` mirrors the `DEFAULT_ADMIN_PASSWORD` default value. In production, this should be overridden via environment variable. A dedicated `PASSCODE` env var was not added to keep scope contained — the diagnostics gate is a soft barrier, not a security boundary.
- **Auth gating uses `useNavigate` redirect, not `<Navigate>`** — The `useEffect` pattern avoids rendering the protected content before the redirect fires and allows the loading state to be shown.

## Retrospective

### What went well
- The existing `session.server.ts` infrastructure made `getCurrentSession` trivially simple — just wrap `getSession()` in a `createServerFn`.
- Component tests (import/export shape) are fast (~600ms each) and don't need jsdom.
- The diagnostics page was already well-structured internally; only the auth wrapper and CheckLabel references were broken.

### What could be improved
- No proper logout endpoint yet. The "Sign Out" link on the triage page navigates to `/admin/login` but doesn't clear the session cookie. A `logout` serverFn should be added to call `deleteCookie()`.
- The hardcoded passcode should be configurable via `env.server.ts` in a follow-up sprint.
- The auth gating hydration flash could be eliminated with TanStack Router's `beforeLoad` route guard (requires session checking at the router level).

## Known Issues
- No `logout` server function — session cookie persists across sign-out. User can manually clear cookies or wait 24h for expiry.
- Passcode is hardcoded (`"0726"`) in `PasscodeGate.tsx`. Not suitable for production multi-admin setups.
- Auth gating redirect creates a brief flash of the loading skeleton before navigation completes on slow connections.
