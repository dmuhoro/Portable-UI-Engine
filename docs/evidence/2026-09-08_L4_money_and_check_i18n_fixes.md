# Daftari evidence — L4 fixes (2026-09-08): money fail-open + check-i18n whitelist drift

Two real fixes driven through the Forge task journal (`queued → … → merged`,
reviewer notes recorded). Both commits SSH-signed (`%G?` = G) and pushed. Root
CHANGELOG row at `3cedd2f`.

## 1. `parseKESInput` silently truncated malformed money (fail-open) — `f64acc5` G

**Before (bug, reproduced at HEAD `36eaf82`):**

```
input      parsed (WRONG)
'1.5.5'    -> 2
'1-2'      -> 1
'15..5'    -> 15
'1500.10.5'-> 1500
```

Rogue digits were dropped so the **wrong amount** reached the money path — a
fail-open that could record the wrong number silently.

**Fix — `src/lib/money.ts` (fail-closed):** the input must match
`/^\d+(\.\d+)?$/` (no sign, no multiple dots), digits are parsed with `Number()`
(not `parseFloat`), and any malformed input returns `null` — the caller now has
to handle and surface the refusal; it can never be a silent truncation.

**Proof:**

```
input          parsed (fixed)
'1500'         -> 1500          # valid still parses
'1.5'          -> 1.5
'1.5.5'        -> null          # was 2
'1-2'          -> null          # was 1
'15..5'        -> null          # was 15
'1500.10.5'    -> null          # was 1500
```

`npm run test:run` → **402 passed** (399 baseline + 3 new cases in
`money.test.ts`); `npm run typecheck` + `npm run lint` clean.

## 2. `check-i18n` hardcoded DYNAMIC_KEYS whitelist drifted (false positives) — `0af9d0f` G

**Before:** `scripts/check-i18n.ts` carried a hand-maintained `DYNAMIC_KEYS` list.
It silently missed the onboarding `yes_set_q1..3` keys, so three real keys
reported "unused" and the linter had blind spots.

**Fix:** the list is grep-sourced from the actual render sites — `labelKey: "…"`
and `\bid: \d+,? key: "…"` in `src/screens/OnboardingScreen.tsx`, and the
`sale_recorded | expense_recorded | withdrawal_recorded` literals in
`src/components/Receipt.tsx`. A sourced key missing from `sw.json`/`en.json`
now **fails the check** (exit 1) instead of being noisily ignored.

**Proof:**

```
$ npm run check:i18n
✅ i18n check passed — 238 keys in use, 238 in sw.json, 238 in en.json   # zero unused

# fail-closed trial: temporarily rename a sourced key, expect the check to fail
$ sed -i "s/'pain_uncollected_debts'/'pain_uncollected_debts_broken'/" src/screens/OnboardingScreen.tsx
$ npm run check:i18n
❌ Dynamic key "pain_uncollected_debts_broken" … MISSING from sw.json/en.json   # exit 1
$ git checkout -- src/screens/OnboardingScreen.tsx                            # restore
✅ i18n check passed — 238 keys in use, 238 in sw.json, 238 in en.json
```

The scan returns exactly the 14 real dynamic keys (4 pain + 4 method + 3
yes_set + 3 receipt literals).

## Verification summary

| Gate | Result |
|---|---|
| `npm run test:run` | **402 passed** |
| `npm run typecheck` | clean |
| `npm run lint` | clean |
| `npm run check:i18n` | 238/238/238, zero unused; fails on missing key |
| Signing | `f64acc5` `%G?`=G, `0af9d0f` `%G?`=G, `3cedd2f` `%G?`=G |
| Pushed | `36eaf82 → 3cedd2f` origin/main |

Not claimed: neither fix changes the realtime/Supabase path; both are NumInput
validation and linter accuracy, verified at their own boundaries. Owned by Daftari;
cited at the ShrinkMedia vertex (sprint-28, C34).