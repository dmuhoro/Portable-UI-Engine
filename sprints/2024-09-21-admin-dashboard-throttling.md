# 2024-09-21 – Admin Dashboard & Sync Throttling

## Added
- Restored original telemetry analytics module with `track`, `flush` and full `EVENTS` enum (23 keys).
- Moved revenue‑related aggregation helpers to `src/lib/analyticsMetrics.ts`.
- Updated `AdminScreen` to import from the new metrics module.
- Fixed stray brace in `OnboardingScreen` causing a syntax error.
- Implemented `debounceWrite` unit test (`src/lib/throttleWrite.test.ts`).
- Implemented `AdminScreen` unit test (`src/screens/AdminScreen.test.tsx`).
- Updated `CHANGELOG.md` with new entries.
- Added sprint documentation `sprints/2024-09-21-admin-dashboard-throttling.md`.
