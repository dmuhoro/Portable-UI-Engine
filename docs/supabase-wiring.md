# Supabase sync — wiring, migrations, and live verification

This is the "make offline→Supabase real" runbook. The sync **code** (offline→IndexedDB→upsert on
`local_id`→mark `synced`, RLS-scoped pull while online) is complete and unit-tested. What was
missing is machine truth: the **deployed build was compiled WITHOUT the Supabase project env**, so
production served a `createClient('http://localhost:0', …)` no-op and sync silently never reached a
real column. This runbook makes that gap impossible to repeat.

## 1. The only required inputs (client-safe; the Postgres URL is NOT needed)

- `VITE_SUPABASE_URL` — the project URL `https://<ref>.supabase.co` (anon/public, safe to ship).
- `VITE_SUPABASE_ANON_KEY` — the anon/public key (safe to ship; protected by RLS on the server).
- The app never sees the Postgres connection string or the service-role key.

## 2. Where each value lives

| Secret | GitHub (used? build≠Vercel) | Vercel (the REAL build env) | Local dev |
|--------|----------------------------|------------------------------|-----------|
| `VITE_SUPABASE_URL` | set on `dmuhoro/Daftari` | **MISSING — this is the gap** | `.env` / `.env.local` |
| `VITE_SUPABASE_ANON_KEY` | set on `dmuhoro/Daftari` | **MISSING — this is the gap** | `.env` / `.env.local` |

The GH secrets exist but the **Vercel build** is the one that compiles the production bundle, and
Vercel's env list for the `dmuhor01/daftari` project is **empty**. That is exactly why `dist`
contained `local-dev-only` / `localhost:0`.

## 3. Migrations (verified applied on live)

All sync tables exist and are RLS-enforced on the live project
(`daftari_transactions/businesses/customers/daily_closes/suppliers/purchase_orders/stock_adjustments/analytics`),
including `daftari_push_subscriptions`.

Verified 2026-09-05 via read-only REST probes (anon key):
- every table above returns HTTP 200 for `select` of its own columns;
- `daftari_push_subscriptions` exposes `id,user_id,subscription,created_at` (the migration's shape);
- anon `INSERT` on `daftari_push_subscriptions` and `daftari_transactions` is refused:
  `"new row violates row-level security policy"` — the `user_id = auth.uid()` policies
  (owner_only_*) are live and fail-closed.

So no pending schema migration. If a schema drift is ever suspected, re-run with a logged-in CLI
(`supabase db push` applies everything under `supabase/migrations/`, all idempotent `IF NOT EXISTS`).
The one pending action is a **realtime publication** change (2026-09-05):

### 3.1 Enable realtime for multi-device live updates

`useRealtimeSync` (shipped `69bf17a`) subscribes to `postgres_changes` on
`daftari_transactions` and `daftari_businesses`. A subscription will report
`SUBSCRIBED` even when a table is **not** in the `supabase_realtime` publication —
but then **no events are delivered**. RLS still scopes the stream; enabling the
publication only turns on the WAL feed and does NOT weaken tenant isolation.

Apply ONE of:

- **Dashboard → Database → Replication** (`/project/rjedivbpldkroffswoyb/database/replication`):
  tick **supabase_realtime** for both tables.
- **SQL editor** — `supabase/migrations/20260905210000_enable_realtime_tables.sql`:
  ```sql
  alter publication supabase_realtime add table public.daftari_transactions;
  alter publication supabase_realtime add table public.daftari_businesses;
  ```
  (idempotent; safe to re-run.)

Verify after applying (browser on prod, signed in): record a sale on the phone, watch
the browser dashboard update in-place without a reload. That in-place delivery is the
B1 exit test.

Enable in the Dashboard (project `rjedivbpldkroffswoyb`):
- Go to **Authentication → Sign In / Providers** (`/project/rjedivbpldkroffswoyb/auth/providers`).
- The **Email** provider is enabled by default. Set **Confirm email** to ON under the Email
  provider card (this is the production posture; the app now handles `session === null`
  gracefully with a check-your-inbox state and resend).
- **Authentication → URL Configuration**: set **Site URL** to `https://daftari-amber.vercel.app`
  and add that origin to **Redirect URLs**. Supabase sends the confirmation redirect there
  with `#access_token=...`; the SPA client (implicit flow) picks the session up on load.
- Note: the default Supabase SMTP is a **dev-only 2 emails/hour** limit (this is the
  `email rate limit exceeded` error `verify:sync:live` hit). For real user signups, configure
  a custom SMTP (Resend/SendGrid/Postmark) under Project Settings → Auth → SMTP before
  inviting beta users.

## 4. Live verification (no browser)

```bash
# optional: activate your local env that holds a real project pair
set -a; . ./.env; set +a

VITE_VERIFY=true npm run verify:sync:live
```

This script uses the app's **own anon bearer path** and, with `VITE_VERIFY=true`, performs a
write→read→delete round-trip against `daftari_transactions`:
- **exit 0** → full round-trip proven on a real project.
- **exit 1** → env not configured (the build is NOT wired).
- **exit 2** → a live network/RLS failure (details printed).

> Note: anon signup can be rate-limited ("email rate limit exceeded"). That is a dashboard limit on
> throwaway signups, not a fault in the app path — wait for the window to clear and re-run once.

## 5. Rebuild and ship so the bundle carries the real client

1. Add both values to **Vercel** for the `dmuhor01/daftari` project (Production), not GitHub —
   Vercel is the compiler:
   ```bash
   cd <linked daftari clone>
   vercel env add VITE_SUPABASE_URL production --type config
   vercel env add VITE_SUPABASE_ANON_KEY production --type config
   ```
2. Push `main` → Vercel redeploys with the real client baked in.
3. Re-verify the deployed bundle:
   ```bash
   curl -s https://daftari-amber.vercel.app/ | grep -o '/assets/index-[^"]*\.js' \
     | while read a; do curl -s "https://daftari-amber.vercel.app$a" | grep -c "supabase.co"; done
   ```
4. `node scripts/verify-sync-live.ts` exit 0 on the live bundle.

> **Status (2026-09-05):** the Production env on `dmuhor01/daftari` **is now set** for both
> `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`, and a redeploy from the corrected source verified
> the live bundle embeds `https://rjedivbpldkroffswoyb.supabase.co` with **zero** `localhost:0`
> fallback. The deployed manifest is PNG (`standalone`, 192/512/maskable), not the stale SVG variant.

## 6. Client guard (in code)

`src/lib/supabase.ts` exports `isSyncConfigured` (true only when both env vars are real). The
Settings screen surfaces it ("Cloud sync is ready on this build" / "not configured") so a
misconfigured build is **visible**, not silent — no more LOCALHOST-FALLBACK-masks-real-sync.
