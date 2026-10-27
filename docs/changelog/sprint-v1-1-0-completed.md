# Sprint v1.1.0 — Language Restore, Dark Mode, Success Flash, Sync Dot, Streak, History Filters

**Date:** 2026-07-18  
**Version:** 1.1.0  
**Status:** Completed ✅

## Objective
Polish the app experience with dark mode, visual feedback on transactions, sync status indicators, engagement streak tracking, and history filtering. Fix the language toggle that was overwritten during the v1.0.0 build.

## Scope

### Dark Mode System
- 3 theme options: Light, Dark, System (follows OS preference)
- CSS custom properties for all surfaces (background, card, ink, muted, border)
- Instant switching via Zustand store, persisted across restarts
- `getResolvedTheme()` helper in App.tsx to compute effective theme from "system"
- `matchMedia` listener for live system preference changes

### Language Toggle Restore
- Chip-style toggle (SW | EN) in Settings screen
- Quick-toggle button on Dashboard header (SW/EN)
- Auth screen language selector
- i18n wiring verified: all components re-render on language change

### Transaction Success Flash
- Full-screen animated overlay after recording sale/expense/withdrawal
- Shows amount and type with 1.2s auto-dismiss
- `SuccessFlash.tsx` component with green income / red expense styling
- `handleQuickSale` in RecordSale and `handleSave` handlers trigger flash

### Sync Status Dot
- Real-time connectivity indicator on Dashboard header
- 4 states: green (synced), amber (pending), grey (idle), red (error)
- `useSync` hook with Dexie liveQuery + `navigator.onLine` + `supabase.channel` heartbeat
- Dot pulses during sync, shows tooltip on hover

### Recording Streak
- `useRecordingStreak` hook counts consecutive days with at least one transaction
- Orange Flame chip on Dashboard for 2–29 day streaks
- Gold milestone message at 30+ days
- Uses EAT (Africa/Nairobi) timezone

### History Filters
- Date filter tabs on HistoryScreen: This Week / This Month / All
- Transactions grouped by date with section headers
- Pull-to-refresh preserved
- Income/expense/withdrawal breakdown per day

### Onboarding Gate Fix
- App.tsx gate logic verified: `needsOnboarding` checks `business && !business.category`
- Null business (first launch) correctly routes to OnboardingScreen
- Loading state shows splash before Dexie read completes
- `handleOnboardingComplete` re-reads business from Dexie after creation

## Files Created
- `src/components/SuccessFlash.tsx`
- `src/hooks/useSync.ts`
- `src/hooks/useRecordingStreak.ts`

## Files Modified
- `src/App.tsx` — dark mode, onboarding gate, loading state
- `src/components/AppShell.tsx` — header structure
- `src/screens/DashboardScreen.tsx` — sync dot, streak, language toggle
- `src/screens/SettingsScreen.tsx` — language toggle, theme picker
- `src/screens/HistoryScreen.tsx` — date filters
- `src/features/transactions/RecordSale.tsx` — success flash
- `src/features/transactions/RecordExpense.tsx` — success flash
- `src/features/transactions/RecordWithdrawal.tsx` — success flash
- `src/features/transactions/RecordFulizaDebt.tsx` — success flash
- `src/features/transactions/RecordFulizaRepaid.tsx` — success flash
- `src/screens/AuthScreen.tsx` — language toggle
- `src/i18n/sw.json` — new strings
- `src/i18n/en.json` — new strings

## Acceptance Criteria
- [x] Dark mode: 3 options, instant switch, persisted
- [x] Language toggle: SW|EN in Settings, Dashboard, Auth
- [x] Success flash: animated overlay after every transaction
- [x] Sync dot: 4 states, real-time connectivity
- [x] Streak: consecutive days tracked, Flame chip at 2+, milestone at 30+
- [x] History filters: This Week / This Month / All
- [x] Onboarding gate: new users always see category flow
- [x] npm run typecheck — zero errors
- [x] npm run lint — zero errors
- [x] npm run test:run — all tests pass
- [x] npm run build — zero errors

## Next
Sprint v1.2.0 — Functional Profiles, Personalized Dashboard, Business Profile, P0 Bug Fixes
