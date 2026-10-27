# Sprint v1.3.0 — Codebase Ownership, CI/CD Pipeline, SMS Parser Hardening

**Date:** 2026-07-19  
**Version:** 1.3.0  
**Status:** Completed ✅

## Objective
Remove all Bolt.ai artifacts to take full ownership of the codebase, harden the SMS parser for production Kenyan phone numbers, establish a proper CI/CD pipeline with Vercel deploy, and set elite-level engineering standards.

## Scope

### Section A — Remove Bolt Fingerprints
- Deleted `.bolt/` directory (config.json + prompt history)
- Removed "Open in Bolt" badge from README.md
- Removed Bolt.new mention from ADR-003-pwa-over-react-native.md
- Rewrote README.md as a professional project readme

### Section B — SMS Parser Hardening
- Fixed phone number regex: `[A-Z0-9]{6,10}` → `\d{6,12}` to handle 12-digit Kenyan numbers (254 + 9 digits)
- Fixed `extractSenderPhone` to match digits only (`[A-Z0-9]` was matching names like "KARIUKI", "WANJIKU" as phone numbers)
- Expanded test coverage: 23 → 50 tests across 3 test files
- Added payment method detection to all SMS patterns (Airtel Money, Till, Paybill, Pochi, send money)
- Added timestamp parsing for standard M-Pesa received messages

### Section C — CI/CD Pipeline
- Renamed workflow: `CI` → `CI/CD`
- Added `deploy` job that triggers Vercel deploy hook after Quality Gate passes on main
- Bumped CI node version: 20 → 22 (lockfile compatibility)
- Fixed lockfile: regenerated with esbuild 0.28.1 properly marked as optional
- Set up GitHub secrets: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VERCEL_DEPLOY_HOOK`

### Section D — Engineering Standards
- Created `.nvmrc` (Node 22)
- Created `AGENTS.md` with project conventions
- Updated `CONTRIBUTING.md` as personal engineering standards
- Fixed 2 lint warnings in `HistoryScreen.tsx` (useCallback + ref capture)
- Achieved 0 lint warnings across the entire codebase

### Section E — User Profile in Settings
- Added user profile card in Settings Account section showing authenticated user email
- Displayed account creation date and last sign-in time with relative date formatting
- Fetched user metadata from `supabase.auth.getUser()` on mount
- Added 3 new i18n keys to both sw.json and en.json (`user_profile`, `account_created`, `last_sign_in`)

## Files Created
- `.nvmrc`
- `AGENTS.md`
- `docs/changelog/sprint-v1-3-0-completed.md`

## Files Modified
- `README.md` — professional rewrite, removed Bolt badge
- `docs/adr/ADR-003-pwa-over-react-native.md` — removed Bolt.new mention
- `CONTRIBUTING.md` — rewritten as personal engineering standards
- `.github/workflows/ci.yml` — CI/CD with deploy job, node 22
- `package-lock.json` — regenerated with optional esbuild deps
- `src/features/sms/parseMpesa.ts` — phone regex hardening
- `src/features/sms/parseMpesa.test.ts` — expanded to 50 tests
- `src/screens/HistoryScreen.tsx` — fixed lint warnings
- `src/screens/SettingsScreen.tsx` — user profile card with email, account creation, last sign-in
- `src/i18n/sw.json` — 3 new keys (user_profile, account_created, last_sign_in)
- `src/i18n/en.json` — 3 new keys (user_profile, account_created, last_sign_in)

## Acceptance Criteria
- [x] `.bolt/` directory deleted
- [x] README.md: no Bolt badge, professional content
- [x] ADR-003: no Bolt.new mention
- [x] `.nvmrc` exists with Node 22
- [x] `AGENTS.md` exists with project conventions
- [x] SMS parser handles 12-digit Kenyan phone numbers
- [x] SMS parser doesn't match names as phone numbers
- [x] 50 tests pass across 3 test files
- [x] CI/CD pipeline: typecheck → lint → test → build → deploy
- [x] User profile card shows email, account creation, last sign-in in Settings
- [x] 3 new i18n keys in both languages
- [x] 0 lint warnings
- [x] 0 typecheck errors
- [x] Vercel deploy hook triggers successfully
- [x] Git: committed and pushed
- [x] Vercel: redeployed successfully

## Dependencies
- Sprint v1.2.0 completed

## Next
- WhatsApp Business API integration
- Multi-channel sales tracking
- Inventory management
- Customer 360 view
