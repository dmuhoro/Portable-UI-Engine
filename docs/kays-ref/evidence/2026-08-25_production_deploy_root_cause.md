# 2026-08-25 — Production Deploy Root-Cause: Missing Env Vars + Webhook Routing

## Status: ROUTE FIX DEPLOYED — remaining blocker is Vercel env vars (owner action)

### UPDATE 2026-08-25 (post-fix)

The webhook/API route registration was fixed and deployed (commit `1541b08`):
- Moved the 6 h3 handlers from `src/routes/api/` to `server/routes/api/**`
  (Nitro `serverDir` scan location) + `vite.config.ts` `nitro.serverDir`.
- Live behavior changed from **404** (routes unreachable) to **500** (routes hit,
  but env vars missing): `/api/webhooks/mpesa` → 500, `/api/webhooks/whatsapp` → 500,
  `/api/health` → 500, all returning `{"error":true,"status":500,"unhandled":true}`.
- This is the expected env-guard crash: `getEnv()` throws `Environment validation
  failed` because `DATABASE_URL` is not set in Vercel.

### Required from owner (Vercel Environment Variables — Production)

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Supabase connection string (see below) |
| `SESSION_SECRET` | strong random 64-char (`openssl rand -hex 32`) |
| `DEFAULT_ADMIN_EMAIL` | e.g. admin@kayswellnesscentre.org |
| `DEFAULT_ADMIN_PASSWORD` | strong temp (change after first login) |
| `WHATSAPP_TOKEN` | WhatsApp Cloud API token (user to provide) |
| `WHATSAPP_PHONE_NUMBER_ID` | number ID for +254703939236 |
| `MPESA_CONSUMER_KEY` | rb3ZYBvJaV6Q4RB9IqpaFbsGm39Mk8HMbkqnyXwCzqz0Aj61 |
| `MPESA_CONSUMER_SECRET` | H32kD88BPuvqvhgka5BL0Uekx4mgARiLG18B1ynCmGcEOk7wNOX7lFG8tFzZOywF |
| `MPESA_SHORTCODE` | 174379 (sandbox test paybill) |
| `MPESA_PASSKEY` | bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919 (sandbox) |
| `MPESA_CALLBACK_URL` | https://kays-wellness-centre.vercel.app/api/webhooks/mpesa |
| `MPESA_CALLBACK_SECRET` | generate a random string |

### DATABASE_URL — password verification

The password `6035DG13971` was **rejected by the Supabase pooler** during testing
(`ENOTFOUND tenant/user postgres.yztalvyiixvlyxrlfnqn not found` = auth failure). The direct host is
IPv6-only and unreachable from serverless. Two options:
1. Owner confirms/resets the postgres password in Supabase Dashboard (Settings → Database →
   Reset database password), then provides it.
2. Owner pastes the exact `DATABASE_URL` shown in the Supabase "Connect" panel.

The connection string format:
`postgresql://postgres.yztalvyiixvlyxrlfnqn:<password>@aws-0-eu-west-1.pooler.supabase.com:6543/postgres`

### After env vars are set

- `/api/health` returns `{status:"ok",db:true}` (schema auto-creates via ensureSchema).
- Admin login works → lead → WhatsApp confirmation (bilingual) → booking → invoice → M-Pesa STK.
- WhatsApp + M-Pesa webhooks reachable at `/api/webhooks/{whatsapp,mpesa}` (routes now registered).

## Critical Finding

The deployed site (`kays-wellness-centre.vercel.app`) renders static pages correctly (SSR works)
but **every server-function call and API route fails**:

| Test | Result |
|------|--------|
| Homepage `/` | **200** — SSR content present ("Executive-Grade Medicine", "Precision healthcare") |
| `/admin/login` | **200** — client page loads |
| `/_serverFn/login` (RPC) | **500** — "This page didn't load" |
| `/_serverFn/anything` | **500** |
| `/api/health` | **404/500** |
| `/api/webhooks/whatsapp` | **404** |
| `/api/webhooks/mpesa` | **404** |

## Root Cause (confirmed from the deployed bundle)

The built server bundle (`_ssr/index.mjs`) begins with `getEnv()` which Zod-validates env vars.
`DATABASE_URL` is required and must be a **valid URL** (`.url()`). On Vercel:

- **`DATABASE_URL` is NOT set** → any server function triggers `getEnv()` → throws
  `Environment validation failed` → the SSR error wrapper renders "This page didn't load" → 500.
- Static pages don't call `getEnv()` → they render fine.

Additionally, the Nitro/Vercel route table registers **only a single catch-all `/**` → ssr-renderer**.
The TanStack Start handler inside does not register the raw h3 webhook files
(`src/routes/api/webhooks/whatsapp.ts`, `mpesa.ts`) as routes — they were never reachable in
production. Server functions use `/_serverFn/<id>` (confirmed in the client bundle) but that path
crashes due to env validation before dispatch.

## What is NOT the cause

- The M-Pesa sandbox credentials: **VALID** (obtained access token
  `qlMPPflQ7NFnkvXPnOA0GCO9QGb9`; STK push init succeeded, ResponseCode 0).
- The code itself: 683 tests green, tsc 0 errors, build passes.
- The design/UI: deployed palette matches lovable (confirmed).

## Required from owner (Vercel Environment Variables)

Set in Vercel project settings → Environment Variables (Production):

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Supabase connection string (see below) |
| `SESSION_SECRET` | strong random 64-char (`openssl rand -hex 32`) |
| `DEFAULT_ADMIN_EMAIL` | e.g. admin@kayswellnesscentre.org |
| `DEFAULT_ADMIN_PASSWORD` | strong temp (change after first login) |
| `WHATSAPP_TOKEN` | WhatsApp Cloud API token (user to provide) |
| `WHATSAPP_PHONE_NUMBER_ID` | number ID for +254703939236 |
| `MPESA_CONSUMER_KEY` | rb3ZYBvJaV6Q4RB9IqpaFbsGm39Mk8HMbkqnyXwCzqz0Aj61 |
| `MPESA_CONSUMER_SECRET` | H32kD88BPuvqvhgka5BL0Uekx4mgARiLG18B1ynCmGcEOk7wNOX7lFG8tFzZOywF |
| `MPESA_SHORTCODE` | 174379 (sandbox test paybill) |
| `MPESA_PASSKEY` | bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919 (sandbox) |
| `MPESA_CALLBACK_URL` | https://kays-wellness-centre.vercel.app/api/webhooks/mpesa |
| `MPESA_CALLBACK_SECRET` | generate a random string |

## DATABASE_URL — password verification

The password `6035DG13971` was **rejected by the Supabase pooler** during testing
(`ENOTFOUND tenant/user postgres.yztalvyiixvlyxrlfnqn not found` = auth failure). The direct host is
IPv6-only and unreachable from serverless. Two options:
1. Owner confirms/resets the postgres password in Supabase Dashboard (Settings → Database →
   Reset database password), then provides it.
2. Owner pastes the exact `DATABASE_URL` shown in the Supabase "Connect" panel.

The connection string format:
`postgresql://postgres.yztalvyiixvlyxrlfnqn:<password>@aws-0-eu-west-1.pooler.supabase.com:6543/postgres`

## After env vars are set

- `/api/health` returns `{status:"ok",db:true}` (schema auto-creates via ensureSchema).
- Admin login works → lead → WhatsApp confirmation (bilingual) → booking → invoice → M-Pesa STK.
- WhatsApp + M-Pesa webhooks need the webhook-route registration fix (the h3 route files under
  `src/routes/api/webhooks/` are not served by TanStack Start's router; must be moved/registered
  as Nitro server routes or the deploy must use the node-server preset). This is the next
  code-layer task once env is confirmed.

---

## UPDATE 2026-08-26 — ALL BLOCKERS RESOLVED

Both blockers were resolved today. Env vars were set, and two additional production-only bugs were
found and fixed (see `docs/sprints/sprint-38-production-golive-api-fixes-ui-parity.md`):

1. **"Invalid lazy handler" 500 on every `/api/*` route** — Nitro 3 beta's Vercel web-format lazy
   handler resolves only a module's default export; the route files exported named `GET`/`POST` only.
   Fixed with default method-dispatch exports on all 6 route handlers.
2. **"Cannot find package 'postgres'"** — the obfuscated dynamic import in `db.server.ts` hid the
   specifier from the server bundler, leaving the driver externalized. Fixed with a literal
   `import("postgres")` + client-env rollup external.
3. **`/api/health` passive flag** — now actively pings the DB via `pingDb()`.

Live result: `/api/health` → healthy, all API routes functional, org+admin seeded, login verified.