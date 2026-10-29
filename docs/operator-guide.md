# Daftari — Operator Guide

This guide is for the **operator** — the person who runs and maintains the deployed Daftari
instance once it is live. If you are a shop owner using the app, read `docs/user-guide.md`; if
you are extending the codebase, read `docs/programmer-guide.md`. This document is about
operating the system safely.

**Reference release:** `v6.7.0`. Follow the release sequence in `docs/deployment-runbook.md`.

---

## 1. What the operator owns

| Component | Provider | Operator responsibility |
|-----------|----------|--------------------------|
| Production bundle | Vercel | Deploys from `main` via CI hook |
| Auth + remote data | Supabase | Project, RLS policies, backups, key rotation |
| Offline store | user's device (IndexedDB) | Nothing — data lives client-side; keep subscribers honest about sync |
| Error telemetry | Sentry | Alerts, release association, triage |
| Push infrastructure | VAPID keys + Supabase | Key expiry, subscription churn |
| DataBank vault | tailnet-hosted service | URL/token here, not in this repo |

## 2. Deployment

- Push to `main` → CI runs all gates → `deploy` job fires `VERCEL_DEPLOY_HOOK`.
- Confirm the deploy by checking the Settings footer version in production.
- See `docs/deployment-runbook.md` §3–§5 for the exact stages and post-deploy checks.

### 2.1 Environment variables

**Daraja (M-PESA STK Push) — server-only, never VITE_*.** These power the
`stk-push` / `lipa-na-mpesa-callback` Supabase Edge Functions via `Deno.env` and are written
to the Supabase project's **Functions → Secrets** in the dashboard — NOT the Vercel env and
NOT `.env.local`. The app bundle never receives them (no `VITE_DARAJA_*`).

| Secret | Purpose | Value |
|--------|---------|-------|
| `DARAJA_ENV` | `sandbox` (fake money) or `production` (real money) | start `sandbox` |
| `DARAJA_CLIENT_KEY` | Daraja app consumer key (portal → Apps → your app) | portal value |
| `DARAJA_CLIENT_SECRET` | Daraja app consumer secret | portal value |
| `DARAJA_PASSKEY` | STK passkey (portal → Security Credentials → Lipa Na MPESA) | portal value |
| `DARAJA_SHORTCODE` | Business shortcode (paybill/buy-goods base) on Daraja | registered number |
| `DARAJA_STORE_NUMBER` | Store/till number (PartyB) that receives money | registered till |
| `DARAJA_CALLBACK_URL` | Public HTTPS — Safaricom posts the STK result callback | see below |

`DARAJA_CALLBACK_URL` **must be the fully-public edge URL** (no auth header — Safaricom doesn't
send one): `https://<project-ref>.supabase.co/functions/v1/lipa-na-mpesa-callback`.

**Sandbox drill before production** — run `§6.1` with a real sandbox phone to confirm PAID.


Required (Vercel): `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_SENTRY_DSN`,
`VITE_VAPID_PUBLIC_KEY`, optional `VITE_CANONICAL_DOMAIN`.

**Admin access is server-driven, not an env flag.** No `VITE_ADMIN_USER_ID`. Grant an owner the CEO
dashboard by inserting their auth UID via the Supabase SQL editor:
`insert into public.daftari_admin_users (user_id) values ('<owner-auth-uid>');`

**Check of record:** `src/lib/supabase.ts` exports `isSyncConfigured` — true **only when**
`VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are real values, not the `localhost:0`
fallback. After every deploy, open Settings and confirm the cloud-sync row reads "ready".
A green build with sync misconfigured is a silent production gap — do not accept it.

**Key rotation:** anon keys rotate in the Supabase dashboard → API keys. The deployed Vercel
env must carry the new key, then re-run the deploy hook. Never commit the key to the repo
(`docs/supabase-wiring.md` covers the wiring sequence).

## 3. Nightly / weekly operational checks

| When | Check | Where | Action if wrong |
|------|-------|-------|------------------|
| After each deploy | Version footer matches release | Settings | Re-check build + env; redeploy |
| After each deploy | Sync status "ready" | Settings on device | Add env vars, redeploy (see §2.1) |
| Weekly | Sentry error rate is stable, no new release > 48 h old | Sentry → Releases | Associate release tag; prioritize new errors |
| Weekly | Supabase error logs (RLS/401 spikes) | Supabase → Logs | Investigate before users do |
| Weekly | VAPID public key valid | `settings.addEventListener` in push flow | Rotate key, redeploy |
| Monthly | Supabase point-in-time backup integrity | Supabase → Backups | Test restore into a scratch project |
| Monthly | Verify the live-sync proof still exits 0 | `npm run verify:sync:live` | Exit 1 → not configured (gap); exit 2 → live failure |

## 4. Monitoring and alerting

- **Sentry**: production errors captured via `src/lib/sentry.ts` only in production builds.
  Set an alert on `error` events for release `v6.7.0`+.
- **Supabase**: watch Auth rate limits (password attempts, signup spam) and unhealthy RLS
  queries. `scripts/verify-sync-live.ts` is the only tooled end-to-end sync check.
- **Vercel**: function/bundle health and deploy success are surfaced in the Vercel dashboard
  and the GitHub Actions `deploy` job output.

## 5. Incident response

1. **Classify.** Data corruption or auth breach → severity 1. Feature outage → 2. Cosmetic → 3.
2. **Comms.** Tell users in the app language expectations: "sync is delayed", never "data is
   lost" until you have proven it.
3. **Contain.** Offline-first means users rarely lose data even if the cloud is down. Decide
   whether to disable sync writes (a flag) before a worst-case data migration.
4. **Fix.** Hotfix path in `docs/deployment-runbook.md` §7.
5. **Post-mortem.** Record the cause, the false-comfort that masked it (if any), and the gate
   that now catches it.

### 5.1 Recurring incidents and their playbooks

| Symptom | First diagnosis |
|---------|------------------|
| Sales exist on device but not in Supabase | Sync queue stalled or RLS rejecting upserts — check `daftari_sync_queue` counts and Supabase logs |
| "Not authorized" on admin screen for an admin | `store.role` is not persisted by design (fail-closed on every boot) — role is set per session; check `setRole` wiring |
| Pus/subscription churn | VAPID key rotated without redeploy, or expired subscriptions piling in `daftari_push_subscriptions` |
| Bundle regression (>300 KB warn) | CI warns on `dist/index.js`; review new imports in the PR |

## 6. Backup and restore

- **Server**: Supabase point-in-time backups + a monthly restore test into a scratch project.
- **On-device**: Settings → Data & Reports → **Export Backup** writes every table as one JSON
  file. Users should be coached to export periodically; the operator should not rely on this
  being done unprompted.
- **DataBank**: vault data is outside this repo — document its own backup somewhere in the
  DataBank repo and link it in the evidence log.

## 7. Handover checklist

Before another operator takes over:
- [ ] Production env vars documented in Vercel + this file §2.1
- [ ] Sentinel/Supabase/Vercel access list current
- [ ] Evidence log in `docs/deployment-runbook.md` filled for the current release
- [ ] Secrets live only in Vercel/Supabase; nothing in the repo
- [ ] `verify:sync:live` exits 0 from the operator's machine