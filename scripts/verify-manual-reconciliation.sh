#!/usr/bin/env bash
# Prove the manual-payment reconciliation path is real AND admin-gated.
#
# A customer-paid Till produces no Daraja callback, so this loop is the only
# thing standing between a stranger's money and a stranger's account. It must
# refuse a non-admin at every step, and it must refuse to mark anything paid
# without a receipt.
set -euo pipefail
REF="${1:-rjedivbpldkroffswoyb}"
API="https://${REF}.supabase.co"
STAMP=$(date +%s)

source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"
ANON="$ANON_KEY"
SVC="$SERVICE_KEY"

fail=0
check() { if [[ "$3" == "$2" ]]; then echo "  OK   $1"; else echo "  FAIL $1 (got '$3', want '$2')"; fail=1; fi; }

EMAIL="recon-${STAMP}@daftari.test"
PASS="Rc-${STAMP}-Aa1!"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\",\"email_confirm\":true}"
TOK=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
USER_ID=$(curl -s "${API}/auth/v1/user" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).id??"")}catch{}})')
[[ -n "$TOK" && -n "$USER_ID" ]] || { echo "FAIL: no user identity"; exit 1; }

rpc() { curl -s -X POST "${API}/rest/v1/rpc/$1" -H "apikey: ${ANON}" -H "Authorization: Bearer $2" \
  -H 'Content-Type: application/json' -d "${3:-\{\}}"; }

echo "########## a customer must not be able to run the operator tools ##########"
out=$(rpc admin_subscription_queue "$TOK" '{}')
check "queue is refused for a non-admin" "yes" \
  "$(printf '%s' "$out" | grep -q 'FORBIDDEN' && echo yes || echo no)"

out=$(rpc admin_resolve_subscription "$TOK" "{\"p_request_id\":\"00000000-0000-0000-0000-000000000000\",\"p_resolution\":\"verified\",\"p_mpesa_receipt\":null}")
check "resolve is refused for a non-admin" "yes" \
  "$(printf '%s' "$out" | grep -q 'FORBIDDEN' && echo yes || echo no)"
check "the RPC is reachable at all (not PGRST202)" "yes" \
  "$(printf '%s' "$out" | grep -q 'PGRST202' && echo no || echo yes)"

echo
echo "########## a customer cannot self-approve a request ##########"
REQ=$(curl -s -X POST "${API}/rest/v1/daftari_subscription_requests" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" -H 'Content-Type: application/json' \
  -H 'Prefer: return=representation' \
  -d "{\"user_id\":\"${USER_ID}\",\"tier\":\"biashara\",\"amount_kes\":500,\"status\":\"pending\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0].id??"")}catch{}})')
[[ -n "$REQ" ]] || { echo "FAIL: could not create a request"; exit 1; }
echo "  request ${REQ} created as pending"

# PostgREST reports an RLS-hidden UPDATE as an empty result set, not an error,
# so the property to assert is that no updated row comes back.
out=$(curl -s -X PATCH "${API}/rest/v1/daftari_subscription_requests?id=eq.${REQ}" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" -H 'Content-Type: application/json' \
  -H 'Prefer: return=representation' \
  -d '{"status":"verified"}')
check "direct PATCH to verified updates no row" "yes" \
  "$(printf '%s' "$out" | grep -q '"status":"verified"' && echo no || echo yes)"

st=$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status&id=eq.${REQ}" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0]?.status??"")}catch{process.stdout.write("")}})')
check "the request is still pending" "pending" "$st"

echo
echo "########## the database refuses a verified row with no receipt ##########"
out=$(curl -s -X PATCH "${API}/rest/v1/daftari_subscription_requests?id=eq.${REQ}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d '{"status":"verified"}')
check "service_role cannot bypass the receipt constraint" "yes" \
  "$(printf '%s' "$out" | grep -qi 'verified_requires_receipt' && echo yes || echo no)"

echo
echo "########## a bogus receipt is rejected by the shape constraint ##########"
out=$(curl -s -X PATCH "${API}/rest/v1/daftari_subscription_requests?id=eq.${REQ}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"mpesa_receipt\":\"'; drop table daftari_businesses; --\"}")
check "a non-alphanumeric receipt is refused" "yes" \
  "$(printf '%s' "$out" | grep -qi 'mpesa_receipt_shape' && echo yes || echo no)"

echo
echo "########## one receipt cannot settle two requests ##########"
curl -s -o /dev/null -X PATCH "${API}/rest/v1/daftari_subscription_requests?id=eq.${REQ}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d '{"mpesa_receipt":"QJG7X8K2PZ"}'
REQ2=$(curl -s -X POST "${API}/rest/v1/daftari_subscription_requests" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"${USER_ID}\",\"tier\":\"biashara\",\"amount_kes\":500,\"status\":\"pending\",\"mpesa_receipt\":\"QJG7X8K2PZ\"}")
check "a duplicate receipt is refused" "yes" \
  "$(printf '%s' "$REQ2" | grep -qi 'subscription_receipt_unique\|duplicate\|conflict' && echo yes || echo no)"

echo
echo "########## cleanup (negative path) ##########"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_subscription_requests?id=eq.${REQ}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${USER_ID}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
echo "  removed probe request and throwaway user"


# ─────────────────────────────────────────────────────────────────────────────
# POSITIVE PATH
#
# Everything above proves the tool refuses. Refusal alone is not evidence the
# tool works, so this section provisions a TEMPORARY admin, closes a real
# pending request through the real RPC, and then removes the admin again.
# A real deployment provisions an admin by EMAIL via scripts/bootstrap-admin.sh;
# nothing is escalated implicitly here.
# ─────────────────────────────────────────────────────────────────────────────
echo
echo "########## an admin can actually close a payment ##########"
ADMIN_EMAIL="recon-admin-${STAMP}@daftari.test"
ADMIN_PASS="Ad-${STAMP}-Aa1!"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASS}\",\"email_confirm\":true}"
ADMIN_ID=$(curl -s "${API}/auth/v1/admin/users?limit=200" -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const u=JSON.parse(s).users??JSON.parse(s);const m=u.find(x=>x.email===process.argv[1]);process.stdout.write(m?.id??"")}catch{}})' "$ADMIN_EMAIL")
ATOK=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASS}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
curl -s -o /dev/null -X POST "${API}/rest/v1/daftari_admin_users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"${ADMIN_ID}\"}"
[[ -n "$ATOK" && -n "$ADMIN_ID" ]] || { echo "FAIL: could not provision a temporary admin"; exit 1; }

# Its own payer: the negative path already deleted the first throwaway user, and
# the request table references auth.users, so reusing that id would fail the FK.
PAYER_EMAIL="recon-payer-${STAMP}@daftari.test"
PAYER_PASS="Py-${STAMP}-Aa1!"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${PAYER_EMAIL}\",\"password\":\"${PAYER_PASS}\",\"email_confirm\":true}"
PAYER_ID=$(curl -s "${API}/auth/v1/admin/users?limit=200" -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const u=JSON.parse(s).users??JSON.parse(s);const m=u.find(x=>x.email===process.argv[1]);process.stdout.write(m?.id??"")}catch{}})' "$PAYER_EMAIL")
[[ -n "$PAYER_ID" ]] || { echo "FAIL: could not create the payer"; exit 1; }

PEND=$(curl -s -X POST "${API}/rest/v1/daftari_subscription_requests" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -H 'Prefer: return=representation' \
  -d "{\"user_id\":\"${PAYER_ID}\",\"tier\":\"biashara_plus\",\"amount_kes\":1500,\"status\":\"pending\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0].id??"")}catch{}})')
[[ -n "$PEND" ]] || { echo "FAIL: could not create the pending request"; exit 1; }
echo "  pending request ${PEND} (1500 KES, biashara_plus)"

q=$(rpc admin_subscription_queue "$ATOK" '{}')
check "the queue shows the pending request" "yes" \
  "$(printf '%s' "$q" | grep -q "$PEND" && echo yes || echo no)"
check "the queue names the payer" "yes" \
  "$(printf '%s' "$q" | grep -q "$PAYER_EMAIL" && echo yes || echo no)"

out=$(rpc admin_resolve_subscription "$ATOK" "{\"p_request_id\":\"${PEND}\",\"p_resolution\":\"verified\",\"p_mpesa_receipt\":null}")
check "verifying with no receipt is refused" "yes" \
  "$(printf '%s' "$out" | grep -q 'INVALID' && echo yes || echo no)"

out=$(rpc admin_resolve_subscription "$ATOK" "{\"p_request_id\":\"${PEND}\",\"p_resolution\":\"verified\",\"p_mpesa_receipt\":\"KQR9T2M4XB\"}")
check "verifying WITH a receipt succeeds" "verified" \
  "$(printf '%s' "$out" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).status??"")}catch{process.stdout.write("")}})')"

row=$(curl -s "${API}/rest/v1/daftari_subscription_requests?select=status,mpesa_receipt,resolved_by&id=eq.${PEND}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}")
check "the row is now verified" "verified" \
  "$(printf '%s' "$row" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0].status??"")}catch{}})')"
check "the receipt is stored" "KQR9T2M4XB" \
  "$(printf '%s' "$row" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0].mpesa_receipt??"")}catch{}})')"
check "the decision is attributed to the admin" "$ADMIN_ID" \
  "$(printf '%s' "$row" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s)[0].resolved_by??"")}catch{}})')"

out=$(rpc admin_resolve_subscription "$ATOK" "{\"p_request_id\":\"${PEND}\",\"p_resolution\":\"rejected\",\"p_mpesa_receipt\":null}")
check "re-resolving an already-decided request is refused" "yes" \
  "$(printf '%s' "$out" | grep -q 'CONFLICT' && echo yes || echo no)"

echo
echo "########## cleanup ##########"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_subscription_requests?id=eq.${PEND}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_admin_users?user_id=eq.${ADMIN_ID}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${ADMIN_ID}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${PAYER_ID}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
echo "  removed probe requests, temporary admin, throwaway users"

echo
[ "$fail" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"
exit "$fail"
