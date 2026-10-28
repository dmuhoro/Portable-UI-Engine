# Daftari platform expansion — future plans (not built)

The owner asked which devices Daftari should target (desktop/laptop browser, Android, iOS) and to
record it as *future plans inside Daftari*. This page is that record. **Decision rule (ROADMAP):
Pilot Validation gate first** — 10 vendors, 30 consecutive days of daily use each. Nothing here is
built before that gate.

## Today (already real)

Daftari is a **browser PWA on every platform**: Android (Chrome), iOS (Safari), desktop/laptop
(any modern browser). One codebase, offline-first core (IndexedDB + sync queue → Supabase on
reconnect), same URL. v6.4.0 made it genuinely *installable* (PNG manifest icons) and *proved*
offline behavior at the production-build boundary (`docs/offline-verified.md`).

## The "platform" meaning (honest)

"Running online and offline" is delivered by the **data contract**, not by any single app shell:
`local_id`-consistent upserts, `synced` flag, circuit-broken retry queue, no-silent-drop
repository layer. Any future surface (TWA, native, desktop shell) plugs into that same contract.

| Surface | Details | Trigger (evidence, not guess) |
|---|---|---|
| Android TWA (Play store) | installable badge via WebView shell around the PWA | pilot gate cleared + vendors hit install-store friction |
| Native Android (Kotlin) | deep OS integration: NFC tap-pay, reliable background sync | TWA proves insufficient |
| iOS installed PWA | install via Share → Add to Home Screen; assets shipped (v6.4.0) | manual iPhone verification + SW eviction handling |
| Desktop shell (Electron/Tauri) | desktop workflows from the same core | real desktop segment appears in pilot data |
| Eco-system seams (Forge) | expose `ai-context/` + task seams read-only to Forge | Forge step-1 exit criterion met |

Full analysis with consequences: `docs/adr/ADR-011-daftari-platforms-future-plan.md`.