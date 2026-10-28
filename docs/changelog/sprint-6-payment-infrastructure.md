# Sprint 6 — Phase 2: Payment Infrastructure + Expanded SMS Parsing

**Date:** Planned  
**Version:** 1.5.0  
**Status:** Pending ⏳

## Objective
Expand M-Pesa SMS parsing to cover all 7 payment patterns (A-G), add payment_method to transaction schema, and build the payment method selection component for the quick-add flow.

## Scope

### Expanded SMS Parsing
- Pattern D: Pochi La Biashara ("You have received KSh X from NAME PHONE to Pochi la Biashara...")
- Pattern E: Till Number / Buy Goods ("[BUSINESS] has received KSh X from NAME PHONE. Trans ID CODE")
- Pattern F: Paybill ("[BUSINESS] received KSh X from NAME PHONE. Account ACC. Trans CODE")
- Pattern G: Airtel Money ("You have received Ksh X from NAME PHONE via Airtel Money. Ref: CODE")
- Generic fallback improvement for unrecognized patterns

### Payment Method Infrastructure
- Add `payment_method` field to transaction schema (Dexie + Supabase)
- Payment method chip selector in Add screens
- Store payment_method on all quick-add and SMS-parsed transactions
- Display payment method icon in transaction history rows
- Filter/sort transactions by payment method (future use)

### SMSParser Component Enhancement
- Show detected payment method icon in SMS confirmation card
- Allow user to override detected payment method
- Show payment method in Kiswahili + English

## Files to Create
- `src/features/sms/PaymentMethodChip.tsx`
- `src/features/sms/PaymentMethodSelector.tsx`

## Files to Modify
- `src/features/sms/parseMpesa.ts` — add patterns D-G, return payment_method
- `src/features/sms/parseMpesa.test.ts` — add tests for patterns D-G
- `src/features/sms/SMSParser.tsx` — show detected payment method
- `src/features/transactions/RecordSale.tsx` — add payment method selector
- `src/features/transactions/RecordExpense.tsx` — add payment method selector
- `src/lib/db.ts` — add payment_method field (version bump)
- `src/lib/types.ts` — ensure PaymentMethod type is comprehensive
- `src/lib/repository.ts` — handle payment_method in saveTransaction
- `src/screens/HistoryScreen.tsx` — show payment method icon per row
- `src/i18n/sw.json` — payment method labels
- `src/i18n/en.json` — payment method labels

## Acceptance Criteria
- [ ] SMS patterns D-G parse correctly with payment_method detection
- [ ] All existing tests still pass with new return shape
- [ ] 100% branch coverage on parseMpesa.ts
- [ ] Payment method selector visible in Add screens
- [ ] Payment method stored in Dexie and displayed in history
- [ ] Detected payment method shown in SMS confirmation card
- [ ] User can override detected payment method
- [ ] Works fully offline
- [ ] npm run typecheck — zero errors
- [ ] npm run test:run — all tests pass

## Dependencies
- Sprint 5 (Business Categories) must be complete — payment method defaults per category feed into this sprint

## Next
Sprint 7: Phase 3 — Dynamic Product Catalog + Personalized Quick-Add
