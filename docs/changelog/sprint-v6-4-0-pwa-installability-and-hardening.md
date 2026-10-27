# Sprint Log: v6.4.0 — Installable PWA, Offline Verification, Growth Engine Rename

**Date:** 2026-09-05  
**Scope:** On-device installability fix (PNG manifest icons), production-build offline/installability
verification, "Brianna" removal from the growth engine, hardening audit + platform future-plan docs.

## Overview

The user reported the PWA "redirects to browser" when added on Android. Root cause: **SVG-only
manifest icons** (Android Chrome requires PNG for installability). Also executed the directive to
remove "Brianna" from the Growth Engine and to make Daftari verifiably anti-fragile online+offline.

## Added

- **`public/pwa-192x192.png`, `public/pwa-512x512.png`, `public/apple-touch-icon-180.png`**: real PNG
  icons derived from the brand SVG (8-bit) for Android Chrome installability + iOS home screen.
- **`e2e/pwa-prod.spec.ts` + `playwright.prod.config.ts`**: production-build verification (runs
  `vite preview` of the real `vite build`): PNG-manifest, SW registration/page-control, offline
  shell reload, offline sale persistence with `synced=0` that survives reload + sync failure.
- **`docs/offline-verified.md`**: evidence + the manual on-device checklist (human install step).
- **`docs/hardening.md`**: Daftari anti-fragility audit (proven-at-boundary vs needs-credentials).
- **`docs/platform-expansion.md` placeholder → ADR-011**: platform future plan (TWA/native/iOS
  desktop) gated by the pilot-readiness rule — documented, **not built**.
- **ADR-010**: installability decision + consequences + honest boundaries.

## Changed

- `vite.config.ts`: manifest icons → PNG (`192x192`, `512x512` + `maskable` 512); includeAssets
  updated.
- `index.html`: `<link rel="apple-touch-icon" href="/apple-touch-icon-180.png" />`.
- **Brianna removal**: `src/features/marketing/briannaContent.ts` →
  `src/features/marketing/growthContent.ts`, `BRIANNA_STORY_TEMPLATES` → `GROWTH_STORY_TEMPLATES`;
  UI labels in `GrowthShareScreen`, `SettingsScreen`, `AppShell` → "Growth Engine"; test updated to
  the new label (**not weakened** — the assertion still verifies the header renders). Sprint/history
  docs intentionally keep the v6.3.0 record.
- `package.json`: `test:e2e:prod` script; version → `6.4.0`.
- `.github/workflows/ci.yml`: `check` job now runs `npm run test:e2e:prod` after dev e2e.

## Verified

- local: `typecheck`, `lint`, `check:i18n`, unit suite — to be executed this sprint before push
  (gates below). CI runs build + dev e2e + prod e2e.

## Honest boundaries

- Remote sync upload needs real Supabase credentials (not in CI); the local no-silent-drop contract
  is proven. Real device-install is a human Chrome step — manual checklist provided.