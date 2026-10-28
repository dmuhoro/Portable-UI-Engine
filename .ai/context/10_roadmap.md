# Roadmap Brief

> Current execution state and layers for this pilot-hardening effort.

## Overarching Goal

Ship a pilot-ready productized clinic-ops platform to **Dr. Jackie (Kay's Wellness Centre)** —
one tenant, live, verified, safe to charge for. Engine = **kays-wellness-centre** (683 tests, the
finished engine). greenleaf-dental and dentalos-kenya are **donors only** (schema + UI ideas).

## Layer Status

| Layer | Work | Status |
|-------|------|--------|
| 0 | Governance folders (`.ai/`, `docs/adr|engineering|evidence|releases|runbooks`, CHANGELOG) | DONE (Sprint 35) |
| 1 | Decisions — ADRs 013–016 (STK push, D11 wiring, engine consolidation, deployment) | DONE (Sprint 35) |
| 2 | M-Pesa STK Push — schema + `api/mpesa.server.ts` + webhook route + tests | DONE (Sprint 35) |
| 3 | D11 PII encryption wiring — lead + STK push phone write/read paths + tests | DONE (Sprint 35) |
| 4 | Deployment prep — build verified, Supabase linked; live deploy owner-blocked | DONE (Sprint 35, partial) |
| 5 | TypeScript cleanup — 89 → 0 errors (`tsc --noEmit` exit 0) | DONE (Sprint 36) |
| 6 | Lovable parity — comparison, MCP harvest, editorial palette elevation | DONE (Sprint 36) |
| 7 | Docs/sprints/CHANGELOG update | IN PROGRESS (Sprint 36) |
| 8 | Push to GitHub, verify CI green | PENDING |

## Completion Criteria (Pilot-Ready)

1. All tests green (`npm test`, no errors) — **683/60 green**
2. M-Pesa STK Push: initiate → callback → payment + invoice auto-paid, idempotent — **DONE**
3. D11 wired: lead PII encrypted at rest, decrypt on read, key rotation intact — **DONE**
4. No TypeScript errors — **DONE (0)**
5. Deployed to Vercel + Supabase Postgres with real env — **BLOCKED on owner credentials**
6. WhatsApp delivery verified to +254703939236 — **BLOCKED on owner credentials**
7. M-Pesa STK live verification — **BLOCKED on owner credentials**
8. All commits SSH-signed, individual, pushed clean

## Remaining Blockers (owner-held credentials, deferred by owner)

Per owner directive, live verification is the **last chunk** of work. Steps in
`docs/runbooks/deployment.md`:
- Supabase DB password → `DATABASE_URL`
- Vercel login → deploy
- `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` → WhatsApp live verify
- Daraja sandbox creds → M-Pesa STK verify

## Non-Goals (deliberately descoped)

- Google review auto-submission (v2)
- WhatsApp inbound media automation (out of pilot day-1 scope)
- Greenleaf/dentalos UI porting (only schema donor for STK push; lovable is the UI reference)
- Multi-tenant onboarding for a third clinic (single-tenant pilot focus)