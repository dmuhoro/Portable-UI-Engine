# Runbook: Production Deployment

> How to deploy the kays-wellness-centre engine to Vercel with Supabase Postgres.

## Prerequisites

- Vercel project (existing: `kays-wellness-centre` → https://kays-wellness-centre.vercel.app/)
- Supabase project with a Postgres connection string
- SSH-signed git config (AGENTS.md rule 10)

## 1. Provision Supabase Postgres

1. Create a Supabase project (or use the one tied to the provided access token).
2. Copy the **transaction** connection string: `postgresql://postgres.<ref>:<password>@aws-...pooler.supabase.com:6543/postgres`.
3. Keep it as `DATABASE_URL`. The schema auto-creates via `ensureSchema()` on first boot.

## 2. Set Vercel Environment Variables

Set in Vercel project settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Supabase transaction connection string |
| `SESSION_SECRET` | 64-char random (generate: `openssl rand -hex 32`) |
| `ENCRYPTION_KEY` | 64-char random |
| `DEFAULT_ADMIN_EMAIL` | e.g. admin@kayswellness.co.ke |
| `DEFAULT_ADMIN_PASSWORD` | strong temp password (change after first login) |
| `NODE_ENV` | `production` |
| `WHATSAPP_TOKEN` | WhatsApp Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Business phone number ID |
| `MPESA_BASE_URL` | `https://sandbox.safaricom.co.ke` (sandbox) |
| `MPESA_CONSUMER_KEY` | Daraja app credentials |
| `MPESA_CONSUMER_SECRET` | Daraja app credentials |
| `MPESA_SHORTCODE` | `174379` (sandbox test paybill) |
| `MPESA_PASSKEY` | sandbox passkey `bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919` |
| `MPESA_CALLBACK_URL` | `https://kays-wellness-centre.vercel.app/api/webhooks/mpesa` |
| `MPESA_CALLBACK_SECRET` | random string shared with Safaricom test tool |

> **Verified 2026-08-25:** The provided Daraja sandbox consumer key/secret successfully obtained an
> access token and initiated an STK push (ResponseCode 0) against `sandbox.safaricom.co.ke`. The
> sandbox shortcode `174379` + standard sandbox passkey are confirmed working.

## 3. Deploy

Push to `main` → CI runs tests, Vercel builds + deploys. Verify:
- `/api/health` returns `{ status: "ok", uptime, db }`
- Admin login works with seeded admin
- Change default password immediately

## 4. Verify

- Run `npm test` (667+ green)
- `npm run typecheck`, `npm run lint`
- WhatsApp test to +254703939236
- M-Pesa STK sandbox push → callback

## Rollback

- Vercel: redeploy previous deployment via dashboard.
- DB: schema is additive (`IF NOT EXISTS`); no destructive migration in normal path.