# Sprint v5.1.0 — Distribution Infrastructure

**Release date:** 2026-07-20  
**Version:** `5.1.0`  
**Theme:** Making Daftari spreadable — referral, push, admin

---

## What was built

### A — Referral + Onboarding Share
- **Referral link**: `generateReferralUrl()` creates UTM-tagged URL with `?ref=[businessCode]&cat=[category]&utm_source=referral&utm_medium=whatsapp`. Business code = first 4 letters of business name.
- **"Tell a Friend" button**: SettingsScreen — opens WhatsApp with Kiswahili/English referral message. Most important organic growth feature.
- **Events tracked**: `REFERRAL_LINK_SHARED`, `REFERRAL_SIGNUP_COMPLETED`
- **`referral_code` field**: Added to Business interface in db.ts

### B — Web Push Notifications
- **Client utility**: `pushNotifications.ts` — `requestNotificationPermission()`, `subscribeToPush()`, `unsubscribeFromPush()`. Stores subscription in `daftari_push_subscriptions` Supabase table.
- **Edge Function**: `supabase/functions/send-daily-close-push/index.ts` — queries active users who haven't closed today, sends push via VAPID keys.
- **Onboarding opt-in**: Step 4 asks "Receive daily close reminders?" with Bell icon. Permission only requested after explicit button tap.

### C — Supabase Realtime Sync Indicator
- SyncDot subscribes to `postgres_changes` INSERT on `daftari_transactions`.
- Green checkmark shown for 2 seconds when remote data confirmed.
- Falls back to normal dot if no realtime confirmation.

### D — Domain + Social Presence
- Open Graph tags updated for `daftari.co.ke` with Swahili-first descriptions.
- `og:image:width`/`height` added. `twitter:card` added.

### E — Beta Cohort Management
- **AdminScreen**: Business list with 7d transaction count, total tx, last active date. Gated by `VITE_ADMIN_USER_ID`.
- **SQL view**: `docs/beta-feedback-view.sql` — `beta_feedback_summary` for weekly feedback monitoring.

### Infrastructure
- `.env.example` updated with new env vars.
- ESLint config ignores `supabase/` directory.

---

## Files changed

| File | Change |
|------|--------|
| `CHANGELOG.md` | Added v5.1.0 section |
| `package.json` | 5.0.1 → 5.1.0 |
| `.env.example` | Added VITE_CANONICAL_DOMAIN, VITE_VAPID_PUBLIC_KEY, VITE_ADMIN_USER_ID |
| `eslint.config.js` | Ignored `supabase/` directory |
| `index.html` | Updated OG tags for daftari.co.ke |
| `docs/changelog/sprint-v5-1-0-distribution-infrastructure.md` | Created (this file) |
| `docs/beta-feedback-view.sql` | Created — SQL view for beta feedback |
| `src/lib/referral.ts` | Created — referral URL + WhatsApp share |
| `src/lib/analytics.ts` | Added REFERRAL_LINK_SHARED, REFERRAL_SIGNUP_COMPLETED events |
| `src/lib/db.ts` | Added referral_code to Business interface |
| `src/lib/pushNotifications.ts` | Created — push subscription utilities |
| `supabase/functions/send-daily-close-push/index.ts` | Created — Edge Function for 8pm push |
| `src/components/SyncDot.tsx` | Realtime sync confirmation with checkmark |
| `src/screens/AdminScreen.tsx` | Created — beta cohort admin |
| `src/screens/SettingsScreen.tsx` | Added "Tell a Friend" + Admin link |
| `src/components/AppShell.tsx` | Added admin view |
| `src/screens/OnboardingScreen.tsx` | Added step 4 — push notification opt-in |

---

## Verification

```bash
npm run typecheck    # ✅ zero errors
npm run lint         # ✅ zero errors
npm run test:run     # ✅ 54 tests
npm run build        # ✅
```
