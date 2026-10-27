# Evidence Brief

> How evidence is recorded and what already exists.

## Location

`docs/evidence/` — dated `.md` or `.log` files. Convention:
`YYYY-MM-DD_<topic>.md` containing: date, command/step, observed result, verdict.

## Evidence Required This Sprint

| Item | Evidence file |
|------|---------------|
| STK Push unit tests pass | Cited in test results (document in sprint note) |
| D11 encryption wiring tests pass | `encryption.test.ts` + new lead-encryption tests |
| Full suite green | `docs/evidence/YYYY-MM-DD_full_test_suite.md` |
| WhatsApp live delivery to +254703939236 | `docs/evidence/YYYY-MM-DD_whatsapp_live_delivery.md` |
| M-Pesa STK live/sandbox verification | `docs/evidence/YYYY-MM-DD_mpesa_stk_verification.md` |
| Deployment (Vercel + Supabase) | `docs/evidence/YYYY-MM-DD_deployment.md` |

## Recording Rule

A PASS row requires a cited test or a cited manual verification step — never narrative alone
(Constitution Article VII).