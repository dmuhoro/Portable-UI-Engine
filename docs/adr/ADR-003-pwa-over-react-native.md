# ADR-003: PWA over React Native

**Status:** Accepted  
**Date:** 2026-06-07

## Context
Daftari needs to run on Hellen's budget Android phone without requiring
an app store download.

## Decision
Build a Progressive Web App (PWA) using Vite + React.

## Consequences
**Positive:**
- Instant deployment — share a URL, no app store review
- Works on any Android Chrome without installation (then installable)
- Single codebase — no iOS/Android split
- Standard web tooling supports it natively (Vite, Workbox)

**Negative:**
- No native push notifications (Notification API has limitations on Android)
- No background sync (service worker limitations on some Android WebViews)
- Older Android WebViews (< Android 7) may have Dexie compatibility issues

## Future consideration
React Native migration when the product requires deep native integrations
(camera for receipt scanning, NFC for tap payments).
