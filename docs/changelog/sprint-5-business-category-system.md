# Sprint 5 — Phase 1: Business Category System + Onboarding Redesign

**Date:** Planned  
**Version:** 1.4.0  
**Status:** Pending ⏳

## Objective
Replace the single-purpose chapati vendor tool with a multi-category business platform. Introduce 7 business categories with subcategories, personalized expense categories, and a 5-step onboarding flow.

## Scope

### Business Category Data (`src/lib/businessCategories.ts`)
- 7 primary categories: food_beverage, retail, jua_kali, agriculture, services, transport, professional
- 20+ subcategories with icons, Kiswahili/English labels
- Per-category expense categories and product templates
- Payment method defaults per category

### Onboarding Redesign (5-step flow)
1. Business category selection (visual grid with icons)
2. Subcategory selection
3. Products/services they sell (user adds, category templates offered as defaults)
4. Payment methods they accept (pre-selected defaults per category)
5. Business name → done → dashboard

### Existing Screen Updates
- Dashboard: personalize labels based on category
- Add screens: filter expense categories by business type
- Quick-add: show user's own products from their catalog

## Files to Create
- `src/lib/businessCategories.ts`
- `src/lib/businessCategories.test.ts`
- `src/screens/OnboardingScreen.tsx` (or `src/features/onboarding/`)
- `src/features/onboarding/CategoryGrid.tsx`
- `src/features/onboarding/SubcategoryPicker.tsx`
- `src/features/onboarding/ProductSetup.tsx`
- `src/features/onboarding/PaymentMethodSetup.tsx`
- `src/features/onboarding/BusinessNameStep.tsx`

## Files to Modify
- `src/lib/store.ts` — store business category, subcategory, products
- `src/lib/db.ts` — add category/subcategory fields to business table (version bump)
- `src/screens/DashboardScreen.tsx` — personalize by category
- `src/App.tsx` — route to onboarding if no category set
- `src/i18n/sw.json` — category labels, onboarding strings
- `src/i18n/en.json` — category labels, onboarding strings

## Acceptance Criteria
- [ ] All 7 categories selectable from grid
- [ ] Subcategory selection filters by parent category
- [ ] Product setup shows category-specific defaults (user can edit)
- [ ] Payment methods default per category (user can edit)
- [ ] Onboarding skipped if returning user (business already has category)
- [ ] Dashboard labels match business type
- [ ] Expense categories in Add screen filtered by business type
- [ ] Works fully offline
- [ ] i18n: all new strings in both sw.json and en.json
- [ ] npm run typecheck — zero errors
- [ ] npm run test:run — all tests pass (including businessCategories.test.ts)

## Dependencies
- None

## Next
Sprint 6: Phase 2 — Payment Infrastructure + Expanded SMS Parsing
