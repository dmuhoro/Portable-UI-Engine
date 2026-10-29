# Sprint v6.10.0 — Catalog Cost Price + Barcode + Services (Q1 Polish #6)

**Status:** Completed — all gates green.

## Objective

Land Q1 polish upgrade #6 from the owner-vision audit (v6.8.0): give every product a
recorded cost price, an optional scannable barcode, and an explicit product-vs-service
distinction — so the Product Profitability screen stops being under-fed and stops
overstating profit when a cost is unknown. Scope: catalog domain + UI, sale-path
wiring, honest profitability, i18n, tests, release + tag.

## Work completed

### L1 — Catalog domain (`src/lib/catalog.ts`) + money helper
- `kesPercent(numerator, denominator)` added to `src/lib/money.ts` (whole percents, guarded
  divide-by-zero) — all margin math stays inside the sanctioned ADR-007 module.
- Pure, I/O-free domain module: `isService`, fail-closed `parseCostPrice` (empty = unknown,
  garbage like `-5`/`abc` rejected — never coerced), whitespace-safe `normalizeBarcode`,
  role-aware `findBarcodeConflict` (barcodes unique across products, self-edit excepted),
  `computeProductMargin` via `kesSubtract` + `kesPercent` (absent cost → margin == price,
  *unknown not free*), `normalizeProductForSave` (services drop `stock`/`low_stock_threshold`).
- 17 unit tests (`catalog.test.ts`) incl. money `kesPercent`.

### L2 — Catalog UI (`ProductCatalogScreen`)
- Cost price + barcode inputs on add; pencil edit updates cost/barcode/service on existing
  products; barcode chip + plummet margin line on cards (margin shown *only* when a cost is set).
- Validation: malformed cost and duplicate barcode block save with inline errors; cost above
  price is a visible amber warning but still allowed (sale may be loss-making).
- "Mark as Service" switch hides stock fields; service books no stock on save. Restock stays
  available for goods only.
- 7 component tests — including fail-closed assertions that bad cost / duplicate barcode
  never reach `updateBusiness`.

### L3 — Sale-path wiring
- `RecordSale` quick-add now passes `product_id` + `cost_price` into the transaction and skips
  stock decrement for services (guardrail tests). Previously quick-adds fed profitability nothing.
- `PosScreen` checkout snapshots `product_id` + aggregated `cost_price` for single-product
  carts; blended carts record no product attribution (honest — no false per-product claim).
  Service lines never decrement stock, and a service-only cart performs **no** no-op stock write
  (`stockChanged` gate added).
- `ProductProfitabilityScreen`: unknown-cost products render "no cost set" instead of revenue-as-
  profit; summary card warns total margin may be overstated until cost prices exist.

### L4 — i18n + tests
- 10 keys added to both `sw.json` and `en.json` (`cost_hint`, `barcode_hint`, `mark_as_service`,
  `service_label`, `service_hint`, `edit_product`, `margin`, `cost`, `invalid_cost_price`,
  `barcode_taken`, `cost_above_price`); parity check 317/317 in use both directions.
- Fixed a **midnight/timezone flake**: `DashboardScreen`/`DailyClose` fixtures used UTC
  `new Date().toISOString()` while screens filter by Nairobi date — between 00:00–03:00 EAT the
  suite dropped transactions. Fixtures now build `recorded_at` from the Nairobi day via
  `vi.hoisted` (no top-level circulars in `vi.mock`).

## Final gate state (v6.10.0)

- `npm run typecheck` — ✅ clean
- `npm run lint` — ✅ clean
- `npm run check:i18n` — ✅ 317/317 in use (both locales)
- `npm run test:run` — ✅ full suite green
- `npm run build` — ✅ production build
- Version `6.10.0` in `constants.ts`, `package.json`, `package-lock.json`; CHANGELOG section added;
  this sprint note committed in the same change; tag `v6.10.0` pushed.