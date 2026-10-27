# Release Readiness Brief

> Condensed from `docs/release-readiness.md`. The literal go/no-go for the pilot.

## Go/No-Go Status (Sprint 34 baseline)

- **PASS:** 667 tests / 58 files; build succeeds; **tsc clean (0 errors as of Sprint 36)**;
  tenant isolation (22 adversarial); RBAC gates; billing locks; scheduling injection; notification
  queue; rate limits; reconciliation (19 tests); encryption (8 tests); webhooks (16 tests);
  subscriptions (37 tests); metering (15 tests); marketing pipeline; CI exists; Docker build fixed.

## UNVERIFIED Blockers (manual verification required)

| # | Blocker | Severity |
|---|---------|----------|
| 39 | WhatsApp delivery in production | MEDIUM — needs `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` |
| 47 | Real M-Pesa transaction reconciled in staging | MEDIUM — needs real M-Pesa CSV export |
| 56 | SSE delivers to browser real-time | LOW |
| 60 | Paywall blocks feature access in UI | LOW |

## Descoped For Pilot

- **PII encryption** (D11) — being wired THIS sprint
- **Google review auto-submission** — sentiment ships, no GBP API
- **M-Pesa STK Push** — was "not built" — being ADDED this sprint from greenleaf donor

## Pre-Pilot Checklist (run before going live to Dr. Jackie)

1. `SESSION_SECRET` set in Vercel env (app refuses boot with default)
2. `DEFAULT_ADMIN_PASSWORD` changed after first login
3. Docker build succeeds
4. Real M-Pesa CSV upload works in staging
5. WhatsApp delivery verified with real number (+254703939236)
6. SSE live-updates verified
7. Subscription paywall verified for starter tier

## This Sprint's Target

Move items 39, 47 (via STK push + CSV), and D11 from UNVERIFIED/DESCOPED to PASS-with-evidence.
Document each in `docs/evidence/`.