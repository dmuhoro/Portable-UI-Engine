#!/usr/bin/env bash
# =============================================================
# Prove that a VERIFIED PAYMENT ACTUALLY GRANTS THE PLAN.
#
# Why this script exists:
#   Before migration 20260926030000, a vendor could pay, have the receipt
#   verified as correct, and still not get the plan — daftari_subscriptions
#   was written only by the signup trigger. Both settlement functions stopped
#   at status='verified'. This is the proof that the gap is closed.
#
# It deliberately drives the REAL paths, not a stand-in:
#   - the vendor signs in and files their own request (the app's RLS path)
#   - an ADMIN resolves it through admin_resolve_subscription() over RPC
#   - the automated path runs through settle_subscription_c2b()
#   - entitlement is read back through user_subscription, the view the app uses
#
# A test of the trigger alone would prove nothing. The trigger is only useful
# if the functions that verify payments actually trip it, so that is what this
# asserts.
#
# Usage: scripts/verify-subscription-activation.sh [project_ref]
# Exits non-zero on the first failed assertion. Creates and deletes its own
# throwaway users; safe to run against production.
# =============================================================
set -euo pipefail

REF="${SUPABASE_PROJECT_REF:-${1:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
STAMP=$(date +%s)

source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"
: "${ANON_KEY:?anon key unavailable}" "${SERVICE_KEY:?service key unavailable}"

PASS=0
FAIL=0
ok()   { PASS=$((PASS+1)); echo "  PASS  $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL  $1"; }
check() { if [ "$2" = "$3" ]; then ok "$1 ($3)"; else bad "$1 -- expected '$3', got '$2'"; fi; }

# Read a top-level field out of a JSON blob on stdin.
field() { node -e '
let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
  let v="";
  try { const p=JSON.parse(s); const a=Array.isArray(p)?p:[p];
        const r=a[0]; v = r==null ? "" : (process.argv[1].includes(".")==false
          ? r[process.argv[1]] : process.argv[1].split(".").reduce((o,k)=>o?.[k],r));
  } catch { v=""; }
  process.stdout.write(v===null||v===undefined ? "" : String(v));
});' "$1"; }

# POST/GET JSON helper.
#
# The apikey header must stay the ANON key even when the caller is a signed-in
# user: putting the user token in apikey makes PostgREST answer 401 "Invalid
# API key". That 401 looks exactly like a successful refusal, so an earlier
# draft of this script reported three security assertions as PASS when the
# request had never reached the permission check at all. The role comes from
# the Authorization bearer token; the service key is used for both when the
# caller IS the service role.
req() { # method path token [json]
  local m="$1" p="$2" tok="$3" data="${4:-}" apikey="${ANON_KEY}"
  [ "$tok" = "$SERVICE_KEY" ] && apikey="${SERVICE_KEY}"
  if [ -n "$data" ]; then
    curl -s -w '\n%{http_code}' -X "$m" "${API}${p}" \
      -H "apikey: ${apikey}" -H "Authorization: Bearer ${tok}" \
      -H 'Content-Type: application/json' -d "$data"
  else
    curl -s -w '\n%{http_code}' -X "$m" "${API}${p}" \
      -H "apikey: ${apikey}" -H "Authorization: Bearer ${tok}"
  fi
}

# A refusal must be a real authorization decision. HTTP 401 means the request
# never got past authentication, so treating it as "the wall held" would let a
# broken script certify a breach.
refused() { # label raw_response expected_substring
  local label="$1" out="$2" want="$3" c b
  c=$(code "$out"); b=$(body "$out")
  if [ "$c" = "401" ] || [ "$c" = "403" ] && [ "$c" = "401" ]; then
    bad "${label} -- HTTP ${c} means the request was not authenticated at all, not that it was refused"
    return
  fi
  if [ "$c" = "200" ] || [ "$c" = "201" ] || [ "$c" = "204" ]; then
    bad "${label} -- the call SUCCEEDED (HTTP ${c}); this is the breach"
    return
  fi
  if printf '%s' "$b" | grep -q "$want"; then
    ok "${label} (HTTP ${c}, reason: ${want})"
  else
    bad "${label} -- HTTP ${c} but body did not contain '${want}': ${b}"
  fi
}

# Field N (1-based) of a "a|b|c" state string.
sf() { printf '%s' "$2" | cut -d'|' -f"$1"; }
body() { printf '%s' "$1" | sed '$d'; }
code() { printf '%s' "$1" | tail -n1; }

# Insert that returns the created row. A bare POST gets 201 with an EMPTY body
# unless representation is requested, which is how the first draft ended up
# holding an empty request id and then testing "does uuid '' exist?".
ins() { # path token json
  curl -s -w '\n%{http_code}' -X POST "${API}$1" \
    -H "apikey: ${ANON_KEY}" -H "Authorization: Bearer $2" \
    -H 'Content-Type: application/json' -H 'Prefer: return=representation' -d "$3"
}

mkuser() { # email -> "token userid"
  local email="$1" pass="$2" out
  out=$(req POST "/auth/v1/admin/users" "$SERVICE_KEY" \
    "{\"email\":\"${email}\",\"password\":\"${pass}\",\"email_confirm\":true}")
  [ "$(code "$out")" = "200" ] || [ "$(code "$out")" = "201" ] \
    || { echo "FATAL: could not create ${email}: $(body "$out")" >&2; exit 1; }
  local uid tok
  uid=$(curl -s "${API}/auth/v1/admin/users?limit=1000" \
    -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" \
    | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
        const b=JSON.parse(s); const us=b.users??b;
        const m=us.find(u=>(u.email??"").toLowerCase()===process.argv[1].toLowerCase());
        process.stdout.write(m?.id??"");});' "$email")
  tok=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON_KEY}" \
    -H 'Content-Type: application/json' -d "{\"email\":\"${email}\",\"password\":\"${pass}\"}" \
    | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
  [ -n "$uid" ] && [ -n "$tok" ] || { echo "FATAL: no identity for ${email}" >&2; exit 1; }
  echo "${tok} ${uid}"
}

sub_state() { # userid -> "tier|status|trial_ends_at|period_end|is_active"
  curl -s "${API}/rest/v1/user_subscription?select=tier,status,trial_ends_at,current_period_end,is_active&user_id=eq.$1" \
    -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
      let o={};
      try{const a=JSON.parse(s); if(Array.isArray(a)&&a[0])o=a[0];}catch{}
      process.stdout.write([o.tier??"none",o.status??"none",
        o.trial_ends_at===null||o.trial_ends_at===undefined?"null":String(o.trial_ends_at),
        o.current_period_end??"null",String(o.is_active??"")].join("|"));});'
}

ADMIN_EMAIL="subadmin-${STAMP}@daftari.test"
VENDOR_EMAIL="subvendor-${STAMP}@daftari.test"
ADMIN_PASS="Sa-${STAMP}-Aa1!"
VENDOR_PASS="Sv-${STAMP}-Aa1!"

echo "=== subscription activation proof against ${REF} ==="
read -r ATOK AUID <<< "$(mkuser "$ADMIN_EMAIL" "$ADMIN_PASS")"
read -r VTOK VUID <<< "$(mkuser "$VENDOR_EMAIL" "$VENDOR_PASS")"
echo "  admin=${AUID}  vendor=${VUID}"

cleanup() {
  curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${AUID}" \
    -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}"
  curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${VUID}" \
    -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}"
  echo "  (throwaway users deleted)"
}
trap cleanup EXIT

# Promote the admin via the service key, the same route bootstrap-admin.sh uses.
promo=$(req POST "/rest/v1/daftari_admin_users" "$SERVICE_KEY" "{\"user_id\":\"${AUID}\"}")
if ! { [ "$(code "$promo")" = "201" ] || [ "$(code "$promo")" = "204" ]; }; then
  bad "admin promotion -- $(code "$promo") $(body "$promo")"
else
  ok "admin promoted (is_admin() gate has a real admin to test against)"
fi
ia=$(req POST "/rest/v1/rpc/is_admin" "$ATOK" '{}')
check "is_admin() for the promoted user" "$(body "$ia")" "true"

echo
echo "--- 1. starting state: signup trial row exists ---"
S0=$(sub_state "$VUID")
check "vendor starts on the msingi tier" "$(sf 1 "$S0")" "msingi"
check "vendor starts in trial status"   "$(sf 2 "$S0")" "trial"
check "trial is active"                "$(sf 5 "$S0")" "true"
if [ "$(sf 3 "$S0")" != "null" ] && [ -n "$(sf 3 "$S0")" ]; then
  ok "a real trial end date is set ($(sf 3 "$S0" | cut -c1-10))"
else
  bad "signup trial row has no trial_ends_at"
fi

echo
echo "--- 2. the vendor files their own upgrade request (the app's real path) ---"
r1=$(ins "/rest/v1/daftari_subscription_requests" "$VTOK" \
  "{\"user_id\":\"${VUID}\",\"tier\":\"biashara\",\"amount_kes\":300}")
[ "$(code "$r1")" = "201" ] || bad "vendor could not file a request -- $(code "$r1") $(body "$r1")"
REQ1=$(body "$r1" | field id)
[ -n "$REQ1" ] && ok "request filed by the vendor (id=${REQ1})"
check "request is still pending" "$(body "$r1" | field status)" "pending"
check "request has NOT yet granted the tier" "$(sub_state "$VUID" | cut -d'|' -f1)" "msingi"

echo
echo "--- 3. a vendor can never approve their own payment ---"
selfres=$(req POST "/rest/v1/rpc/admin_resolve_subscription" "$VTOK" \
  "{\"p_request_id\":\"${REQ1}\",\"p_resolution\":\"verified\",\"p_mpesa_receipt\":\"SELFPROOF1\"}")
refused "vendor approving their own payment" "$selfres" "FORBIDDEN"
check "and the request is still pending afterwards" \
  "$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status&id=eq.${REQ1}" \
     -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" | field status)" "pending"

echo
echo "--- 4. THE GAP: admin verifies the payment -> the plan must be granted ---"
ver=$(req POST "/rest/v1/rpc/admin_resolve_subscription" "$ATOK" \
  "{\"p_request_id\":\"${REQ1}\",\"p_resolution\":\"verified\",\"p_mpesa_receipt\":\"RCP1A2B3C4D\"}")
check "admin verification succeeded" "$(code "$ver")" "200"
STATE=$(sub_state "$VUID")
check "tier granted"            "$(printf '%s' "$STATE" | cut -d'|' -f1)" "biashara"
check "status is active"        "$(printf '%s' "$STATE" | cut -d'|' -f2)" "active"
check "trial is closed out"     "$(printf '%s' "$STATE" | cut -d'|' -f3)" "null"
check "user_subscription says active" "$(printf '%s' "$STATE" | cut -d'|' -f5)" "true"
PEND=$(printf '%s' "$STATE" | cut -d'|' -f4)
if [ "$PEND" != "null" ] && [ -n "$PEND" ]; then
  DAYS=$(node -e 'const d=(new Date(process.argv[1])-Date.now())/86400000;process.stdout.write(String(Math.round(d)))' "$PEND")
  if [ "$DAYS" -ge 27 ] && [ "$DAYS" -le 31 ]; then
    ok "paid period ends ~1 month out (${DAYS} days)"
  else
    bad "paid period is ${DAYS} days out, expected ~30"
  fi
else
  bad "no current_period_end was set on a paid subscription"
fi

echo
echo "--- 5. the audit view agrees payment and entitlement match ---"
# The view exposes the request's primary key as request_id (not id); filtering
# on a column the view does not have returns an error body, not an empty list,
# so a wrong column name here reads as "the audit row is missing".
aud=$(curl -s "${API}/rest/v1/subscription_activation_audit?select=requested_tier,granted_tier,granted_status,entitlement_matches_payment&request_id=eq.${REQ1}" \
  -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}")
if printf '%s' "$aud" | grep -q '"code":"PGRST'; then
  bad "audit view query errored: ${aud}"
fi
check "audit: requested == granted tier" "$(printf '%s' "$aud" | field granted_tier)" "biashara"
check "audit: entitlement matches payment" "$(printf '%s' "$aud" | field entitlement_matches_payment)" "true"

echo
echo "--- 6. a REJECTED claim must never grant anything ---"
r2=$(ins "/rest/v1/daftari_subscription_requests" "$VTOK" \
  "{\"user_id\":\"${VUID}\",\"tier\":\"biashara_plus\",\"amount_kes\":700}")
REQ2=$(body "$r2" | field id)
[ -n "$REQ2" ] && ok "second request filed (id=${REQ2})" || bad "second request was not created: $(body "$r2")"
rej=$(req POST "/rest/v1/rpc/admin_resolve_subscription" "$ATOK" \
  "{\"p_request_id\":\"${REQ2}\",\"p_resolution\":\"rejected\",\"p_mpesa_receipt\":null}")
RC=$(code "$rej")
if [ "$RC" = "200" ] || [ "$RC" = "201" ]; then
  ok "rejection recorded (HTTP ${RC})"
else
  bad "rejection failed (HTTP ${RC}): $(body "$rej")"
fi
check "the rejected request really is on file" \
  "$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status&id=eq.${REQ2}" \
     -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" | field status)" "rejected"
check "rejected claim did NOT change the tier" "$(sub_state "$VUID" | cut -d'|' -f1)" "biashara"
check "rejected claim did NOT change the status" "$(sub_state "$VUID" | cut -d'|' -f2)" "active"

echo
echo "--- 7. THE AUTOMATED PATH: C2B settlement must also grant the plan ---"
r3=$(ins "/rest/v1/daftari_subscription_requests" "$VTOK" \
  "{\"user_id\":\"${VUID}\",\"tier\":\"biashara_plus\",\"amount_kes\":700}")
REQ3=$(body "$r3" | field id)
TRANS="C2B${STAMP}"
note=$(ins "/rest/v1/daftari_c2b_notifications" "$SERVICE_KEY" \
  "{\"trans_id\":\"${TRANS}\",\"receipt_no\":\"C2BRCP${STAMP}\",\"amount\":700,\"payer_msisdn\":\"254700000000\",\"account_reference\":\"${VUID}\",\"safaricom_confirmed\":true,\"verdict\":\"SETTLED\",\"settled_request_id\":\"${REQ3}\",\"raw_payload\":{\"proof\":\"activation drill\"}}")
[ "$(code "$note")" = "201" ] || bad "could not stage the confirmed C2B notification -- $(body "$note")"
settle=$(req POST "/rest/v1/rpc/settle_subscription_c2b" "$SERVICE_KEY" \
  "{\"p_request_id\":\"${REQ3}\",\"p_trans_id\":\"${TRANS}\"}")
SC=$(code "$settle")
if [ "$SC" = "200" ] || [ "$SC" = "201" ]; then
  ok "C2B settlement succeeded (HTTP ${SC})"
else
  bad "C2B settlement failed (HTTP ${SC}): $(body "$settle")"
fi
check "C2B marked the request verified" \
  "$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status&id=eq.${REQ3}" \
     -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" | field status)" "verified"
check "C2B granted the paid tier" "$(sub_state "$VUID" | cut -d'|' -f1)" "biashara_plus"
check "C2B left the plan active" "$(sub_state "$VUID" | cut -d'|' -f2)" "active"

echo
echo "--- 8. an unconfirmed notification must still not move money ---"
r4=$(ins "/rest/v1/daftari_subscription_requests" "$VTOK" \
  "{\"user_id\":\"${VUID}\",\"tier\":\"msingi\",\"amount_kes\":1}")
REQ4=$(body "$r4" | field id)
TRANS2="UNCONF${STAMP}"
ins "/rest/v1/daftari_c2b_notifications" "$SERVICE_KEY" \
  "{\"trans_id\":\"${TRANS2}\",\"receipt_no\":\"UNCONFRCP${STAMP}\",\"safaricom_confirmed\":false,\"verdict\":\"UNVERIFIED\",\"raw_payload\":{\"proof\":\"unconfirmed\"}}" >/dev/null
unc=$(req POST "/rest/v1/rpc/settle_subscription_c2b" "$SERVICE_KEY" \
  "{\"p_request_id\":\"${REQ4}\",\"p_trans_id\":\"${TRANS2}\"}")
refused "unconfirmed notification settling a request" "$unc" "NOT_CONFIRMED"
check "unconfirmed request stays pending" \
  "$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status&id=eq.${REQ4}" \
     -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" | field status)" "pending"

echo
echo "--- 9. re-saving a verified request must not re-charge the period ---"
SENTINEL="2099-01-01T00:00:00+00:00"
curl -s -o /dev/null -X PATCH "${API}/rest/v1/daftari_subscriptions?user_id=eq.${VUID}" \
  -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" \
  -H 'Content-Type: application/json' -d "{\"current_period_end\":\"${SENTINEL}\"}"
req PATCH "/rest/v1/daftari_subscription_requests?id=eq.${REQ3}" "$SERVICE_KEY" \
  '{"status":"verified"}' >/dev/null
check "period untouched by a non-transition update" \
  "$(sub_state "$VUID" | cut -d'|' -f4 | cut -c1-10)" "2099-01-01"

echo
echo "--- 10. the RLS wall still stands: no client self-grants ---"
gr=$(req POST "/rest/v1/daftari_subscriptions" "$VTOK" \
  "{\"user_id\":\"${VUID}\",\"tier\":\"biashara_plus\",\"status\":\"active\"}")
refused "client INSERT granting itself a subscription" "$gr" "row-level security"
# Try to DOWNGRADE to the free tier. The row is on a paid tier at this point,
# so a change would be unmistakable. Asserting the HTTP code is not enough:
# a PATCH that matches zero rows also answers 204, so "204" is not evidence of
# anything. The only evidence is the tier afterwards.
BEFORE=$(sf 1 "$(sub_state "$VUID")")
req PATCH "/rest/v1/daftari_subscriptions?user_id=eq.${VUID}" "$VTOK" \
  '{"tier":"msingi"}' >/dev/null
AFTER=$(sf 1 "$(sub_state "$VUID")")
check "client UPDATE could not change the tier (${BEFORE} -> ${AFTER})" "$AFTER" "$BEFORE"
req PATCH "/rest/v1/daftari_subscriptions?user_id=eq.${VUID}" "$SERVICE_KEY" \
  "{\"current_period_end\":null}" >/dev/null

echo
echo "==================================================="
echo "  passed: ${PASS}   failed: ${FAIL}"
echo "==================================================="
[ "$FAIL" -eq 0 ] || exit 1
