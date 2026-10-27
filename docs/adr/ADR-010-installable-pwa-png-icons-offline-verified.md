# ADR-010: Installable PWA — PNG manifest icons, offline-first verification

**Status:** Accepted  
**Date:** 2026-09-05  
**Supersedes/refines:** ADR-003 (PWA over React Native) — this is the correctness pass that makes
the existing decision actually *installable on-device*; it does not reverse it.

## Context

Users reported that tapping "Add to Home Screen" on Android Chrome opened the **browser**, not a
standalone app. Root cause (verified on the live site and in `vite.config.ts`): the web manifest
declared **SVG-only icons**. Android Chrome's installability criteria require **PNG** icons for
`192x192` and `512x512` (with a `maskable` purpose for the latter); with only SVG icons, `beforeinstallprompt`
never fires and Android silently falls back to a browser shortcut.

## Decision

1. **Ship real PNG icons** derived from the existing brand SVG: `pwa-192x192.png`, `pwa-512x512.png`
   (with a `maskable` variant of the 512), and an `apple-touch-icon-180.png` linked from `index.html`
   for iOS home-screen use.
2. **Verify the installed-mode + offline claims against the shipped production build**, not dev mode:
   a dedicated `playwright.prod.config.ts` runs a `vite build` + `vite preview` boundary — this is
   where the service worker actually registers, the manifest is actually served, and the app shell
   + IndexedDB are actually exercised offline.
3. **On-device behavior documented**, not assumed: a manual device checklist remains (PWA install is
   a Chrome user gesture; a headless CI cannot click "Install"). Native/TWA wrapper is deferred —
   see ADR-011.

## Consequences

**Positive**
- Android Chrome can now present Daftari as an installable, standalone PWA.
- Production-build e2e proves (a) manifest PNG compliance, (b) real SW registration + page control,
  (c) offline reload keeps the shell + local ledger intact, (d) an offline sale is persisted
  (`synced=0`) and never dropped, even when sync cannot reach the server.
- Drives toward the "works as an installed app, online and offline" state the owner asked for.

**Negative / honest**
- Install still requires a human gesture in Chrome ("Install app" / "Add to Home Screen"); a
  headless CI cannot complete that step — the manual device checklist is the remaining proof.
- True **background sync** (auto-upload after process kill) is still limited by PWA background sync
  support on some Android WebViews; the documented offline-first contract covers foreground
  reconnect sync ([ADR-001], sync queue with circuit breaker).
- Remote sync correctness against a real Supabase backend with real credentials is **not** provable
  in CI (no secrets); the local boundary (persist, retain on failure, never drop) is proven.

## Verification (evidence)

`docs/offline-verified.md` and `e2e/pwa-prod.spec.ts`; CI runs `npm run test:e2e:prod` on every push.