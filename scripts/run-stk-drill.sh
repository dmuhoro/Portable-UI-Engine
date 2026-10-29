#!/usr/bin/env bash
# End-to-end M-Pesa drill: a REAL STK push to a REAL phone, then proof that the
# money actually settled and reconciled.
#
# scripts/verify-stk-callback-e2e.sh proves the callback logic settles correctly
# when it is handed a Daraja-shaped payload. That is necessary but NOT
# sufficient: it never talks to Safaricom. This script closes that gap by
# driving the real chain end to end:
#
#   stk-push (real OAuth + real STK request)
#     -> YOUR PHONE shows an M-Pesa prompt that only you can approve
#     -> Safaricom debits the till and POSTs the real callback
#     -> we verify request PAID, receipt stored, income booked, health clean
#
# It refuses to run unless scripts/daraja-preflight.sh says READY, so it can
# never half-run against a half-configured merchant.
#
# Usage: scripts/run-stk-drill.sh <msisdn> [amount] [project_ref]
#   msisdn     the phone that will receive the prompt (e.g. 254798655485)
#   amount     whole KES, default 1 (never drill with real money by accident)
#
# Reads API keys into variables and never prints them. Creates and deletes a
# throwaway auth user and probe rows.
set -euo pipefail

MSISDN="${1:?usage: scripts/run-stk-drill.sh <msisdn> [amount] [project_ref]}"
AMOUNT="${2:-1}"
REF="${SUPABASE_PROJECT_REF:-${3:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
STAMP=$(date +%s)
EMAIL="stk-drill-${STAMP}@daftari.test"
PASSWORD="Dr1ll-${STAMP}-Aa1!"

if ! [[ "$AMOUNT" =~ ^[0-9]+$ ]] || [ "$AMOUNT" -lt 1 ] || [ "$AMOUNT" -gt 150000 ]; then
  echo "FATAL: amount must be a whole number of KES within [1, 150000]" >&2
  exit 2
fi

# ── Gate: never attempt a push we already know will be refused ───────────────
echo "==> preflight"
if ! ./scripts/daraja-preflight.sh "$REF"; then
  echo
  echo "DRILL ABORTED: Daraja is not fully configured, so no prompt would appear."
  echo "Set the missing credential first (see the instructions above)."
  exit 1
fi

# Key parsing lives in one shared place. This script used to carry its own
# hand-typed copy of it, and that copy had a ternary with no else-branch — a
# syntax error — so the drill aborted before it ever talked to Safaricom. The
# script looked complete and had never once run.
source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"
ANON="$ANON_KEY"; SERVICE="$SERVICE_KEY"

field() { printf '%s' "$1" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const o=JSON.parse(s)[0]||{};process.stdout.write(String(o[process.argv[1]]??"MISSING"))}catch{process.stdout.write("UNPARSEABLE")}})' "$2"; }
fail=0
assert() { if [[ "$3" == "$2" ]]; then echo "  OK   $1 = $3"; else echo "  FAIL $1 = '$3', expected '$2'"; fail=1; fi; }
as_user() { curl -s "${API}/rest/v1/$1?select=${2:-*}" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}"; }

echo
echo "==> creating a throwaway customer"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"email_confirm\":true}"
TOKEN=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
USERID=$(curl -s "${API}/auth/v1/user" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).id??"")}catch{}})')
[[ -n "$TOKEN" && -n "$USERID" ]] || { echo "FAIL: no user identity"; exit 1; }

LOCAL="drill-${STAMP}"

cleanup() {
  # Transactions first: leaving a 1 KES income row behind would silently
  # corrupt real revenue and profit reporting.
  curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_transactions?local_id=like.drill-*" \
    -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
  curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_stk_requests?local_id=like.drill-*" \
    -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
  curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_businesses?local_id=like.drill-*" \
    -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
  curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${USERID}" \
    -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
}
trap cleanup EXIT

echo "==> creating a throwaway business owned by the drill customer"
# Two contract details, both verified against the real code rather than assumed:
#   * ownership is user_id (RLS policy + the stk-push gate both use it);
#     owner_id is legacy and nullable, so writing only owner_id yields a row
#     that exists but is invisible to the gate
#   * stk-push compares businessId against daftari_businesses.local_id, the
#     same thing StkPushPanel.tsx sends, so this must NOT be the UUID
biz=$(curl -s -X POST "${API}/rest/v1/daftari_businesses" \
  -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" \
  -H 'Content-Type: application/json' -H 'Prefer: return=representation' \
  -d "{\"local_id\":\"${LOCAL}\",\"user_id\":\"${USERID}\",\"name\":\"STK Drill ${STAMP}\",\"payment_methods\":[\"till_number\"]}")
BUSINESSID=$(printf '%s' "$biz" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const o=JSON.parse(s);process.stdout.write(Array.isArray(o)?(o[0]?.id??""):(o?.id??""))}catch{}})')
if [ -z "$BUSINESSID" ]; then
  echo "FAIL: could not create the drill business, so the push would be refused." >&2
  echo "${biz}" >&2
  exit 1
fi
echo "  business ${BUSINESSID} (local_id ${LOCAL})"

echo
echo "########## STEP 1: fire a real STK push to ${MSISDN} for ${AMOUNT} KES ##########"
echo "  The function mirrors a PENDING row first, so an approval can be attributed."
resp=$(curl -s -w '\n%{http_code}' -X POST "${API}/functions/v1/stk-push" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d "{\"amount\":${AMOUNT},\"phone\":\"${MSISDN}\",\"accountReference\":\"DRILL\",\"transactionDesc\":\"Daftari drill\",\"businessId\":\"${LOCAL}\",\"localId\":\"${LOCAL}\",\"paymentMethod\":\"till_number\"}")
code=$(printf '%s' "$resp" | tail -1)
body=$(printf '%s' "$resp" | sed '$d')
echo "  HTTP ${code}"
echo "  ${body}"

if [ "$code" != "200" ]; then
  echo
  echo "DRILL FAILED: Safaricom did not accept the push."
  echo "  - 502 UPSTREAM usually means the consumer key/secret, passkey, or the"
  echo "    store/till number does not match the product Safaricom issued."
  echo "  - Check the STK push product page in the Daraja portal for the exact"
  echo "    Business Short Code and Passkey belonging to THIS environment."
  exit 1
fi

CHECKOUT=$(printf '%s' "$body" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).checkoutRequestId??"")}catch{}})')
[[ -n "$CHECKOUT" ]] || { echo "FAIL: no CheckoutRequestID to reconcile against"; exit 1; }
echo "  CheckoutRequestID = ${CHECKOUT}"
echo
echo "  >>> APPROVE THE PROMPT ON ${MSISDN} NOW (enter your M-Pesa PIN)."
echo "  >>> If no prompt arrives, the request never reached your handset."

echo
echo "==> waiting up to 120s for Safaricom's real callback"
settled=no
for _ in $(seq 1 40); do
  sleep 3
  r=$(as_user daftari_stk_requests "status,mpesa_code" "local_id=eq.${LOCAL}")
  st=$(field "$r" status)
  if [ "$st" = "PAID" ]; then settled=yes; break; fi
  if [ "$st" = "FAILED" ]; then echo "  request settled as FAILED"; break; fi
  printf '.'
done
echo

echo
echo "########## STEP 2: did the real money actually reconcile? ##########"
if [ "$settled" != yes ]; then
  echo "  FAIL no callback arrived within 120s. Nothing was booked, so the"
  echo "       customer was NOT charged and no income was recorded. Investigate"
  echo "       before treating the flow as live."
  exit 1
fi

assert "request is marked PAID" "PAID" "$(field "$r" status)"
receipt=$(field "$r" mpesa_code)
if [ "$receipt" != "MISSING" ] && [ -n "$receipt" ]; then
  echo "  OK   a real M-Pesa receipt was stored = ${receipt}"
else
  echo "  FAIL no M-Pesa receipt stored — the callback did not carry one"; fail=1
fi

tx=$(as_user daftari_transactions "amount,source" "local_id=eq.${LOCAL}")
assert "income was booked" "$AMOUNT" "$(field "$tx" amount)"
assert "sourced from daraja" "daraja" "$(field "$tx" source)"

h=$(as_user stk_health)
assert "no unbooked income" "0" "$(field "$h" income_without_request)"
assert "no amount mismatch" "0" "$(field "$h" amount_mismatch)"

echo
if [ "$fail" -eq 0 ]; then
  echo "DRILL PASSED: a real M-Pesa payment reached the till and reconciled."
  echo "Keep the receipt number above as launch evidence."
else
  echo "DRILL FAILED: see the FAIL lines above."
fi
exit "$fail"
