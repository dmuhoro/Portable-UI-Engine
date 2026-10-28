#!/usr/bin/env bash
# Register the C2B Confirmation/Validation URLs with Safaricom.
#
# C2B is how a customer-initiated payment reaches us: the customer opens their
# own M-PESA app, types a Daftari shortcode, and pays. We receive nothing for
# that unless a ConfirmationURL is registered — which is exactly why the manual
# Till flow needed a human to match an M-Pesa receipt by eye.
#
# This is the automated replacement. It is separate from STK Push registration:
# STK Push is merchant-initiated and needs no registration, while C2B needs a
# shortcode that Safaricom has issued for C2B and a registered callback URL.
#
# Reads the consumer key/secret from Supabase secrets or the environment, never
# prints them, and never writes them to disk.
#
# Usage:
#   scripts/register-c2b-urls.sh <shortcode> [project_ref]
#   DARAJA_CLIENT_KEY=... DARAJA_CLIENT_SECRET=... scripts/register-c2b-urls.sh 3631767
set -euo pipefail

SHORTCODE="${1:?usage: scripts/register-c2b-urls.sh <shortcode> [project_ref]}"
REF="${SUPABASE_PROJECT_REF:-${2:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"
ENV_NAME="${DARAJA_ENV:-sandbox}"
BASE="https://sandbox.safaricom.co.ke"
[ "$ENV_NAME" = "production" ] && BASE="https://api.safaricom.co.ke"

CONFIRM_URL="${API}/functions/v1/c2b-confirmation"

echo "Environment : ${ENV_NAME}"
echo "Base        : ${BASE}"
echo "ShortCode   : ${SHORTCODE}"
echo "Confirm URL : ${CONFIRM_URL}"
echo

if [ -z "${DARAJA_CLIENT_KEY:-}" ] || [ -z "${DARAJA_CLIENT_SECRET:-}" ]; then
  cat >&2 <<'EOF'
FATAL: DARAJA_CLIENT_KEY / DARAJA_CLIENT_SECRET are not in this shell.

They exist as Supabase secrets but secrets are not readable back out, and
that is deliberate. Read them from the Daraja portal and export them here
for this one command, then unset:

  export DARAJA_CLIENT_KEY='...'
  export DARAJA_CLIENT_SECRET='...'
  scripts/register-c2b-urls.sh <shortcode>
  unset DARAJA_CLIENT_KEY DARAJA_CLIENT_SECRET

Do not write them to a file inside the repository. public/ is served to the
internet; see scripts/guard-public-secrets.sh.
EOF
  exit 2
fi

echo "==> requesting an OAuth token"
TOKEN=$(curl -s -X POST "${BASE}/oauth/v1/generate?grant_type=client_credentials" \
  -H "Authorization: Basic $(printf '%s:%s' "$DARAJA_CLIENT_KEY" "$DARAJA_CLIENT_SECRET" | base64 -w0)" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')

if [ -z "$TOKEN" ]; then
  echo "FATAL: no access token. Check the key/secret belong to ${ENV_NAME}." >&2
  exit 1
fi
echo "  got a token"

echo
echo "==> registering C2B URLs"
resp=$(curl -s -w '\n%{http_code}' -X POST "${BASE}/mpesa/c2b/v1/registerurl" \
  -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d "{\"ShortCode\":\"${SHORTCODE}\",\"ResponseType\":\"Completed\",\"ConfirmationURL\":\"${CONFIRM_URL}\",\"ValidationURL\":\"${CONFIRM_URL}\"}")
code=$(printf '%s' "$resp" | tail -1)
body=$(printf '%s' "$resp" | sed '$d')

echo "  HTTP ${code}"
echo "  ${body}"

if [ "$code" != "200" ]; then
  cat >&2 <<EOF

Registration refused. Common causes:
  - the shortcode is not registered for C2B. A Till number is usually NOT a
    C2B shortcode; Safaricom issues a Paybill for C2B. Check the Daraja
    dashboard for the C2B product's shortcode.
  - the key/secret are for the other environment.
  - the URL must be publicly reachable over HTTPS with no auth.
EOF
  exit 1
fi

case "$body" in
  *'"Status":"Success"'*|*'"status":"Success"'*)
    echo
    echo "OK: C2B registered for ${SHORTCODE} in ${ENV_NAME}."
    echo "Every customer-initiated payment to that shortcode is now POSTed to"
    echo "${CONFIRM_URL} and settled automatically, once Safaricom confirms it."
    ;;
  *)
    echo
    echo "Registration returned a non-Success body; treat this as failed." >&2
    exit 1
    ;;
esac
