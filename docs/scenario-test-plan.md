# Daftari — Real-World Scenario Test Plan

**Version:** 1.0 · **Phase B deliverable** · **Gate before marketing spend**

Execute each scenario on **localhost** (`npm run dev`) and **staging** (Vercel preview + Supabase staging).
Mark **PASS** only when all criteria are met. Any **FAIL** blocks broad launch.

**Legend:** 🔴 P0 (launch blocker) · 🟡 P1 (fix before scale) · 🟢 P2 (track, fix if time)

---

## A. Auth & Session (6)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 1 | New user sign-up | Landing → Sign up → email confirm → onboarding | Business created with `local_id`; dashboard loads | 🔴 |
| 2 | Returning user sign-in | Sign out → sign in same account | Previous active business restored via `activeBusinessIdByUser` | 🔴 |
| 3 | Shared phone — user switch | User A sign out → User B sign in | User B sees only their businesses/transactions; no A data in UI | 🔴 |
| 4 | Session expiry mid-sale | Start sale form → expire JWT (DevTools) → save | Graceful error or re-auth prompt; no silent data loss | 🟡 |
| 5 | Password recovery | Forgot password → reset link → new password → sign in | Can access prior data after restore/sync | 🟡 |
| 6 | Sign out cleanup | Record sale → sign out | In-memory store cleared; re-login loads correct scoped data | 🔴 |

## B. Core Ledger (6)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 7 | Manual sale | Add → Sale → KES 500 → Save | Dashboard profit +KES 500; History shows entry; receipt ID generated | 🔴 |
| 8 | M-Pesa SMS income | Paste standard M-Pesa received SMS | Amount, sender, method auto-filled; saves as income | 🔴 |
| 9 | Expense + withdrawal | Record expense 200, withdrawal 100 | Dashboard reflects both; profit math correct (money.ts) | 🔴 |
| 10 | Edit transaction | History → edit amount → save | Local + queue updated; dashboard recalculates | 🔴 |
| 11 | Delete with undo | History → delete → undo | Transaction restored; profit restored | 🟡 |
| 12 | Double-tap save | Tap Save twice rapidly on sale | Exactly one transaction created | 🟡 |

## C. Offline & Sync (6)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 13 | Offline sale | DevTools → Offline → record sale → Online | Sale visible offline; syncs on reconnect; SyncDot healthy | 🔴 |
| 14 | 50 offline sales burst | Offline → 50 sales → Online | All 50 reach Supabase; none marked synced if upsert failed | 🔴 |
| 15 | Manual Sync Now | Settings → Sync Now | Toast shows synced count; no false "synced" on failed rows | 🔴 |
| 16 | Cloud restore | Device A sync → Device B → Restore from Cloud | B shows A's transactions after restore | 🔴 |
| 17 | Conflict — concurrent edit | Edit same tx on two devices offline → both online | Dead-letter or LWW; no corrupted amount; user notified | 🟡 |
| 18 | Supabase outage | Block `*.supabase.co` → use app 30 min | All writes local; no crash; queue drains when unblocked | 🟡 |

## D. Multi-Business & Tenancy (4)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 19 | Add second business | Settings → Add business → switch | Each business has unique `local_id`; switch updates dashboard | 🔴 |
| 20 | Business-scoped transactions | Sale in Biz A → switch to Biz B | B dashboard excludes A's sale (by `business_id`) | 🔴 |
| 21 | Multi-business sync | Add Biz B → sync | Both businesses push to Supabase under same user | 🟡 |
| 22 | Legacy user_id business id | Account created before v5.9.4 | Migration or fallback resolves active business correctly | 🟡 |

## E. Performance & Device (4)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 23 | Large history (1000+ tx) | Seed or import 1000 transactions | Dashboard loads < 3s; History scroll smooth | 🟡 |
| 24 | Low-end Android Chrome | Test on 2GB RAM device | PWA usable; no white screen > 5s | 🟡 |
| 25 | PWA install | Install to home screen → open | Same data as browser; offline works | 🟢 |
| 26 | 2G throttling | DevTools Slow 3G → open app | LoadingScreen → usable within 10s on cache hit | 🟢 |

## F. Daily Close & Edge Time (2)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 27 | Daily close after 8pm EAT | Record sales → wait past 8pm Nairobi | Modal appears; close saves to Dexie with `synced: 0` | 🟡 |
| 28 | Midnight boundary | Record sale 11:59pm → 12:01am | Correct day bucket on dashboard | 🟢 |

## G. Backup & Data Integrity (2)

| # | Scenario | Steps | Pass criteria | Pri |
|---|----------|-------|---------------|-----|
| 29 | Export backup JSON | Settings → Export Backup | File includes `_version`, `_exported_at`, all tables | 🟡 |
| 30 | Fuliza + SMS variants | Paste Fuliza M-Pesa SMS + 3 non-standard formats | Parser extracts amount or shows clear error | 🟡 |

---

## Execution log

| Date | Environment | Tester | P0 pass | P1 pass | Notes |
|------|-------------|--------|---------|---------|-------|
| | localhost | | /13 | | |
| | staging | | /13 | | |

**Launch gate:** All 🔴 scenarios PASS on staging + `npm run test:run` green + E2E green in CI.

## Automation mapping

| Scenarios | Automated by |
|-----------|--------------|
| 7, 9–10 | Vitest (store, repository, transaction forms) |
| 13–15 | `syncAll.test.ts`, `syncQueue.test.ts` |
| 14 partial | `syncAll.test.ts` early-failure marking |
| 3, 6, 19–20 | `store.test.ts`, `businessId.test.ts`, `session.test.ts` |
| 7, navigation | Playwright E2E (`e2e/*.spec.ts`) |

Run automated suite before manual checklist:

```bash
npm run typecheck && npm run lint && npm run test:run && npm run build
CI=true PLAYWRIGHT_CHROMIUM_PATH=/usr/bin/google-chrome npm run test:e2e
```
