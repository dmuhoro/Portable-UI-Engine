# Sprint 15 — Multi-Tenant Isolation, Edge Telemetry & Friday Pilot Hardening

## Objective
Harden the multi-tenant SaaS build for pilot-readiness: enforce tenant isolation at every data access point, add structured event-driven telemetry with PII redaction, and validate environment configuration on bootstrap.

## Deliverables

### 1. Strict Tenant Isolation
- **`src/lib/tenant.server.ts`** — `requireOrg()` middleware that:
  - Creates a `requestId` (crypto.randomUUID, first 8 chars)
  - Calls `getCurrentOrgId()` and throws `TenantError` if null
  - Returns `{ orgId, requestId, log }` (logger pre-seeded with `tenant_id` and `request_id`)
- Every server function in `leads.server.ts`, `scheduling.server.ts`, `diagnostics.server.ts` now calls `requireOrg()` before touching the database.
- `submitLeadViaWebhook` now enforces tenant context before forwarding payloads.

### 2. Production Telemetry & Structured Logging
- **`EVENTS`** constant map in `logger.server.ts` covering all 15 operational event types:
  `AUTH_SUCCESS`, `AUTH_FAILURE`, `LEAD_CREATED`, `LEAD_FETCHED`, `LEAD_UPDATED`, `LEAD_DELETED`, `SLOTS_GENERATED`, `SLOT_BOOKED`, `SLOT_UNAVAILABLE`, `QUEUE_SYNC_SUCCESS`, `QUEUE_SYNC_FAILURE`, `DB_UNAVAILABLE`, `TENANT_MISSING`, `SCHEMA_SETUP`, `ENV_VALIDATION`.
- **PII redaction**: `redact()` function strips `email`, `password`, `phone`, `name`, `raw_payload` keys from all log entries before writing.
- **Structured JSON** in production (stdout), human-readable with `[LEVEL] [EVENT] [req:xxx] [org:xxx]` prefix in development.
- All server function handlers log with `event` property for filtering and dashboards.

### 3. Live Deployment Validation
- **`src/lib/env.server.ts`** — Zod-validated environment configuration:
  - `DATABASE_URL` (required URL)
  - `SESSION_SECRET` (min 32 chars, default dev-only)
  - `DEFAULT_ADMIN_EMAIL`/`DEFAULT_ADMIN_PASSWORD` (with safe defaults)
  - `NODE_ENV` (enum: development/production/test)
  - Warns on boot if using default SESSION_SECRET in production.
- Bootstrap throws immediately with descriptive error listing missing vars.
- `getDb()` now delegates to `requireDatabaseUrl()` for centralized URL validation.

### 4. Module Changes Summary

| File | Change |
|---|---|
| `src/lib/env.server.ts` | **New** — Typed env validation with Zod, singleton cache |
| `src/lib/tenant.server.ts` | **New** — `requireOrg()` middleware, `TenantError` class |
| `src/lib/logger.server.ts` | **Upgraded** — `EVENTS` constants, PII redaction, standardized metadata |
| `src/lib/db.server.ts` | **Upgraded** — Use `requireDatabaseUrl()`, structured event logging |
| `src/lib/session.server.ts` | **Upgraded** — Use `getSessionSecret()` from env module |
| `src/lib/auth.server.ts` | **Upgraded** — Use `getDefaultAdminEmail/Password()`, structured event logging with `EVENTS` |
| `src/lib/api/leads.server.ts` | **Upgraded** — `requireOrg()` middleware, structured event logging, slot collision events |
| `src/lib/api/scheduling.server.ts` | **Upgraded** — `requireOrg()` middleware, structured event logging |
| `src/lib/api/diagnostics.server.ts` | **Upgraded** — Structured event logging |

### 5. Test Results
- All 26 existing tests pass unchanged.
- Build succeeds cleanly (client + SSR + Nitro/Vercel).

## Key Design Decisions
- **`requireOrg()` throws, doesn't return null** — Server functions catch at the handler level, producing a clean early-return with `TENANT_MISSING` event. This avoids silent data leaks from missing tenant context.
- **PII redaction happens at write time**, not at call site — every log entry is scrubbed regardless of whether the developer remembered to redact. The `redact` function recursively walks nested objects.
- **Env validation is lazy** — `getEnv()` is called on first access, not at module import time, avoiding boot failures during client-side module resolution where `process.env` may not be fully available.
- **Event constants are plain string literals** (not enum symbols) — serializable to JSON without custom serializers, queryable in observability backends.

## Retrospective
### What went well
- Middleware pattern (`requireOrg`) made the audit trivial — every existing server function was refactored with a one-line change.
- Zod schema for env vars catches misconfiguration at first request, not at crash time.
- Event constants create a queryable taxonomy for log aggregation (Datadog, Grafana Loki, etc.).

### What could be improved
- Migrate `.inputValidator()` to `.validator()` across all server functions (deprecation warnings remain).
- Add a DB-level `SET session.organization_id` on each connection to enable PostgreSQL RLS when the database supports it.
- Consider extracting `EVENTS` into a shared TypeScript enum for cross-service consumption.

## Known Issues
- `use client` directive warnings in Nitro build (TanStack Router / React Query / Sonner) — cosmetic.
- `crypto.pbkdf2Sync` is a Node.js API — works in Vercel Node.js runtime but would need migration to Web Crypto `subtle.timingSafeEqual` for edge runtime compatibility.
