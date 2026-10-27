# Sprint 6: Install Hardening + Sync Wiring Seam

**Status:** In-progress (code changes complete; release + live Vercel env wiring pending)  
**Version Target:** v6.5.0  
**Focus:** Make "open as an app, never in the browser" a guarantee, not an accident. Expose the
real sync state so a misconfigured build is visible, not silent.

---

## Sprint Objectives

1. **Persistent install banner**: A global top-bar CTA on non-installed mobile browsers — shows an
   install button (Android/Chrome) or Share→Add to Home Screen instructions (iOS Safari), with a
   one-tap dismiss. Hidden immediately once running in `display-mode: standalone` or
   `navigator.standalone === true`.
2. **Dead-button guarantee**: After any prompt outcome (accepted or dismissed), the deferred prompt
   is consumed AND the button is removed — no silent no-ops.
3. **Sync state surface**: Export `isSyncConfigured` from `src/lib/supabase.ts` (true only when both
   `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` point at a real project, NOT the
   `localhost:0` fallback). Settings shows a clear colored dot + "Cloud sync is ready on this build"
   or "not configured". A misconfigured build is now visible.
4. **Live-sync verification script** (`scripts/verify-sync-live.ts`): proves the real network path
   (upsert + RLS read + delete) without a browser. Three exit codes: 0 (pass), 1 (not configured,
   the production gap), 2 (live failure). Rate-limited signups are surfaced as errors, not silently
   swallowed.
5. **Release wiring runbook** (`docs/supabase-wiring.md`): the exact sequence to add the two env
   values to Vercel (the actual production compiler), push main, and verify the deployed bundle
   carries the real client. Makes the prior LOCALHOST-FALLBACK-masks-real-sync gap impossible to
   repeat.

---

## Key Files Created / Modified

* `src/components/InstallBanner.tsx` — global install CTA component (reads `usePWAInstall` + `isAlreadyInstalled`/`isIOS` heuristics).
* `src/components/InstallBanner.test.tsx` — 7 jsdom tests: install CTA visible, hidden when installed, runs install, dismisses, no CTA before prompt, iOS guidance, dismiss iOS.
* `src/hooks/usePWAInstall.ts` — patched: after any prompt outcome, clear `canInstall` immediately (no dead button).
* `src/components/AppShell.tsx` — `<InstallBanner />` rendered global top-bar below `<OfflineBanner />`.
* `src/lib/supabase.ts` — new `isSyncConfigured` export; used in SettingsScreen.
* `src/screens/SettingsScreen.tsx` — sync-status row with colored dot + bilingual label based on `isSyncConfigured`.
* `scripts/verify-sync-live.ts` — network round-trip proof (insert + RLS read + delete) against the real anon bearer path.
* `package.json` — `verify:sync:live` script; version → `6.5.0`.
* `docs/supabase-wiring.md` — the permanent wiring + migration + env + release runbook.
* `sprints/sprint_6_install_hardening_and_sync_wiring.md` — this file.
* `CHANGELOG.md` — [Unreleased] / [6.5.0] entry.

---

## Validation & Verification Checklist

- [x] `npm run typecheck` — clean
- [x] `npm run lint` — 0 errors
- [x] `npm run test:run` — 376 passed (7 new: InstallBanner.test)
- [x] `npm run build` — successful
- [x] `npx tsc --noEmit -p tsconfig.node.json` — clean (verify-sync-live.ts compiles)
- [ ] `npm run verify:sync:live` — hits real Supabase rate limiter (transient anon email limit);
      reached the network path (proof = rate limiter response, not LOCALHOST-FALLBACK)
- [ ] Live Vercel deploy with real env baked in (the literal "wiring the gap")
- [ ] Re-run `curl ... | grep "supabase.co"` on live assets to confirm the real client is shipped

---

## Honest Boundaries (this sprint)

- The **install banner does not create the app shortcut** — that's a Chrome/iOS gesture on the
  phone. It makes the gesture impossible to miss.
- **Live sync proof end-to-end** requires one transient input from the user (adding two env vars
  to Vercel, or handing us the Vercel env). The hard work (RLS + sync code + migrations) is real
  and server-live; the bundle just wasn't compiled with the key. The runbook closes that gap
  permanently.
- The rate-limited email signup ("email rate limit exceeded") is a Supabase free-tier guard,
  not an app bug; the verify script surfaces it honestly (exit 2) instead of mislabeling it.
