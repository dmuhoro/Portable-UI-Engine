# Sprint 4 — Phase 0: Auth Fix + Error Boundaries

**Date:** Planned  
**Version:** 1.3.0  
**Status:** Pending ⏳

## Objective
Fix critical authentication issues and add error boundaries to prevent silent failures. This is the blocking prerequisite for all future phases.

## Scope
- Fix supabase.auth.getUser() null handling in store.ts
- Wrap transaction write in try/catch with proper error state
- Add React error boundary at App shell level
- Add loading/error states for auth flow (email not confirmed, wrong password, network error)
- Ensure auth errors display user-friendly Kiswahili/English messages (not raw Supabase errors)
- Verify RLS policies prevent cross-user data access
- Add `ErrorBoundary.tsx` component

## Files to Create
- `src/components/ErrorBoundary.tsx`
- `src/components/AuthErrorDisplay.tsx`

## Files to Modify
- `src/lib/store.ts` — add error handling for addTransaction
- `src/screens/AuthScreen.tsx` — better error display
- `src/i18n/sw.json` — auth error keys
- `src/i18n/en.json` — auth error keys

## Acceptance Criteria
- [ ] Sign in with wrong password shows "Nenosiri si sahihi" not raw Supabase error
- [ ] Sign in with unconfirmed email shows "Barua pepe haijathibitishwa" not raw error
- [ ] Network error during sign in shows "Huna mtandao" fallback
- [ ] Transaction write failure shows error message (not silent fail)
- [ ] React error boundary catches render crashes and shows recovery UI
- [ ] Working offline: auth state persists from Dexie/localStorage
- [ ] npm run typecheck — zero errors
- [ ] npm run lint — zero errors
- [ ] npm run test:run — all tests pass

## Dependencies
- None — all existing dependencies sufficient

## Next
Sprint 5: Phase 1 — Business Category System + Onboarding Redesign
