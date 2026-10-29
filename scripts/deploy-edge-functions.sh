#!/usr/bin/env bash
# Deploy Daftari's Edge Functions with the JWT posture each one actually needs.
#
# WHY THIS SCRIPT EXISTS
# ----------------------
# v6.13.0 shipped an outage that no test caught: the callback was deployed with
# the CLI default (verify_jwt = true). Safaricom cannot send a Supabase JWT, so
# the gateway rejected every confirmation. Safaricom saw ResultCode 0, retried
# nothing, and the failure was silent. Worse, the health view reported a clean
# bill of health because the callbacks were rejected before any handler code ran.
#
# The posture is not obvious from the function name, so it lives here instead of
# in someone's shell history:
#
#   lipa-na-mpesa-callback   verify_jwt = FALSE  (Safaricom calls it; no JWT exists)
#   c2b-confirmation         verify_jwt = FALSE  (Safaricom calls it; no JWT exists)
#   stk-push                 verify_jwt = TRUE   (called by our authenticated app)
#   send-daily-close-push    verify_jwt = TRUE   (called by our authenticated app)
#
# Deploying the callback WITHOUT --no-verify-jwt silently breaks all payment
# confirmation. This script makes that impossible to do by accident, and proves
# the resulting posture instead of assuming it.
#
# Usage: scripts/deploy-edge-functions.sh [project_ref]
set -euo pipefail

PROJECT_REF="${1:-${SUPABASE_PROJECT_REF:-}}"
if [[ -z "$PROJECT_REF" ]]; then
  echo "error: pass a project ref or set SUPABASE_PROJECT_REF" >&2
  exit 1
fi

API_URL="https://${PROJECT_REF}.supabase.co"
CB_URL="${API_URL}/functions/v1/lipa-na-mpesa-callback"
C2B_URL="${API_URL}/functions/v1/c2b-confirmation"

echo "==> deploying to ${PROJECT_REF}"

# The callback. --no-verify-jwt is NOT optional and NOT default.
echo "--> lipa-na-mpesa-callback (verify_jwt=false)"
supabase functions deploy lipa-na-mpesa-callback \
  --project-ref "$PROJECT_REF" \
  --no-verify-jwt

# The C2B ConfirmationURL. Same reasoning as the STK callback: Safaricom POSTs
# here with no JWT. Shipping it JWT-gated would make every customer-initiated
# payment silently unreconciled — the exact v6.13.0 failure, on a new endpoint.
echo "--> c2b-confirmation (verify_jwt=false)"
supabase functions deploy c2b-confirmation \
  --project-ref "$PROJECT_REF" \
  --no-verify-jwt

# Authenticated user-facing functions. --no-verify-jwt is deliberately absent:
# these must keep rejecting anonymous callers, so the flag must never be added.
for fn in stk-push send-daily-close-push; do
  echo "--> ${fn} (verify_jwt=true)"
  supabase functions deploy "$fn" --project-ref "$PROJECT_REF"
done

echo
echo "==> verifying the deployed JWT posture"

# 1. The callback must be reachable WITHOUT a JWT. Safaricom's request is a bare
#    POST; if this is rejected we have recreated the v6.13.0 outage. A forged body
#    is safe to send here: it is written to the audit trail as IGNORED and can
#    never move money, because no matching PENDING request exists.
echo "--> callback must ACCEPT an unauthenticated POST (Safaricom has no JWT)"
status=$(curl -s -o /tmp/deftari-cb-probe.txt -w '%{http_code}' \
  -X POST "$CB_URL" \
  -H 'Content-Type: application/json' \
  -d '{"Body":{"stkCallback":{"CheckoutRequestID":"deploy-probe-not-a-real-request","ResultCode":1}}}' \
  --max-time 30)
# Anything in the 2xx/3xx range proves the gateway let it through to the handler.
if [[ "$status" -ge 200 && "$status" -lt 400 ]]; then
  echo "    OK (HTTP $status) — callback is public, as required"
else
  echo "    FAIL (HTTP $status) — the callback is JWT-gated and will reject all" >&2
  echo "    of Safaricom's confirmations. Re-run without dropping --no-verify-jwt." >&2
  exit 1
fi

# 1b. The C2B ConfirmationURL must also be reachable WITHOUT a JWT. A forged
#     body here is safe: it is recorded with safaricom_confirmed = false and can
#     never settle, because settlement requires Safaricom to confirm the TransID.
echo "--> c2b-confirmation must ACCEPT an unauthenticated POST (Safaricom has no JWT)"
status=$(curl -s -o /tmp/deftari-c2b-probe.txt -w '%{http_code}' \
  -X POST "$C2B_URL" \
  -H 'Content-Type: application/json' \
  -d '{"TransID":"deploy-probe-not-a-real-transaction","TransAmount":"1","ReceiptNo":"PROBE0000","MSISDN":"254000000000","BusinessShortCode":"3631767"}' \
  --max-time 30)
if [[ "$status" -ge 200 && "$status" -lt 400 ]]; then
  echo "    OK (HTTP $status) — C2B confirmation URL is public, as required"
else
  echo "    FAIL (HTTP $status) — C2B is JWT-gated and will reject every" >&2
  echo "    customer-initiated payment. Re-run without dropping --no-verify-jwt." >&2
  exit 1
fi

# 2. The authenticated functions must still REJECT an anonymous caller. This is
#    the check that stops someone "fixing" the callback by disabling JWT on
#    everything.
for fn in stk-push send-daily-close-push; do
  echo "--> ${fn} must REJECT an unauthenticated POST"
  status=$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "${API_URL}/functions/v1/${fn}" \
    -H 'Content-Type: application/json' \
    -d '{}' \
    --max-time 30)
  if [[ "$status" == "401" || "$status" == "403" ]]; then
    echo "    OK (HTTP $status) — still authenticated"
  else
    echo "    FAIL (HTTP $status) — expected 401/403. ${fn} is publicly reachable." >&2
    exit 1
  fi
done

echo
echo "All functions deployed and the JWT posture is verified."
