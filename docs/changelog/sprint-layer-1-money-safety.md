# Sprint: Post-Audit Remediation — Layer 1: Money Safety

**Version:** 5.8.2
**Date:** 2026-07-23
**Theme:** Fix P1 money safety violations in PosScreen and print.ts, verify with tests.

---

## What Changed

### P1 Fixes
- **PosScreen.tsx** (lines 54, 56-57, 132, 259): Replaced raw `cents()` arithmetic with `kesSum()`, `kesSubtract()`, `toKES()` from `money.ts`
  - `cartTotal = kesSum(cart.map(i => toKES(i.price * i.qty)))`
  - `discount = toKES(redeemPoints ? Math.min(maxRedeem, cartTotal) : 0)`
  - `finalTotal = kesSubtract(cartTotal, discount)`
- **print.ts** (line 63): Wrapped `data.amount + data.discount` with `cents()` from `money.ts`

### New Tests
- **PosScreen.test.tsx** (7 tests): Cart total calculations, mixed items, quantity updates, item removal, kesSubtract discount
- **print.test.ts** (+1 test): Floating-point precision for receipt subtotals with discounts

## Verification
- Typecheck: 0 errors
- Lint: 0 errors
- Tests: 293/293 passing
- Build: Success (40.87s)

---

## Files Changed

```
M  src/screens/PosScreen.tsx
M  src/lib/print.ts
A  src/screens/PosScreen.test.tsx
M  src/lib/print.test.ts
M  CHANGELOG.md
```
