# 2026-08-25 — Deployment: Supabase DB Connectivity Verification

## Status: BLOCKED — DB password rejected by Supabase pooler

## Verified (with evidence)

| Item | Result | Evidence |
|------|--------|----------|
| Vercel site live + current HEAD deployed | **PASS** | `kays-wellness-centre.vercel.app` serves palette `#fdfcf8`, `#d97c50`, `#e3ad4b` from CSS `styles-IZqLwRwr.css`; matches HEAD `d74175c` |
| Repo matches lovable editorial standard | **PASS** | Design tokens confirmed in deployed CSS (same as repo `src/styles.css`) |
| Supabase project healthy | **PASS** | `yztalvyiixvlyxrlfnqn`, region `eu-west-1`, status `ACTIVE_HEALTHY`, PG 17.6 |
| Pooler IPv4 reachable | **PASS** | `aws-0-eu-west-1.pooler.supabase.com` → `108.128.216.176`, TCP:6543 connects |
| **DB password `6035DG13971` authenticates** | **FAIL** | Pooler returns `(ENOTFOUND) tenant/user postgres.yztalvyiixvlyxrlfnqn not found` (PG `XX000`) for both `postgres.<ref>` and `postgres` usernames at ports 6543/5432 |

## Root Cause

The Supabase **pooler** rejects the tenant username with the provided password. The `XX000`/
`ENOTFOUND tenant/user` error from the pooler means **authentication failed** — the password
`6035DG13971` does not match the `postgres` role password configured for this project.

The direct host (`db.<ref>.supabase.co`) is **IPv6-only** (`2a05:d018:...`) and unreachable from
serverless/this environment, so the pooler is the required route.

## What I could not do

- Reset/verify the DB password: the `sbp_` management token lacks the DB-password endpoint scope
  (`/database-password` → 404/Cannot POST). CLI `db reset` also requires a working connection string.

## Required from owner

Confirm or reset the Supabase `postgres` DB password for project `yztalvyiixvlyxrlfnqn`:
1. Supabase Dashboard → project `kays-wellness-centre` → Settings → Database → **Reset database password**
2. Provide the confirmed password (or run `supabase db reset` / verify in the dashboard's
   "Connect" panel which shows the live connection string).

## Impact

- Blocks: `DATABASE_URL` env var, live `/api/health` → `{status:ok,db}`, schema auto-create
  (`ensureSchema`), admin login, and all DB-backed verification (WhatsApp/M-Pesa end-to-end).
- Does NOT block: Vercel automated deploys (already live), the build, or the codebase (all green).
- M-Pesa Daraja sandbox and WhatsApp Cloud API config can be prepared in Vercel env vars regardless
  (they don't require the DB to be configured), pending the DB password for end-to-end verification.

---

## UPDATE 2026-08-26 — RESOLVED

The blocker above was resolved today. The owner provided a new DB password, and the CLI's linked
project revealed the **correct pooler host**: `aws-1-eu-west-1.pooler.supabase.com` (note `aws-1`,
not the `aws-0` host used in the original test above). The new password authenticates against the
transaction pooler on port **6543**.

Working connection string:
`postgresql://postgres.yztalvyiixvlyxrlfnqn:<password>@aws-1-eu-west-1.pooler.supabase.com:6543/postgres`

Verified (see `docs/sprints/sprint-38-production-golive-api-fixes-ui-parity.md` for the full record):

- App's own `postgres` driver connects (PG 17.6) → `SELECT current_database() → postgres`.
- Live `/api/health` in production: `{"status":"healthy","dbAvailable":true,"queueStatus":"operational"}`.
- Schema created (28 tenant tables); org + admin seeded; login verified via the production RPC.