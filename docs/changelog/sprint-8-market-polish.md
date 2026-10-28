# Sprint 8 — Phase 4: Market Polish

**Date:** Planned  
**Version:** 1.7.0  
**Status:** Pending ⏳

## Objective
Production-readiness polish: landing page, empty states, form validation hardening, mobile UX improvements, and accessibility audit. This sprint touches every screen but changes no business logic.

## Scope

### Landing Page
- Public landing page at `/` (unauthenticated)
- Value proposition in Kiswahili + English
- Feature highlights with icons
- Call-to-action: "Anza" / "Start" → Auth screen
- PWA install prompt from landing page
- Mobile-first design (360px-768px)

### Empty States
- Dashboard: "Rekodi muamala wako wa kwanza" / "Record your first transaction" with illustration
- History: "Hakuna miamala bado" / "No transactions yet" with CTA to Add screen
- Weekly chart: "Hakuna data ya wiki hii" / "No data for this week"
- Settings: sections without content get clean empty state (not broken layout)

### Form Validation Hardening
- All inputs validate on blur and on submit
- Amount: min 1, max 999,999 (from VALIDATION constants)
- Description: max 200 characters with character counter
- Business name: min 2, max 80 characters
- Remove any remaining `required` HTML attributes (use JS validation with custom messages)
- Validation messages in Kiswahili + English

### Mobile UX
- Add safe area insets for notch devices (pb-safe, pt-safe)
- Fix bottom nav spacing on devices with gesture nav bar
- Improve pull-to-refresh on History screen
- Add haptic feedback simulation for tap actions (CSS active state)
- Improve tap target sizes (ensure minimum 48×48px on all interactive elements)

### Accessibility Audit
- All interactive elements: aria-label present
- All form inputs: properly associated <label>
- Color contrast: WCAG AA 4.5:1 minimum verified
- Focus order: logical tab order through all screens
- Keyboard navigation: all actions reachable without touch
- Screen reader: test with TalkBack on Android

## Files to Create
- `src/screens/LandingScreen.tsx`
- `src/components/EmptyState.tsx`
- `src/components/ValidationMessage.tsx`

## Files to Modify
- `src/App.tsx` — add landing route
- `src/screens/DashboardScreen.tsx` — empty state
- `src/screens/HistoryScreen.tsx` — empty state, pull-to-refresh
- `src/screens/AddScreen.tsx` — validation
- `src/screens/AuthScreen.tsx` — validation
- `src/screens/SettingsScreen.tsx` — empty states
- `src/App.css` — safe area insets, tap highlight
- `src/i18n/sw.json` — empty state strings, validation messages
- `src/i18n/en.json` — empty state strings, validation messages

## Acceptance Criteria
- [ ] Landing page renders for unauthenticated users
- [ ] Empty states shown when no transactions exist
- [ ] All form validation works on blur and submit
- [ ] Validation messages in both Kiswahili and English
- [ ] Safe area insets applied to all screens
- [ ] WCAG AA contrast ratio on all text elements
- [ ] Keyboard navigable: all actions reachable via Tab/Enter
- [ ] aria-label on all icon-only buttons
- [ ] Works fully offline
- [ ] npm run typecheck — zero errors
- [ ] npm run lint — zero errors
- [ ] npm run test:run — all tests pass

## Dependencies
- All previous phases complete

## Next
Sprint 9: Phase 5 — Settings Completion + PWA Install Prompt + Repo Finalization
