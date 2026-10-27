#!/usr/bin/env bash
# Report the RESOLVED Daraja wiring from inside the edge function.
#
# WHY THIS EXISTS
# ---------------
# Supabase secrets are write-only: `supabase secrets list` prints a SHA hash and
# never the value. So DARAJA_ENV and DARAJA_MERCHANT_KIND — the two values that
# decide which Safaricom API a push hits, and which TransactionType it sends —
# cannot be read back from the shell at all. When a push fails with something
# like "Invalid TransactionType", the only way to tell a wrong-environment push
# from a wrong-product push is to ask the function that can actually see them.
#
# It reports NON-SECRET wiring plus presence/length of credentials. No key,
# secret, passkey or token value is ever returned or printed.
#
# The endpoint is JWT-gated AND admin-gated, so only a provisioned admin can
# read it. This script provisions its OWN throwaway admin rather than signing
# in as a real person, so it needs no password and touches no real account.
#
# Usage: scripts/daraja-diagnostics.sh [project_ref]
set -euo pipefail

REF="${SUPABASE_PROJECT_REF:-${1:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
STAMP=$(date +%s)
EMAIL="daraja-diag-${STAMP}@daftari.test"
PASS="Diag-${STAMP}-Aa1!"

source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"
ANON="$ANON_KEY"; SVC="$SERVICE_KEY"

cleanup() {
  [[ -n "${TOK:-}" ]] && curl -s -o /dev/null -X DELETE "${API}/rest/v1/daftari_admin_users?user_id=eq.${USER_ID:-none}" \
    -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
  [[ -n "${USER_ID:-}" ]] && curl -s -o /dev/null -X DELETE "${API}/auth/v1/admin/users/${USER_ID}" \
    -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}"
  echo "  (throwaway admin removed)"
}
trap cleanup EXIT

echo "==> provisioning a throwaway admin (${EMAIL})"
curl -s -o /dev/null -X POST "${API}/auth/v1/admin/users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\",\"email_confirm\":true}"
TOK=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON}" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')
USER_ID=$(curl -s "${API}/auth/v1/user" -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).id??"")}catch{}})')
[[ -n "$TOK" && -n "$USER_ID" ]] || { echo "FATAL: could not create the throwaway admin" >&2; exit 1; }
curl -s -o /dev/null -X POST "${API}/rest/v1/daftari_admin_users" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"${USER_ID}\"}"

echo "  is_admin = $(curl -s "${API}/rest/v1/daftari_admin_users?select=user_id&user_id=eq.${USER_ID}" \
  -H "apikey: ${SVC}" -H "Authorization: Bearer ${SVC}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(String(JSON.parse(s).length>0))}catch{process.stdout.write("false")}})')"

echo
echo "==> resolved Daraja wiring (as the function sees it)"
curl -s -X POST "${API}/functions/v1/stk-push" \
  -H "apikey: ${ANON}" -H "Authorization: Bearer ${TOK}" -H 'Content-Type: application/json' \
  -d '{"diagnostic":true}' \
  | node -e '
let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
  let d; try { d = JSON.parse(s) } catch { console.log("  unparseable:", s.slice(0,200)); return }
  if (d.outcome !== "ok") { console.log("  refused:", JSON.stringify(d)); return }
  const p = (l,v)=>console.log("  "+(l+"                    ").slice(0,20)+v);
  p("env", d.env);
  p("apiBase", d.apiBase);
  p("merchantKind", d.merchantKind ?? "(unset -> refuses to push)");
  if (d.routing) {
    p("BusinessShortCode", d.routing.businessShortCode);
    p("PartyB", d.routing.partyB);
    p("TransactionType", d.routing.transactionType);
  } else p("routingError", d.routingError);
  const c = d.credentials ?? {};
  p("clientKey", c.clientKey ? "present" : "MISSING");
  p("clientSecret", c.clientSecret ? "present" : "MISSING");
  p("passkey", c.passkeyPresent ? "present ("+c.passkeyLength+" chars)" : "MISSING");
  p("callbackUrl", c.callbackUrl);
  p("c2bShortcode", c.c2bShortcode);
  (d.warnings ?? []).forEach(w => console.log("  !! WARNING: " + w));
})'
