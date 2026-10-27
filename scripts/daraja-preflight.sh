#!/usr/bin/env bash
# Report whether Daftari can actually push an M-Pesa STK request, and if not,
# exactly which credential is missing and where to get it.
#
# This exists because "not configured" used to be a single opaque 503. Before
# the drill, an operator needs to know whether the blocker is a missing portal
# value, a misspelled merchant kind, or a routing inconsistency.
#
# Prints secret NAMES and their presence only. Never prints a secret value.
set -euo pipefail

REF="${SUPABASE_PROJECT_REF:-${1:-rjedivbpldkroffswoyb}}"

REQUIRED=(DARAJA_CLIENT_KEY DARAJA_CLIENT_SECRET DARAJA_PASSKEY DARAJA_CALLBACK_URL DARAJA_MERCHANT_KIND)
# A till needs BOTH: STORE becomes BusinessShortCode, TILL becomes PartyB.
# Preflight checked only the store, so a till merchant with no till number
# would have been reported READY and then silently charged to the store as
# PartyB, because the resolver falls back to the store value.
ROUTING_FOR_TILL=(DARAJA_STORE_NUMBER DARAJA_TILL_NUMBER)
ROUTING_FOR_PAYBILL=(DARAJA_PAYBILL_NUMBER)

names_json=$(supabase secrets list --project-ref "$REF" --output json 2>/dev/null)
if [ -z "$names_json" ]; then
  echo "FATAL: could not read secrets for $REF (is the Supabase CLI linked?)" >&2
  exit 2
fi

present() { printf '%s' "$names_json" | grep -q "\"$1\"" && echo yes || echo no; }
getval() { printf '%s' "$names_json" | python3 -c "
import sys, json
for d in json.load(sys.stdin):
    if d.get('name') == '$1':
        print(d.get('digest') and '' or '', end='')
" 2>/dev/null; }

echo "Daftari Daraja preflight"
echo "  project: $REF"
echo

missing=0
echo "Required credentials"
for key in "${REQUIRED[@]}"; do
  if [ "$(present "$key")" = yes ]; then
    printf '  [ok]      %s\n' "$key"
  else
    printf '  [MISSING] %s\n' "$key"
    missing=$((missing + 1))
  fi
done
echo

kind=no
[ "$(present DARAJA_MERCHANT_KIND)" = yes ] && kind=yes
echo "Merchant routing"
if [ "$kind" = no ]; then
  printf '  [MISSING] DARAJA_MERCHANT_KIND  (set to "till" or "paybill")\n'
  missing=$((missing + 1))
  echo "  routing   : cannot resolve, merchant kind is unset"
else
  for key in "${ROUTING_FOR_TILL[@]}"; do
    if [ "$(present "$key")" = yes ]; then
      printf '  [ok]      %s\n' "$key"
    else
      printf '  [MISSING] %s   (required for a till merchant)\n' "$key"
      missing=$((missing + 1))
    fi
  done
  for key in "${ROUTING_FOR_PAYBILL[@]}"; do
    if [ "$(present "$key")" = yes ]; then
      printf '  [ok]      %s\n' "$key"
    fi
  done
  echo
  echo "  Safaricom routes till and paybill differently:"
  echo "    till    -> BusinessShortCode = STORE, PartyB = TILL, CustomerBuyGoodsOnline"
  echo "    paybill -> BusinessShortCode = PAYBILL, PartyB = PAYBILL, CustomerPayBillOnline"
fi
echo

# C2B (customer-initiated) is a separate product with its own registration.
# Its absence does NOT block STK Push, so it is reported rather than counted as
# a missing STK credential.
echo "C2B (customer-initiated payments into our shortcode)"
if [ "$(present C2B_SHORTCODE)" = yes ]; then
  printf '  [ok]      C2B_SHORTCODE\n'
else
  printf '  [not set] C2B_SHORTCODE — C2B cannot settle without it.\n'
  printf '             Needed only if you want automated reconciliation of\n'
  printf '             hand-paid subscriptions. Register with\n'
  printf '             scripts/register-c2b-urls.sh <shortcode>.\n'
fi
echo

if [ "$missing" -gt 0 ]; then
  echo "RESULT: NOT READY — stk-push will refuse with 503 DARAJA_NOT_CONFIGURED."
  echo
  echo "Where the missing values come from:"
  echo "  1. Sign in at https://developer.safaricom.co.ke"
  echo "  2. Open your app -> 'Lipa na M-PESA Online' (STK Push) product."
  echo "  3. The product page shows: Consumer Key, Consumer Secret, Passkey,"
  echo "     Business Short Code / Paybill, and the sandbox Test MSISDN."
  echo "  4. The Passkey is ONLY on that page. It cannot be derived or guessed."
  echo "  5. Set it server-side (never in the app bundle):"
  echo "       supabase secrets set --project-ref $REF DARAJA_PASSKEY='<passkey>'"
  echo
  echo "  Note: sandbox credentials are NOT production credentials. Safaricom"
  echo "  issues a separate consumer key, secret, passkey and shortcode for live."
  exit 1
fi

echo "RESULT: READY — a push will be attempted. Run scripts/run-stk-drill.sh to prove it end to end."
