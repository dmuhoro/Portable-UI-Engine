#!/usr/bin/env bash
# End-to-end proof that payment reconciliation works THROUGH THE REAL PUBLIC
# ENDPOINT, as the real customer.
#
# v6.13.0 shipped a false all-clear: no customer could see any callback row, so
# stk_health could not report a genuine failure to the person who paid. Agreeing
# totals on an empty database prove nothing, so this drives the actual callback
# function with a real Daraja payload and checks what the customer sees.
#
# Branch 1  amount mismatch  -> must REFUSE, must be visible to the customer
# Branch 2  exact amount     -> must SETTLE, must book income, customer sees PAID
# Branch 3  the customer cannot forge or settle anything themselves
set -euo pipefail

# Requires the Supabase CLI to be linked. Reads API keys into variables and
# never prints them; only booleans and counts are printed. Creates and deletes a
# throwaway auth user and probe rows, so do not run it against production data
# you care about. Usage: scripts/verify-stk-callback-e2e.sh [project_ref]
REF="${SUPABASE_PROJECT_REF:-${1:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
CB="${API}/functions/v1/lipa-na-mpesa-callback"
STAMP=$(date +%s)
EMAIL="stk-e2e-${STAMP}@${PROBE_DOMAIN:-daftari.test}"
PASSWORD="Pr0be-${STAMP}-Aa1!"
CK_BAD="ws_BAD_${STAMP}"; CK_GOOD="ws_GOOD_${STAMP}"

keys_json=$(supabase projects api-keys --project-ref "$REF" --output json 2>/dev/null)
pick() { printf '%s' "$keys_json" | node -e '
let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
  const k=JSON.parse(s); const f=Array.isArray(k)?k:(k.data??k);
  const e=(f.find?.(x=>x.name===process.argv[1]) ?? f.find?.(x=>x.role===process.argv[1]));
  process.stdout.write(e?.api_key ?? e?.key ?? "");});' "$1"; }
ANON=$(pick anon); SERVICE=$(pick service_role)

field() { printf '%s' "$1" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const o=JSON.parse(s)[0]||{};process.stdout.write(String(o[process.argv[1]]??"MISSING"))}catch{process.stdout.write("UNPARSEABLE")}})' "$2"; }
fail=0
assert() { if [[ "$3" == "$2" ]]; then echo "  OK   $1 = $3"; else echo "  FAIL $1 = '$3', expected '$2'"; fail=1; fi; }

# A real Daraja callback: the parser reads Amount from CallbackMetadata.Item[].
daraaja_post() { # $1 checkout, $2 amount
  curl -s -o /dev/null -w '%{http_code}' -X POST "$CB" -H 'Content-Type: application/json' -d "{
    \"Body\":{\"stkCallback\":{
      \"CheckoutRequestID\":\"$1\",\"ResultCode\":0,\"ResultDesc\":\"Success\",
      \"CallbackMetadata\":{\"Item\":[
        {\"Name\":\"Amount\",\"Value\":$2},
        {\"Name\":\"MpesaReceiptNumber\",\"Value\":\"RCP-${STAMP}-$2\"},
        {\"Name\":\"TransactionDate\",\"Value\":\"2026-09-26T08:00:00Z\"},
        {\"Name\":\"PhoneNumber\",\"Value\":\"0700000000\"}]}}}}"
}

seed() { # $1 checkout, $2 local, $3 amount
  curl -s -o /dev/null -X POST "${API}/rest/v1/daftari_stk_requests" \
    -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" -H 'Content-Type: application/json' \
    -d "{\"checkout_request_id\":\"$1\",\"local_id\":\"$2\",\"user_id\":\"${USERID}\",\"amount\":$3,\"phone\":\"0700000000\",\"account_reference\":\"Test Vendor\",\"status\":\"PENDING\"}"
}

# as_user <table> [select] [filter]
#
# The filter argument used to be accepted and then silently dropped, so every
# call site that passed one ("checkout_request_id=eq.${CK_GOOD}") was in fact
# querying the whole table and taking whichever row came back first. That made
# "the request is marked PAID" order-dependent: it passed or failed depending on
# whether Postgres happened to return the PAID row or a PENDING one first. It
# only surfaced once another branch added more PENDING rows for the same user.
# An assertion that reads an arbitrary row is not an assertion.
as_user() {
  local table="$1" select="${2:-*}" filter="${3:-}" query="select=${2:-*}"
  if [[ -n "$filter" ]]; then query="${query}&${filter}"; fi
  curl -s "${API}/rest/v1/${table}?${query}" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}"
}

echo "==> creating a customer"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"email_confirm\":true}"
TOKEN=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
USERID=$(curl -s "${API}/auth/v1/user" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).id??"")}catch{}})')
[[ -n "$TOKEN" && -n "$USERID" ]] || { echo "FAIL: no user identity"; exit 1; }

echo
echo "########## BRANCH 1: amount mismatch must be refused and visible ##########"
seed "$CK_BAD" "local-bad-${STAMP}" 100
code=$(daraaja_post "$CK_BAD" 999)
assert "callback is always ACKed so Safaricom stops retrying" "200" "$code"

rows=$(as_user daftari_stk_callbacks "checkout_request_id,ignore_reason,user_id")
assert "the customer can see their own refusal" "$CK_BAD" "$(field "$rows" checkout_request_id)"
assert "and the reason is specific" "AMOUNT_MISMATCH" "$(field "$rows" ignore_reason)"
assert "and it is owned by them" "$USERID" "$(field "$rows" user_id)"

h=$(as_user stk_health)
assert "health counts their refusal" "1" "$(field "$h" ignored_callbacks)"
assert "health shows NO income was booked" "0" "$(field "$h" income_without_request)"

r=$(as_user daftari_stk_requests "status" "checkout_request_id=eq.${CK_BAD}")
assert "the request stays unpaid" "PENDING" "$(field "$r" status)"

echo
echo "########## BRANCH 2: exact amount must settle and book income ##########"
seed "$CK_GOOD" "local-good-${STAMP}" 100
code=$(daraaja_post "$CK_GOOD" 100)
assert "callback ACKed" "200" "$code"

r=$(as_user daftari_stk_requests "status,mpesa_code" "checkout_request_id=eq.${CK_GOOD}")
assert "the request is marked PAID" "PAID" "$(field "$r" status)"
assert "with the real receipt" "RCP-${STAMP}-100" "$(field "$r" mpesa_code)"

tx=$(as_user daftari_transactions "amount,source" "local_id=eq.local-good-${STAMP}")
assert "income of 100 was booked" "100" "$(field "$tx" amount)"
assert "sourced from daraja" "daraja" "$(field "$tx" source)"

echo
echo "########## BRANCH 3: the customer has no settlement authority ##########"
st=$(curl -s -o /dev/null -w '%{http_code}' -X PATCH "${API}/rest/v1/daftari_stk_requests?checkout_request_id=eq.${CK_BAD}" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -d '{"status":"PAID"}')
if [[ "$st" == 401 || "$st" == 403 ]]; then echo "  OK   marking a request PAID denied ($st)"; else echo "  FAIL got $st"; fail=1; fi

st=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/rest/v1/daftari_stk_callbacks" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d "{\"checkout_request_id\":\"forged\",\"verdict\":\"PAID\",\"ignore_reason\":null,\"mpesa_code\":\"X\",\"amount\":1}")
if [[ "$st" == 401 || "$st" == 403 ]]; then echo "  OK   forging an audit row denied ($st)"; else echo "  FAIL got $st"; fail=1; fi

st=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "${API}/rest/v1/daftari_stk_requests?checkout_request_id=eq.${CK_GOOD}" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOKEN}")
if [[ "$st" == 401 || "$st" == 403 ]]; then echo "  OK   deleting a request denied ($st)"; else echo "  FAIL got $st"; fail=1; fi

echo
echo "########## BRANCH 4: an unconfirmed payment must be VISIBLE when the ##########"
echo "########## device gives up -- not 25 minutes later                            ##########"
#
# The device stops waiting at STK_EXPIRE_AFTER_MS and tells the vendor the
# payment failed. If the view's stale_pending threshold is later than that, the
# operator screen reads "all clear" for the whole window in which a payer could
# have been charged and the callback lost. That was the bug: 5 minutes on the
# device, 30 minutes in the view.
#
# The threshold is read from constants.ts rather than hardcoded here, so the two
# sides are asserted against each other. A row one minute PAST the device's
# give-up point must be flagged, and one minute before it must not be. Raise or
# lower STK_EXPIRE_AFTER_MS without moving the view and this branch fails in the
# direction that matters.
EXPIRE_MS=$(sed -n 's/.*STK_EXPIRE_AFTER_MS:[[:space:]]*\([0-9]*\).*/\1/p' src/lib/constants.ts)
if [[ -z "$EXPIRE_MS" ]]; then
  echo "  FAIL could not read STK_EXPIRE_AFTER_MS from src/lib/constants.ts"
  fail=1
else
  MINS=$(( EXPIRE_MS / 60000 ))
  echo "  device gives up after ${MINS} min (STK_EXPIRE_AFTER_MS=${EXPIRE_MS})"

  seed_aged() { # $1 checkout, $2 local, $3 age in minutes
    local created
    created=$(node -e 'process.stdout.write(new Date(Date.now()-Number(process.argv[1])*60000).toISOString())' "$3")
    curl -s -o /dev/null -X POST "${API}/rest/v1/daftari_stk_requests" \
      -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" -H 'Content-Type: application/json' \
      -d "{\"checkout_request_id\":\"$1\",\"local_id\":\"$2\",\"user_id\":\"${USERID}\",\"amount\":100,\"phone\":\"0700000000\",\"account_reference\":\"Test Vendor\",\"status\":\"PENDING\",\"created_at\":\"${created}\",\"updated_at\":\"${created}\"}"
  }

  # as_user returns raw JSON; field pulls the scalar out of it.
  before=$(field "$(as_user stk_health 'stale_pending')" stale_pending)
  seed_aged "ws_YOUNG_${STAMP}" "local-young-${STAMP}" "$(( MINS - 1 ))"
  mid=$(field "$(as_user stk_health 'stale_pending')" stale_pending)
  if [[ "$mid" == "$before" ]]; then
    echo "  OK   a payment from $((MINS-1)) min ago is not yet flagged"
  else
    echo "  FAIL the view flags at $((MINS-1)) min, before the device gives up (noise, and the two disagree)"
    fail=1
  fi

  seed_aged "ws_STALE_${STAMP}" "local-stale-${STAMP}" "$(( MINS + 1 ))"
  after=$(field "$(as_user stk_health 'stale_pending')" stale_pending)
  if [[ "$after" -gt "$mid" ]]; then
    echo "  OK   a payment the vendor was already told failed IS flagged (${mid} -> ${after})"
  else
    echo "  FAIL a payment ${MINS} min old is still not flagged -- the operator screen would read all clear"
    fail=1
  fi
  echo "       this is the whole point: the payer may be out of pocket and nobody is looking"
fi

echo
echo "########## cleanup ##########"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_transactions?local_id=like.local-*-${STAMP}" -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_stk_callbacks?checkout_request_id=like.ws_*_${STAMP}" -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_stk_requests?checkout_request_id=like.ws_*_${STAMP}" -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}"
curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users" -H "apikey: ${SERVICE}" -H "Authorization: Bearer ${SERVICE}" -H 'Content-Type: application/json' -d "{\"email\":\"${EMAIL}\"}"
echo "  probe data for stamp ${STAMP} removed"

if [[ $fail -ne 0 ]]; then echo; echo "RESULT: reconciliation is NOT trustworthy end-to-end."; exit 1; fi
echo; echo "RESULT: a real callback settles correctly, a wrong one is refused AND visible"
echo "        to the payer, and the payer cannot settle or forge anything."
