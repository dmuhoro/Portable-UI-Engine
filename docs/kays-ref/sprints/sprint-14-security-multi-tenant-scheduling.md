# Sprint 14 — Security, Multi-Tenant Auth & Deterministic Scheduling

## Objective
Move the codebase from single-tenant to a closed-pilot multi-tenant SaaS framework with cookie-based auth, deterministic scheduling, testing, and structured observability.

## Deliverables

### 1. Multi-Tenant Schema & Org Isolation
- **`src/lib/db.server.ts`** — `ensureSchema(multiTenant)` creates `organizations`, `users`, `clinic_availability` tables; adds `organization_id` + `appointment_timestamp` columns + partial unique index to `clinic_leads`.
- **`src/lib/session.server.ts`** — `getSession`, `getCurrentOrgId`, `getCurrentUserId`, `getCurrentUserRole` use `getCookie` from TanStack Start.
- All server functions in `leads.server.ts`, `scheduling.server.ts` call `getCurrentOrgId()` and filter/insert by `orgId`.

### 2. Cookie-Based Auth
- **`src/lib/auth.server.ts`** — HMAC SHA-256 signed tokens (`signToken`/`verifyToken` with `crypto.timingSafeEqual`), PBKDF2 SHA-512 password hashing (100k iterations), `login` server fn, session cookie `kwc_session`.
- **`src/routes/admin/login.tsx`** — Proper login form with email/password, error state, loading spinner, navigation to triage.
- **`src/routes/admin/triage.tsx`** — Replaced passcode gate with session-based flow.
- **`src/routes/admin/diagnostics.tsx`** — Removed passcode gate.

### 3. Deterministic Scheduling
- **`src/lib/api/scheduling.server.ts`** — `generateSlots` (pure, flat while-loop, UTC-based), `getAvailableSlots`, `getAvailabilityRange` with `clinic_availability` table.
- `generateSlots` exported as pure function for unit testing.

### 4. Structured Observability
- **`src/lib/logger.server.ts`** — Structured JSON logger with `createLogger({ request_id, tenant_id })`, `child()`, `info/warn/error/debug`, production JSON → stdout, dev human-readable.

### 5. Default Org Seeding
- `seedDefaultOrgAndAdmin()` creates default `Kay's Wellness Centre` org + admin user (`DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` env vars, defaults: `admin@kayswellnesscentre.org` / `admin0726`) + Mon–Sat clinic availability (08:00–17:00 weekdays, 08:00–13:00 Saturday, 60-min slots).

### 6. Testing Infrastructure
- **`vitest.config.ts`** — TZ=UTC, Node environment, path alias `@/` → `./src/`, setup file with localStorage mock.
- **`src/__tests__/offline-queue.test.ts`** (8 tests) — Payload resilience: empty storage, single/multiple packets, corrupted JSON, nested payloads, mutation isolation.
- **`src/__tests__/slot-generation.test.ts`** (9 tests) — Boundary times (last slot ends at close), timezone handling (UTC day), empty/missing availability, booked exclusion, Saturday hours.
- **`src/__tests__/submit-lead.test.ts`** (9 tests) — Validation rollback guarantee on Zod schema: empty name, invalid email/priority/datetime, minimal payload, whitespace name, max-length fields.

All 26 tests pass.

## Key Design Decisions

- **`session.server.ts`** uses `getCookie` from `@tanstack/react-start/server` (not `getRequestEvent`) to avoid SSR build resolution issues with virtual module exports. The final file is **not** imported by any client route component — only by other `.server.ts` modules.
- **`postgres`** dynamically imported via string concatenation (`["p","o","s","t","g","r","e","s"].join("")`) to prevent Rollup from bundling Node.js-specific modules (`perf_hooks`, `crypto`, `net`, `tls`, `stream`, `fs`) into the client build.
- Server functions (`createServerFn`) handle `getRequestEvent` correctly inside their `.handler()` bodies. Standalone server-only utilities must use the real API exports (`getCookie`, `setCookie`) instead.
- The TanStack Start import-protection plugin blocks `@tanstack/react-start/server` in any file that reaches the client build. Splitting server-only logic into files not imported by route components ensures build passes.

## Build Results
- `npm run build` succeeds (client + SSR + Nitro/Vercel layers).
- Deprecation warnings: `createServerFn().inputValidator()` → should migrate to `.validator()` in a future sprint.

## Retrospective
### What went well
- Multi-tenant schema migration via `ensureSchema()` is idempotent and backward-compatible.
- Pure `generateSlots` function made unit testing straightforward.
- Zod schema validation decoupled from DB logic enables easy integration tests.

### What could be improved
- Migrate all `.inputValidator()` calls to `.validator()` to remove deprecation warnings.
- Add integration tests with a real/test DB container (e.g., `testcontainers` + PostgreSQL).
- Move TanStack Start server-only utilities to `@tanstack/start-server-core` real exports instead of relying on virtual module resolution.

### Known Issues
- `use client` directive warnings in Nitro build (TanStack Router / React Query / Sonner) — cosmetic, no runtime impact.
- Deprecation warnings for `inputValidator` — non-breaking, should be updated next sprint.
