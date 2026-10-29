# 2026-08-25 — M-Pesa STK Push + D11 Encryption Verification

## M-Pesa STK Push — Unit Verification

Command: `npx vitest run src/__tests__/mpesa-stk-push.test.ts`
Result: **12 tests passed**.

Verified: phone normalization (+, 0, 254 prefixes), Daraja timestamp format,
callback metadata extraction (Amount/MpesaReceiptNumber), initiate success records
pending row, initiate failure returns `init_failed` with no DB write, callback
ResultCode 0 records payment via `recordPayment`, non-zero marks failed, replayed
success is idempotent, unknown checkout returns error.

## D11 PII Encryption Wiring — Unit Verification

Command: `npx vitest run src/__tests__/leads-encryption.test.ts`
Result: **4 tests passed**.

Verified (real path, not a mock):
- `encryptLeadPII` (used by `submitLead`) produces `ENC:`-prefixed values
- `decryptLeadRows` (used by `fetchLeads`) returns plaintext
- Legacy plaintext rows pass through (lazy migration)
- STK push phone is encrypted on insert

## Live Verification Status

| Item | Status | Evidence |
|------|--------|----------|
| STK push unit tests | PASS | above |
| Encryption wiring tests | PASS | above |
| STK push against Daraja sandbox | **BLOCKED** | requires MPESA_CONSUMER_KEY/SECRET/SHORTCODE/PASSKEY/CALLBACK_SECRET (owner-held) |
| WhatsApp live delivery to +254703939236 | **BLOCKED** | requires WHATSAPP_TOKEN + WHATSAPP_PHONE_NUMBER_ID (owner-held) |

## Verdict

Code-level verification PASS. Live channel verification is blocked on owner-held
credentials — see `docs/evidence/2026-08-25_deployment.md`.