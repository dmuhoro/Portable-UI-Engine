# Sprint 7 — Phase 3: Dynamic Product Catalog + Personalized Quick-Add

**Date:** Planned  
**Version:** 1.6.0  
**Status:** Pending ⏳

## Objective
Replace the hardcoded "chapati KES 20" quick-add chips with a dynamic product catalog. Users manage their own products, and quick-add chips reflect what they actually sell — personalized by business category.

## Scope

### Product Catalog (Dexie table)
- New `products` table in Dexie: id, name, price (KES), unit, category_key, sort_order
- CRUD repository functions for products
- Product management screen in Settings
- Category-specific product templates seeded from businessCategories.ts

### Personalized Quick-Add
- Quick-add chips load from user's product catalog (not hardcoded)
- Preserve quick-add as 1-tap → amount screen → confirm
- Default sort: by frequency of use (track usage count)
- Show product unit in chip label where applicable

### Product Management UI
- Settings → Manage Products screen
- Add product: name, price, unit (optional), category auto-set from business
- Edit product: change name/price/unit
- Delete product: confirm dialog
- Bulk-add from category templates during onboarding

## Files to Create
- `src/features/products/ProductCatalog.tsx`
- `src/features/products/ProductForm.tsx`
- `src/features/products/ProductList.tsx`
- `src/features/products/ProductChip.tsx`

## Files to Modify
- `src/lib/db.ts` — add products table (version bump)
- `src/lib/repository.ts` — add product repository functions
- `src/lib/types.ts` — add Product type (if not already there)
- `src/screens/AddScreen.tsx` — load chips from product catalog
- `src/screens/SettingsScreen.tsx` — add "Manage Products" link
- `src/features/transactions/RecordSale.tsx` — use product catalog for quick-add
- `src/features/transactions/RecordExpense.tsx` — potentially use product catalog
- `src/i18n/sw.json` — product management strings
- `src/i18n/en.json` — product management strings

## Acceptance Criteria
- [ ] Products table created in Dexie with proper indexes
- [ ] User can add/edit/delete products in Settings
- [ ] Quick-add chips load from user's product catalog
- [ ] Category-specific default products seeded on first login
- [ ] Product price pre-fills on quick-add tap (user can override)
- [ ] Works fully offline
- [ ] All new strings in both sw.json and en.json
- [ ] npm run typecheck — zero errors
- [ ] npm run test:run — all tests pass

## Dependencies
- Sprint 5 (Business Categories) — product templates per category
- Sprint 6 (Payment Infrastructure) — payment method integration in quick-add

## Next
Sprint 8: Phase 4 — Market Polish
