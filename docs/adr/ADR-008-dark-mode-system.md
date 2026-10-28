# ADR-008: Dark Mode with Tailwind CSS darkMode: 'class'

Status: Accepted
Date: 2026-07-18

## Context
Daftari users operate in varying light conditions — outdoor market stalls
in direct sunlight (needs high contrast light mode) and indoor evening use
(dark mode reduces eye strain, saves battery on OLED screens common in
budget Android phones).

## Decision
Implement dark mode using Tailwind CSS darkMode: 'class' strategy.
Theme preference stored in Zustand (persisted), applied via
document.documentElement.classList by a useEffect in App.tsx.
Three options: light, dark, system.

## Consequences
Positive:
- System option follows OS preference — zero friction for users who already
  set their phone to dark mode
- Class-based approach enables runtime switching without page reload
- All dark: variants are compile-time — no runtime CSS parsing cost

Negative:
- Every component needs dark: class variants added — one-time cost
- Flash of unstyled content (FOUC) on first load before JS applies dark class
  Mitigation: inline script in index.html reads localStorage before React mounts
