# ADR-011: Daftari platforms — expand only when the pilot gate is clear

**Status:** Accepted (a *future plan*, not a build)  
**Date:** 2026-09-05

## Context

The owner asked what makes Daftari "a platform running online and offline", and whether to build
for desktop/laptop browsers, Android, and iOS. Decision rule set by ROADMAP.md: **Pilot Validation
gate (10 vendors, 30 consecutive days each) comes first** — "nothing moves to the next phase until
this gate is cleared."

## Decision

- Keep the **on-device, offline-first PWA** as the current pillar; the ecosystem keeps running it on
  Android Chrome (installed) and any browser, today, online + offline (IndexedDB → sync on reconnect).
- Do **not** build native/TWA/desktop apps now. Record the options and their trigger points.
- Software is a sequence: each platform is a separate capability with its own cost; adding them
  before real pilot demand is a pre-scale gamble the roadmap explicitly forbids.

## Options (future expansion, gated)

| Platform | What it means | Trigger (gate) |
|---|---|---|
| Android **TWA** (Trusted Web Activity) | Wraps the installed PWA in a WebView shell → Play Store presence, badge, install from store | Pilot gate cleared AND vendors hit the install-store barrier (evidence, not guess) |
| Android native | Kotlin port of ledger+offline core (reuses ADR-006 Dexie? no — sqlite/room, new sync layer) | TWA insufficient: needs NFC tap-pay, background sync, deep OS integration |
| iOS PWA | Same URL; manifest + apple-touch-icon (delivered in v6.4.0); iOS install via Share → Add to Home Screen | Manual device verification + deal with iOS-specific SW storage eviction rules |
| Desktop (macOS/Windows/Linux) | Same PWA via browser; optional Electron/Tauri shell for offline-first desktop workflows | Real desktop-using segment appears in pilot data |
| **Orchestrator / Forge ecosystem** | Daftari exposes `ai-context/` corpus + task seams to the eco-system (Forge pilot repo) | Forge step-1 exit met, then read-only context extraction |

## What "platform running online + offline" means today (honest)

Daftari is already a platform in the functional sense: the **local-first core** (repository →
IndexedDB → sync queue → Supabase on reconnect) runs identically offline and online, single codebase,
on any device with a browser. The **"platform" boundary is its data contract** (local_id-consistent
upserts, `synced` flag, circuit-broken queue, no-silent-drop) — that contract is what new surfaces
(installed app, desktop shell, TWA) would plug into without rearchitecting.

## Consequences

- v6.4.0 delivers the PWA gap (installability + offline verification) now; the rest waits.
- Manifest PNG icons + apple-touch-icon make every future surface cheap (reused assets).