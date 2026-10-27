# Daftari — Deployment Runbook

This runbook is the permanent sequence for shipping a Daftari release. Follow it top-to-bottom;
do not skip the verification steps.

**Reference:** latest release `v6.7.0`.

---

## 1. Release checklist

Before tagging a release, all of these must pass locally:

```bash
npm ci
npm run typecheck     # strict TypeScript — 0 errors
npm run lint          # ESLint — 0 errors, 0 warnings
npx tsx scripts/check-i18n.ts   # sw/en key parity
npm run test:run      # unit + component suite
npm run build         # production bundle
```

Do not publish a tag if any command fails.

## 2. Versioning

- `package.json` `"version"` and `src/lib/constants.ts` → `APP.VERSION` **must match**. Sentry
  releases and the Settings footer derive from `APP.VERSION`; the deployed bundle is identified
  in release tracking from `package.json`.
- Bump on a dedicated commit, then tag the same commit.

```bash
npm version 6.7.0 --no-git-tag-version
# update APP.VERSION in src/lib/constants.ts to match
npm i   # refresh package-lock
git add package.json package-lock.json src/lib/constants.ts CHANGELOG.md
git commit -m "chore: bump version to 6.7.0"
git tag v6.7.0
```

## 3. CI / CD

`.github/workflows/ci.yml` runs on every push or PR to `main`:

| Stage | Command | Gate |
|-------|---------|------|
| Typecheck | `npm run typecheck` | blocks merge |
| Lint | `npm run lint` | blocks merge |
| i18n parity | `npx tsx scripts/check-i18n.ts` | blocks merge |
| Unit/component | `npm run test:run` | blocks merge |
| Bundler | `npm run build` | blocks merge |
| Bundle budget | size of `dist/index.js` | warns > 300 KB |
| E2E (dev mode) | `npm run test:e2e` | blocks merge |
| E2E (production build) | `npm run test:e2e:prod` | blocks merge |

On a push to `main`, after `check` passes, the `deploy` job fires the Vercel deploy hook
(`secrets.VERCEL_DEPLOY_HOOK`). Health-check the deployment against the production URL after
triggering.

## 4. Environment variables (Vercel)

The following are required in production (see `docs/supabase-wiring.md` for the full wiring
sequence and how to verify the real Supabase client ships in the bundle):

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SENTRY_DSN`
- `VITE_VAPID_PUBLIC_KEY`
- `VITE_CANONICAL_DOMAIN` (defaults to the Vercel domain)

Admin access is **not** an env var: grant the CEO dashboard server-side via
`insert into public.daftari_admin_users (user_id) values ('<owner-auth-uid>');`

**Never** commit real values; use Vercel's environment UI or CLI.

## 5. Post-deploy verification

1. Confirm the deployed bundle's version footer matches (`Settings → … → Daftari vX.Y.Z`).
2. Run the live sync check against the deployed environment (requires valid cloud credentials):

   ```bash
   npm run verify:sync:live
   ```
   - exit `0` → cloud sync proven end-to-end
   - exit `1` → sync not configured (production gap — fix env and redeploy)
   - exit `2` → live failure — investigate before telling users it works
3. Open the app on a phone: sign up, record a sale, close the day, go offline and reload.

## 6. Rollback

Vercel keeps previous deployments. To roll back:

1. Open the Vercel project → Deployments.
2. Select the last known-good deployment labeled with a prior tag.
3. Use **Promote to Production** (or re-trigger the prior git ref if the deploy hook is used).

Rollback restores the previous build as-is — it does not undo cloud data changes.

## 7. Hotfix (patch) path

1. Branch of `main` → fix → open PR (CI gates run).
2. Merge to `main` → CI → deploy hook fires.
3. Bump patch version and tag (`v6.7.1`, …) once verified on production.

---

## Evidence log

| Release | Typecheck | Lint | i18n | Tests | Build | Deployed |
|---------|-----------|------|------|-------|-------|----------|
| v6.7.0  | ✅ | ✅ | ✅ | 415 ✅ | ✅ | pending hook |

Record the row for every future release; leave it blank if a gate was skipped.