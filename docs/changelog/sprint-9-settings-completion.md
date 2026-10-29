# Sprint 9 — Phase 5: Settings Completion + PWA Install Prompt + Repo Finalization

**Date:** Planned  
**Version:** 1.8.0  
**Status:** Pending ⏳

## Objective
Complete the Settings screen, add proper PWA install prompt behavior, and finalize the repository for production readiness.

## Scope

### Settings Completion
- Language toggle (sw/en) with immediate UI refresh
- Business profile editing: name, category, subcategory, payment methods
- Data management: export transactions (CSV), clear local data
- App version display (from package.json)
- About section with links to docs/adr/ and CHANGELOG
- Theme toggle (optional — light/dark if feasible)

### PWA Install Prompt
- Custom install banner (not browser default) in Kiswahili + English
- "Sakinisha Daftari" / "Install Daftari" prompt on landing page and after 3 transactions recorded
- Track install state: already installed, dismissed, deferred
- beforeinstallprompt event handling with user preference storage
- Install instructions for Android Chrome (step by step with screenshots)

### Repo Finalization
- README.md audit: accurate build instructions, environment variables, contributing guide
- ARCHITECTURE.md: verify accuracy, add ADR references
- ROADMAP.md: update with completed phases
- LICENSE file (MIT)
- Verify all CI checks pass on clean clone
- GitHub repo description and topics updated

### Performance Audit
- Bundle size analysis: check code splitting is effective
- Dexie query audit: verify all display queries use indexed fields
- Service worker cache audit: verify CacheFirst for app shell
- Lighthouse mobile audit: target >80 in all categories
- Fix any performance regressions introduced in Phase 1-4

## Files to Create
- `src/hooks/usePWAInstall.ts`
- `src/components/InstallBanner.tsx`
- `LICENSE`

## Files to Modify
- `src/screens/SettingsScreen.tsx` — complete all sections
- `src/App.tsx` — install prompt logic
- `README.md` — audit and update
- `ARCHITECTURE.md` — verify and update
- `ROADMAP.md` — mark completed phases
- `src/i18n/sw.json` — settings and install strings
- `src/i18n/en.json` — settings and install strings

## Acceptance Criteria
- [ ] Settings screen complete: language, business profile, data export, about
- [ ] PWA install prompt shows in Kiswahili (custom UI, not browser default)
- [ ] Install prompt dismissed remembered (not shown again)
- [ ] Install instructions available in Kiswahili + English
- [ ] CSV export of transactions works
- [ ] README.md accurate and complete
- [ ] ROADMAP.md updated
- [ ] LICENSE file present (MIT)
- [ ] Lighthouse mobile: >80 all categories
- [ ] Clean clone → npm ci → typecheck → lint → test → build passes
- [ ] npm run typecheck — zero errors
- [ ] npm run lint — zero errors
- [ ] npm run test:run — all tests pass

## Dependencies
- All previous phases complete

## Next
Future: SME Tier — inventory, multi-staff, reports, paid subscription
