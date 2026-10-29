# Offline-first verification evidence (2026-09-05, production build)

Answers: **"Does Daftari really run offline, as an installed app?"** — at the *shipped-prod* boundary.

## Root cause fixed

Live manifest + `vite.config.ts` had **SVG-only icons**. Android Chrome requires **PNG** icons
(192 + 512, `maskable` on 512) for installability → the "Add to Home Screen" produced a browser
shortcut. Fixed in v6.4.0: real PNGs derived from the brand SVG, `apple-touch-icon` added, the dev
SW-test documented in ADR-010.

## The proof (production build, `vite build` + `vite preview`)

Run: `npm run build && npm run test:e2e:prod` — suite also wired into CI (`.github/workflows/ci.yml`,
`npm run test:e2e:prod`).

| Claim | Assertion in `e2e/pwa-prod.spec.ts` | Result |
|---|---|---|
| Manifest installable | every icon `image/png`; sizes include `192x192` + `512x512`; `maskable` 512 present; `display: standalone`; `start_url: /` | PASS |
| iOS home-screen icon | `link[rel=apple-touch-icon]` → reachable `.png` (HTTP 200) | PASS |
| SW real in prod | `navigator.serviceWorker.getRegistration()` + `controller` active | PASS |
| Offline shell survives | full offline reload keeps shell + IndexedDB ledger + offline banner | PASS |
| Offline sale persisted, never dropped | offline record lands with `synced=0`, survives reload & sync failure | PASS |
| Automated gates | `typecheck`, `lint`, `check:i18n`, `test:run`, `npm run build`, dev e2e — all part of CI `check` job | runs on every push |

## Manual device checklist (human step headless CI cannot fake)

1. Open https://daftari-olive.vercel.app (or the live domain) in **Android Chrome**.
2. Chrome menu → **Install app** (or Add to Home Screen). The icon must be the D-brand **PNG**, and
   the app must open **standalone** (no URL bar).
3. Turn on Airplane mode → open Daftari from the launcher → record a sale offline → home-screen
   note: offline banner + value present after restart. Reconnect → sync queue drains it.
4. iOS: Safari → Share → **Add to Home Screen**; verify `apple-touch-icon` shows and standalone.
5. Record `docs/evidence/<date>_device.md` with the phone model + observed result (Constitution
   Article VII — narrative alone is not evidence).

## Honest boundaries

- Remote **upload** to Supabase is not proven in CI (no secrets/tenant there). The local contract
  (persist → retry → keep, never drop) is proven; real uploads need the device checklist above or a
  staging tenant.
- Chromium's install prompt cannot be clicked headlessly — the "installed" verdict is the human
  checklist, not a green CI box.