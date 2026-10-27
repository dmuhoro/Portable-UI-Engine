# 2026-08-25 — Deployment Verification

## Status: PARTIALLY COMPLETE — blocked on owner-held credentials

## Verified (with evidence)

| Item | Result | Evidence |
|------|--------|----------|
| Production build succeeds | **PASS** | `npm run build` → `BUILD_EXIT=0`, "✓ built in 56.31s", `[nitro] ✔ built`, `.vercel/output` generated |
| STK Push code bundled into serverless output | **PASS** | `STK_PUSH_INITIATED` event present in `.vercel/output/functions/__server.func/_ssr/index.mjs`; `mpesa_stk_push_requests` schema in `db.server-*.mjs` |
| M-Pesa webhook route compiles | **PASS** | `src/routes/api/webhooks/mpesa.ts` is file-based-routed by TanStack Start; build exited 0 with it present |
| Supabase project exists | **PASS** | `supabase projects list` → `kays-wellness-centre`, ref `yztalvyiixvlyxrlfnqn`, region `eu-west-1`, status `ACTIVE_HEALTHY`, PG 17.6 |
| Supabase link | **PASS** | `supabase link --project-ref yztalvyiixvlyxrlfnqn` → "Finished supabase link." |
| API keys retrievable | **PASS** | Management API returned anon + service_role keys |
| `.env*` and `.vercel` are gitignored | **PASS** | No secrets in repo |

## BLOCKED — requires owner-held credentials

| Item | Blocker | Action Needed |
|------|---------|---------------|
| Set `DATABASE_URL` in Vercel | DB password is set at project creation, not retrievable via API | Owner provides the Supabase DB connection string (`postgresql://postgres.<ref>:<pwd>@db.<ref>.supabase.co:5432/postgres`) |
| Deploy to Vercel | Vercel CLI is **logged out** | Owner runs `vercel login` (or provides token) |
| WhatsApp live verification to +254703939236 | `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` not provided | Owner adds WhatsApp Business Cloud API credentials; then run dispatch test |
| M-Pesa sandbox STK verification | `MPESA_CONSUMER_KEY/SECRET/SHORTCODE/PASSKEY/CALLBACK_SECRET` not provided | Owner adds Daraja sandbox credentials; set `MPESA_CALLBACK_URL` to the Vercel URL |

## Deployment Runbook

See `docs/runbooks/deployment.md` for the full step-by-step. Summary:
1. Owner provides `DATABASE_URL`, `SESSION_SECRET` (openssl rand -hex 32), `ENCRYPTION_KEY`, admin creds
2. Set Vercel env vars → push `main` → CI tests + Vercel build+deploy
3. Verify `/api/health` returns ok
4. Change default admin password
5. WhatsApp + M-Pesa live verification per runbooks

## Verdict

Code is deploy-ready and deploy-prep is complete up to the credential boundary. The remaining steps
are owner-executable in minutes once the 4 credential sets are provided.

---

## UPDATE 2026-08-26 — DEPLOYED + VERIFIED

The credential boundary was cleared today. All 12 Vercel env vars set (DATABASE_URL, SESSION_SECRET,
NODE_ENV, admin creds, M-Pesa sandbox vars), production deployed, and verified live:

- `/api/health` → `{"status":"healthy","dbAvailable":true,"queueStatus":"operational"}`.
- Org + admin seeded; login verified via the production `/_serverFn/*` RPC (200, set-cookie, admin).
- Vercel UI aligned with the Lovable deploy (holistic copy + light theme default).

Full record: `docs/sprints/sprint-38-production-golive-api-fixes-ui-parity.md`.