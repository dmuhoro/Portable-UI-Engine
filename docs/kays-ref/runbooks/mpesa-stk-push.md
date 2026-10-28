# Runbook: M-Pesa STK Push

> How to operate the automatic payment flow.

## Flow

1. Clinic creates/opens an invoice for a lead.
2. Staff calls **initiate STK push** (server function) with invoiceId + amount + patient phone.
3. Platform: rate-limit check → Daraja oauth token → `mpesa/stkpush/v1/processrequest` →
   inserts `mpesa_stk_push_requests` row (status `pending`).
4. Patient receives STK push prompt on their phone and enters M-Pesa PIN.
5. Safaricom calls `POST /api/webhooks/mpesa` with the callback.
6. Platform: verify callback secret → find request by `CheckoutRequestID` → update status
   (`success`/`failed`) + result code + receipt → on success record payment (idempotent) + mark
   invoice paid.

## Auth

- Callback requires `x-callback-secret` header (or `?secret=` query) == `MPESA_CALLBACK_SECRET`.
  If `MPESA_CALLBACK_SECRET` is unset, callback is rejected (fail closed).

## Idempotency

- Unique `(organization_id, checkout_request_id, mpesa_receipt_number)`.
- Replayed callback → `{ ok: true, idempotent: true }`, no second payment.

## Sandbox Test

1. Set `MPESA_BASE_URL=https://sandbox.safaricom.co.ke`.
2. Use Daraja sandbox consumer key/secret + test shortcode/passkey.
3. `MPESA_CALLBACK_URL` must be the public Vercel URL.
4. Trigger a push from admin UI; confirm callback arrives; check invoice auto-paid.

## Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 callback | wrong/absent secret | check `MPESA_CALLBACK_SECRET` matches test tool |
| Push never arrives | sandbox creds / shortcode | verify Daraja sandbox setup |
| Callback OK but no payment | idempotency conflict | check `(org, checkout_id, receipt)` uniqueness; replayed? |
| Invoice not auto-paid | amount mismatch or already paid | verify invoice `status='issued'` and amount matches |