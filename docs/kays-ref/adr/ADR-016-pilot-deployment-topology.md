# ADR-016 — Pilot Deployment Topology

**Status:** Accepted
**Date:** 2026-08-25
**Applies to:** kays-wellness-centre deployment

---

## Context

The product must be deployed and verified live for a Dr. Jackie pilot. Current state: no live
Postgres wired, no production env configured, Vercel app exists but is outdated relative to the repo.

Available infrastructure:
- Supabase (access token provided by product owner) — can host the Postgres `DATABASE_URL`.
- Vercel — existing app `https://kays-wellness-centre.vercel.app/`.
- WhatsApp Business number +254703939236 (test target).
- App refuses to boot with default `SESSION_SECRET` in production (env guard).

## Decision

1. **Database:** Supabase Postgres. Use the Supabase project's connection string as `DATABASE_URL`.
   Schema is auto-created by `ensureSchema()` on first boot — no external migration runner required
   (D2: DDL lives in `db.server.ts`).
2. **App hosting:** Vercel (existing). Env vars set in Vercel dashboard / CLI:
   `DATABASE_URL`, `SESSION_SECRET` (strong, generated), `ENCRYPTION_KEY`(derived; used as
   per-org key material seed), `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD` (changed after first
   login), WhatsApp + M-Pesa vars per ADR-014.
3. **WhatsApp:** outbound Cloud API from `dispatch.server.ts`; verify delivery to +254703939236.
4. **M-Pesa:** STK Push in sandbox first (Daraja sandbox base URL), callback URL must be a public
   HTTPS endpoint on the Vercel app.
5. **Evidence:** each live verification writes an evidence file under `docs/evidence/`.

## Consequences

- One live URL serves Dr. Jackie's tenant; multi-tenancy unchanged.
- Env secrets live only in Vercel/Supabase; `.env.local` in repo contains no real secrets.
- Deployment verification unblocks release-readiness #39, #47.

## Alternatives Rejected

- **Self-hosted Postgres** — operational overhead for a pilot; Supabase already available.
- **No WhatsApp verification** — the visible pilot "wow" feature must be proven live before selling.
- **Delaying deployment until full hardening** — contradicts the fast-path-to-pilot strategy.