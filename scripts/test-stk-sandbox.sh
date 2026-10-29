#!/usr/bin/env bash
# Is the Daraja STK sandbox path actually WORKING right now?
#
# THIS SCRIPT IS A GATE, NOT A SMOKE TEST. IT IS BUILT TO FAIL.
# ------------------------------------------------------------------------
# The failure mode this exists to prevent is a green tick that means "we called
# an endpoint". `supabase functions list` being green, secrets existing, and
# OAuth returning a token all prove the wiring is present — none of them prove
# Safaricom will accept a push for THIS merchant. In this repo's history the
# credentials were all present, OAuth succeeded, and every push was still
# refused with `400.002.02 Invalid TransactionType`, because the shortcode and
# product were not a real Daraja sandbox product.
#
# So the exit code here is the answer to "can we take a vendor's money?", and it
# is non-zero unless an STK push is accepted by Safaricom. There is no branch
# in this file that reports success without a CheckoutRequestID coming back
# from Safaricom. When the configuration is wrong, the correct output is FAIL
# and the correct exit code is 1 — that is this script working, not failing.
#
# WHAT IT CHECKS, IN ORDER (cheapest and most decisive first)
#   1. Secrets present at all                     -> daraja-preflight.sh
#   2. Resolved wiring, read from INSIDE the function (env, apiBase,
#      merchant kind, shortcode, passkey shape)  -> stk-push {"diagnostic":true}
#   3. A live OAuth token can be minted
#   4. Safaricom ACCEPTS a real STK push and returns a CheckoutRequestID
#   5. We recorded a PENDING request row for it
#
# Step 2 is not decoration. Supabase secrets are write-only, so a wrong
# DARAJA_ENV or a till-vs-paybill mismatch is invisible from the shell; the
# function is the only place that can report what it resolved. When step 2
# warns, the script refuses to spend a push attempt on a request that cannot
# work, and says exactly which secret to fix.
#
# WHAT IT DOES NOT DO
#   It does NOT wait for you to approve the prompt on your phone, and it does
#   NOT prove settlement. An accepted STK push only means Safaricom is willing
#   to prompt you. For the full loop — prompt, approval, real callback, real
#   credit in the books — use:
#       scripts/run-stk-drill.sh <msisdn> [amount]
#   and keep this script for the cheap, repeatable "is Daraja sane?" question.
#
# Usage: scripts/test-stk-sandbox.sh [project_ref]
#   project_ref   defaults to $SUPABASE_PROJECT_REF, then the production ref
#
# Exit codes:  0 = Safaricom accepted a push   1 = FAIL (see the reason)
set -uo pipefail

REF="${SUPABASE_PROJECT_REF:-${1:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
STAMP=$(date +%s)
EMAIL="stk-gate-${STAMP}@daftari.test"
PASSWORD="Gat3-${STAMP}-Aa1!"
MSISDN="${STK_TEST_MSISDN:-254708374149}"

source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"
ANON="$ANON_KEY"; SVC="$SERVICE_KEY"

FAILURES=0
step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; FAILURES=$((FAILURES + 1)); }

cleanup() {
  [[ -n "${TOK:-}" && -n "${USER_ID:-}" ]] && curl -s -o /dev/null \
    -X DELETE "${API}/rest/v1/daftari_admin_users?user_id=eq.${USER_ID}" \
    -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
  [[ -n "${USER_ID:-}" ]] && curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${USER_ID}" \
    -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
}
trap cleanup EXIT

# ── 1. secrets present ──────────────────────────────────────────────────────
step "1/5  credentials present"
if ./scripts/daraja-preflight.sh "$REF" >/dev/null 2>&1; then
  pass "all Daraja secrets are set"
else
  ./scripts/daraja-preflight.sh "$REF" || true
  fail "credentials are incomplete — see the preflight output above"
  echo
  echo "GATE FAILED at step 1. Not attempting a push."
  exit 1
fi

# ── 2. resolved wiring, from inside the function ────────────────────────────
step "2/5  resolved wiring (as the edge function sees it)"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"email_confirm\":true}"
TOK=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" \
  -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
USER_ID=$(curl -s "${API}/auth/v1/user" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).id??"")}catch{}})')
if [[ -z "$TOK" || -z "$USER_ID" ]]; then
  fail "could not provision a throwaway admin to read the diagnostic"
  exit 1
fi
curl -s -o /dev/null -X POST "${API}/rest/v1/daftari_admin_users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"${USER_ID}\"}"

DIAG=$(curl -s -X POST "${API}/functions/v1/stk-push" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" -H 'Content-Type: application/json' \
  -d '{"diagnostic":true}')

DIAG_OUTCOME=$(printf '%s' "$DIAG" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).outcome??"")}catch{process.stdout.write("unparseable")}})')
DIAG_WARNINGS=$(printf '%s' "$DIAG" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(String((JSON.parse(s).warnings??[]).length))}catch{process.stdout.write("0")}})')
DIAG_ROUTING=$(printf '%s' "$DIAG" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const d=JSON.parse(s);process.stdout.write(d.routing?"ok":"missing")}catch{process.stdout.write("missing")}})')
DIAG_PASSKEY_LEN=$(printf '%s' "$DIAG" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(String(JSON.parse(s).credentials?.passkeyLength??"0"))}catch{process.stdout.write("0")}})')

if [[ "$DIAG_OUTCOME" != "ok" ]]; then
  fail "the diagnostic endpoint refused: ${DIAG:0:200}"
  exit 1
fi
if [[ "$DIAG_ROUTING" != "ok" ]]; then
  fail "the function cannot resolve its Daraja routing — merchantKind is probably unset, which is a deliberate fail-closed refusal"
  exit 1
fi
pass "routing resolves and the function is willing to push"
printf '%s\n' "$DIAG" | node -e '
let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
  const d=JSON.parse(s); const r=d.routing??{}; const c=d.credentials??{};
  const p=(l,v)=>console.log("        "+(l+"                ").slice(0,16)+v);
  p("env",d.env); p("apiBase",d.apiBase); p("merchantKind",d.merchantKind);
  p("shortcode",r.businessShortCode); p("partyB",r.partyB); p("txnType",r.transactionType);
  p("passkey",c.passkeyPresent?c.passkeyLength+" chars":"MISSING");
  (d.warnings??[]).forEach(w=>console.log("        !! "+w));
})'

# A warning here is a refusal to continue, not a footnote. A passkey of the
# wrong length cannot possibly be accepted by Daraja, so spending a live push
# on it would only produce a confusing 400 further down.
if [[ "$DIAG_WARNINGS" != "0" ]]; then
  fail "the function reported ${DIAG_WARNINGS} wiring warning(s) above — Safaricom cannot accept a push in this state"
  echo
  echo "GATE FAILED at step 2. Fix the flagged secret, then re-run:"
  echo "  ./scripts/daraja-diagnostics.sh          # shows resolved wiring"
  echo "  supabase secrets set --project-ref ${REF} DARAJA_PASSKEY='<32-or-64-char passkey from the Daraja product page>'"
  echo
  echo "Use the EXACT values from the same Daraja sandbox product page for the"
  echo "passkey, the business shortcode and the till. They are issued together"
  echo "and are not interchangeable; do not copy one into the other."
  exit 1
fi
pass "no wiring warnings (passkey is ${DIAG_PASSKEY_LEN} chars)"

# ── 3. live OAuth ───────────────────────────────────────────────────────────
step "3/5  Safaricom OAuth token"
# Deliberately not attempted from here: DARAJA_CLIENT_KEY / DARAJA_CLIENT_SECRET
# are write-only Supabase secrets, so this shell cannot see them and a direct
# OAuth call here would be theatre. OAuth is exercised THROUGH the function
# instead, which means reaching step 4 at all proves a token was minted. A
# separate OAuth check would only re-test the same code path with less context.
pass "exercised by the push in step 4 — the credentials live in the function, not this shell"

# ── 4. the push Safaricom must accept ───────────────────────────────────────
step "4/5  live STK push to ${MSISDN}"

# stk-push mirrors a PENDING request row before it calls Safaricom, and it
# refuses unless that row can be attributed to a business this user owns. So a
# real push needs a real business first. The field names below are the actual
# contract (phone / accountReference / transactionDesc, and businessId compared
# against daftari_businesses.local_id) — verified against the function, because
# guessing them yields a 400 "Unusable phone" that looks exactly like a broken
# Daraja config and is not one.
LOCAL="stk-gate-${STAMP}"
BIZ=$(curl -s -X POST "${API}/rest/v1/daftari_businesses" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" \
  -H 'Content-Type: application/json' -H 'Prefer: return=representation' \
  -d "{\"local_id\":\"${LOCAL}\",\"user_id\":\"${USER_ID}\",\"name\":\"STK Gate ${STAMP}\",\"payment_methods\":[\"till_number\"]}")
BUSINESS_ID=$(printf '%s' "$BIZ" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const o=JSON.parse(s);process.stdout.write(Array.isArray(o)?(o[0]?.id??""):(o?.id??""))}catch{}})')
if [[ -z "$BUSINESS_ID" ]]; then
  fail "could not create the throwaway business, so the push would be refused before it reached Safaricom"
  printf '        %s\n' "${BIZ:0:300}"
  exit 1
fi

PUSH=$(curl -s -w '\n%{http_code}' -X POST "${API}/functions/v1/stk-push" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" -H 'Content-Type: application/json' \
  -d "{\"amount\":1,\"phone\":\"${MSISDN}\",\"accountReference\":\"STK-GATE\",\"transactionDesc\":\"Daftari sandbox gate\",\"businessId\":\"${LOCAL}\",\"localId\":\"${LOCAL}\",\"paymentMethod\":\"till_number\"}")

PUSH_BODY=$(printf '%s' "$PUSH" | sed '$d')
PUSH_CODE=$(printf '%s' "$PUSH" | tail -n1)
PUSH_RESULT=$(printf '%s' "$PUSH_BODY" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).result??"")}catch{process.stdout.write("")}})')
PUSH_CRI=$(printf '%s' "$PUSH_BODY" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).checkoutRequestId??"")}catch{process.stdout.write("")}})')

# A CheckoutRequestID is the ONLY thing that counts as accepted. HTTP 200 alone
# is deliberately not enough: the function returns 200 with result:"FAILED" for
# an upstream refusal, so trusting the status code is exactly how a gate like
# this reports success while no prompt ever reaches a phone.
if [[ -n "$PUSH_CRI" && "$PUSH_RESULT" != "FAILED" ]]; then
  pass "Safaricom ACCEPTED the push — CheckoutRequestID ${PUSH_CRI}"
else
  fail "Safaricom refused the push (HTTP ${PUSH_CODE})"
  printf '        %s\n' "${PUSH_BODY:0:400}"
  echo
  echo "GATE FAILED. This is the script working: Safaricom will not accept a"
  echo "push for this merchant, so a vendor cannot pay right now."
  echo
  echo "  400.002.02 Invalid TransactionType  -> the shortcode / merchant kind"
  echo "      and the product on the Daraja portal are not a matching set."
  echo "      Copy all of them from ONE product page."
  echo "  Invalid passkey / 400 authentication -> the passkey is not the one"
  echo "      issued for that product."
  echo "  INVALID_INPUT / Unusable phone       -> the probe's own phone number"
  echo "      was rejected before Daraja was involved; set STK_TEST_MSISDN to a"
  echo "      real sandbox handset. This is a fault in the GATE, not Daraja."
  echo
  echo "Inspect the resolved wiring with: ./scripts/daraja-diagnostics.sh"
  exit 1
fi

# ── 5. our own PENDING row ──────────────────────────────────────────────────
step "5/5  our PENDING request row"
ROW=$(curl -s "${API}/rest/v1/daftari_stk_requests?select=checkout_request_id,status,amount&checkout_request_id=eq.${PUSH_CRI}" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}")
ROW_OK=$(printf '%s' "$ROW" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const r=JSON.parse(s);process.stdout.write(r.length>0&&r[0].status==="PENDING"?"ok":"missing")}catch{process.stdout.write("missing")}})')
if [[ "$ROW_OK" == "ok" ]]; then
  pass "the push is recorded PENDING and the callback will find it"
  curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_stk_requests?checkout_request_id=eq.${PUSH_CRI}" \
    -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
else
  fail "no PENDING row for ${PUSH_CRI} — a callback for it would be refused as forged"
  printf '        %s\n' "${ROW:0:300}"
fi

echo
if [[ "$FAILURES" -eq 0 ]]; then
  echo "GATE PASSED — Daraja will accept a real STK push."
  echo "This does NOT prove settlement. For the full loop, run:"
  echo "  ./scripts/run-stk-drill.sh ${MSISDN} 1"
  exit 0
fi
echo "GATE FAILED (${FAILURES} check(s)). Daraja is NOT ready to take a payment."
exit 1
