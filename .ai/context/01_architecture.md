# Architecture Brief

> Condensed from `docs/architecture.md`. For full detail read the canonical file.

## Stack

- **Framework:** TanStack Start + TanStack Router (`@tanstack/react-start` v1.131.0+)
- **Runtime:** Vite + Nitro (preset `vercel`)
- **Database:** PostgreSQL via `postgres` v3.4.x (raw `db.unsafe(sql, params)` — no ORM)
- **Validation:** Zod (shared client/server schemas)
- **State:** TanStack Query + Router stores + URL search params
- **Hosting:** Vercel (`vercel.json` — security headers + immutable asset caching)

## Request Lifecycle

```
Browser → __root.tsx layout → TanStack Router route match
  → client component calls createServerFn()
  → TanStack Start server handler
  → createServerFn handler (src/lib/**/*.server.ts)
  → requireOrg() reads kwc_session JWT → { orgId, requestId, log }
  → getDb() → db.unsafe(sql, params)
  → JSON response → TanStack Query cache
```

**Key pattern:** every `createServerFn` handler independently calls `requireOrg()` and must bind
`orgId` in every SQL query. No global middleware auto-scopes. This is D7.

## Server File Map

| Area | Files |
|------|-------|
| Core infra | `db.server.ts`, `env.server.ts`, `config.server.ts`, `logger.server.ts` |
| Auth/tenant | `auth.server.ts`, `auth-check.server.ts`, `session.server.ts`, `tenant.server.ts`, `permissions.server.ts` |
| Subscriptions | `subscriptions.server.ts`, `metering.server.ts`, `trials.server.ts`, `checkout.server.ts` |
| Messaging/queue | `messaging.server.ts`, `queue.server.ts`, `fallback.server.ts`, `api/dispatch.server.ts` |
| Integrations | `encryption.server.ts`, `webhooks.server.ts`, `event-bus.server.ts`, `audit.server.ts`, `storage.server.ts` |
| Marketing | `marketing/leads.server.ts`, `marketing/automation.server.ts`, `marketing/reviews.server.ts` |
| API layer | `api/leads.server.ts`, `api/billing.server.ts`, `api/scheduling.server.ts`, `api/resources.server.ts`, `api/analytics.server.ts`, `api/clinic-config.server.ts`, `api/dispatch.server.ts`, `api/registration.server.ts`, `api/reconciliation.server.ts` |
| Money | `reconciliation.server.ts` (CSV), `api/billing.server.ts` (invoice/payment), `checkout.server.ts` (subscription checkout) |
| Webhooks | `routes/api/webhooks/whatsapp.ts` (WhatsApp), `routes/api/webhooks/` (M-Pesa — new) |
| SSE | `routes/api/streams/live-updates.ts` |

## Build & Deploy

- Build: `npm run build` (Vite + `@lovable.dev/vite-tanstack-config`)
- Tests: `npm test` (vitest)
- CI: `.github/workflows/ci.yml` (tests), `.github/workflows/deploy.yml` (lint+build)
- Docker: `Dockerfile` with `NITRO_PRESET=node-server`; `docker-compose.yml` for local PG

## Known Gaps (from architecture.md §9)

| Gap | Severity |
|-----|----------|
| `config.server.ts` bypasses Zod validation | Low |
| No CSRF protection on createServerFn POST | Low |
| `processQueue()` default runs unscoped (role-gated callers) | Low |
| No idempotency on `registerOrganization` | Low |