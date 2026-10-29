# Sprint v1.2.0 — Functional Profiles, Personalized Dashboard, Business Profile, P0 Bug Fixes

**Date:** 2026-07-19  
**Version:** 1.2.0  
**Status:** Completed ✅

## Objective
Fix two P0 bugs (invisible nav icons, onboarding redirect hanging), complete the business profiles system so all 7 categories have functional income/expense flows, personalize the dashboard per business type, and create a Business Profile screen.

## Scope

### Section A — P0 Bug Fixes

#### A1: Bottom Nav Invisible Colors (AppShell.tsx)
- Nav icon and label colors were invisible after the dark mode refactor (both used the same CSS variable)
- Fixed: explicit `text-green-600 dark:text-green-400` for active, `text-stone-500 dark:text-stone-400` for inactive
- Active indicator bar: `w-8 h-0.5 rounded-full bg-green-600 dark:bg-green-400` at top of active tab
- Added `pb-20` padding to main content area to clear the fixed nav
- Nav uses `fixed bottom-0 left-0 right-0 z-50` with `safe-area-inset-bottom`
- All nav buttons have `aria-label` attributes

#### A2: Onboarding Redirect Hangs (OnboardingScreen.tsx + App.tsx)
- Root cause: `handleSubmit` awaited Supabase `.upsert()` before calling `setBusiness()` and `onComplete()`
- Fix: Dexie-first architecture — business written to IndexedDB immediately, `setBusiness()` called, then `onComplete()` navigates, Supabase upsert queued as fire-and-forget `.then().catch()`
- Created `LoadingScreen.tsx` — reusable splash component (D logo + loading text)
- Added `isLoadingBusiness` state + `useEffect` driven by `[session]` in App.tsx
- Business is reloaded from Dexie whenever session changes (fixes stale data after sign in/out)
- On sign out, business is reset to null in the store

#### A3: Complete businessCategories.ts Template Products
- All 30 subcategories across 7 categories populated with 8-10 realistic products each
- Products have KES prices and units appropriate to the category (e.g. food → pcs/cups, transport → trips/km)
- Exported helpers: `categoryEmoji`, `getTemplateProducts(category, subcategory)`, `getCategoryLabels(lang)`

### Section B — Functional Profiles

#### B1: Per-Category Income Labels + Template Quick-Add (RecordSale.tsx)
- Each BUSINESS_CATEGORY now has `incomeCategories` — 3 income source options with bilingual labels
- Example: food_beverage → Food/Chakula, Beverages/Vinywaji, Other/Nyingine
- Example: transport → Fare/Nauli, Delivery/Usafirishaji, Other/Nyingine
- Template products displayed as "Add from Templates" banner when user has no saved products
- "Add All Templates" button records all template products as transactions in one tap
- Falls back to default `[product_sale, service, other_income]` when no category is set

#### B2: Category/Subcategory Picker in SettingsScreen
- "Change Business Category" button below business info card
- Opens inline two-step picker: category grid → subcategory list
- Uses emoji icons from `categoryEmoji` map
- Saves to store + Dexie + Supabase with `onConflict: 'owner_id'`
- Products reset to empty array on category change
- Added `"change_category"` key to both i18n files

### Section C — Personalized Dashboard

#### DashboardScreen.tsx
- Header shows category emoji + label (e.g. 🍽️ Food & Beverages) below business name
- Income card label uses per-category `incomeLabel` (e.g. "Mauzo/Sales", "Nauli/Fares", "Tume/Commission")
- Expense card label uses per-category `expenseLabel` (e.g. "Gharama/Costs")
- Today's empty state uses per-category `emptyTitle` + `emptyDesc` (e.g. "Bado hakuna mauzo leo" / "Bonyeza + kuongeza mauzo")
- Week empty state uses per-category `emptyWeekTitle` + `emptyWeekDesc`
- Falls back to default i18n keys when no category is set

#### AddScreen.tsx
- Income card sublabel uses per-category `incomeLabel` instead of generic `t('income')`
- SMS parser card and Fuliza section hidden for cash-only businesses (only `payment_methods: ['cash']` or empty)
- Defined `CATEGORY_DASHBOARD_LABELS` export in businessCategories.ts with all 7 categories' bilingual labels

### Section D — Business Profile Screen

#### BusinessProfileScreen.tsx
- Full-screen profile editor with back navigation
- Category display with emoji + bilingual label + subcategory
- Editable business name field
- Editable owner name field
- Payment methods shown as green chips (read-only display)
- Save button persists to store + Dexie + Supabase with 2-second "Saved!" confirmation
- All new strings added to both i18n files

#### SettingsScreen + AppShell Integration
- Profile row in Settings "Account" section now navigates to `'profile'` view when `onNavigate` is provided
- AppShell: `'profile'` added to View type, `BusinessProfileScreen` imported and rendered
- Header hidden for profile view (BusinessProfileScreen has its own header)
- Nav hidden for profile view

## Files Created
- `src/screens/LoadingScreen.tsx`
- `src/screens/BusinessProfileScreen.tsx`

## Files Modified
- `src/App.tsx` — isLoadingBusiness, session-driven business reload
- `src/components/AppShell.tsx` — nav colors, pb-20, active indicator, profile route
- `src/screens/OnboardingScreen.tsx` — Dexie-first submit
- `src/screens/DashboardScreen.tsx` — emoji header, personalized labels, empty states
- `src/screens/AddScreen.tsx` — per-category income label, cash-only mode
- `src/screens/SettingsScreen.tsx` — category picker, profile nav
- `src/features/transactions/RecordSale.tsx` — income categories, template quick-add
- `src/lib/businessCategories.ts` — templateProducts, incomeCategories, categoryEmoji, CATEGORY_DASHBOARD_LABELS, getTemplateProducts, getCategoryLabels
- `src/i18n/sw.json` — 7 new keys
- `src/i18n/en.json` — 7 new keys

## Acceptance Criteria
- [x] Bottom nav: icons visible in light/dark, active indicator bar, content clears nav
- [x] Onboarding: business saved locally first, navigates immediately, Supabase syncs in background
- [x] Template products: all 30 subcategories populated, helpers exported
- [x] RecordSale: income categories per business type, template quick-add
- [x] Settings: category/subcategory inline picker, persists to Dexie + Supabase
- [x] Dashboard: emoji + category in header, personalized income/expense/empty labels
- [x] AddScreen: income label per type, SMS/Fuliza hidden for cash-only
- [x] BusinessProfileScreen: name/owner editable, category display, payment chips, save
- [x] npm run typecheck — zero errors
- [x] npm run lint — zero errors
- [x] npm run test:run — 34/34 tests pass
- [x] npm run build — zero errors
- [x] Git: committed and pushed
- [x] Vercel: redeployed successfully

## Dependencies
- Sprint v1.1.0 completed

## Next
Future sprints: Inventory management, multi-staff support, advanced reporting, paid subscription tier
