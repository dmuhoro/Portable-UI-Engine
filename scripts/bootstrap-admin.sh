#!/usr/bin/env bash
# Promote an EXISTING Daftari account to operator (admin).
#
# Why this is a script and not a button: daftari_admin_users has RLS with
# `using (false) with check (false)`, so no client can add an admin. Promotion
# is deliberately a service_role-only, out-of-band action. Production currently
# has ZERO admins, which means the reconciliation queue and the CEO dashboard
# are both unreachable until someone runs this.
#
# It takes an EMAIL, never a user id, so it is impossible to promote the wrong
# account by pasting a stale uuid. It refuses to invent an account: the user
# must already exist, because an admin row pointing at a nonexistent user would
# silently grant nothing while appearing provisioned.
#
# Usage: scripts/bootstrap-admin.sh <email> [project_ref]
#   scripts/bootstrap-admin.sh owner@example.com
set -euo pipefail

EMAIL="${1:?usage: scripts/bootstrap-admin.sh <email> [project_ref]}"
REF="${SUPABASE_PROJECT_REF:-${2:-rjedivbpldkroffswoyb}}"
API="https://${REF}.supabase.co"

source "$(dirname "$0")/_supabase-keys.sh"
supa_keys_init "$REF"

echo "Looking up ${EMAIL} in ${REF}..."
USER_ID=$(curl -s "${API}/auth/v1/admin/users?limit=1000" \
  -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" \
  | node -e '
let s = "";
process.stdin.on("data", d => s += d).on("end", () => {
  const body = JSON.parse(s);
  const users = body.users ?? body;
  const match = users.find(u => (u.email ?? "").toLowerCase() === process.argv[1].toLowerCase());
  process.stdout.write(match?.id ?? "");
});
' "$EMAIL")

if [ -z "$USER_ID" ]; then
  echo "No Daftari account has the email ${EMAIL}." >&2
  echo "Sign up in the app first, then re-run. Refusing to invent an account:" >&2
  echo "an admin row pointing at a nonexistent user grants nothing while" >&2
  echo "looking provisioned, which is the worst possible failure here." >&2
  exit 1
fi

echo "Promoting ${USER_ID} ..."
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${API}/rest/v1/daftari_admin_users" \
  -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}" \
  -H 'Content-Type: application/json' -H 'Prefer: resolution=merge-duplicates' \
  -d "{\"user_id\":\"${USER_ID}\"}")

if [ "$code" != "201" ] && [ "$code" != "204" ]; then
  echo "FAILED: Supabase returned HTTP ${code}." >&2
  exit 1
fi

echo "Verifying the admin row is actually readable..."
ROW=$(curl -s "${API}/rest/v1/daftari_admin_users?select=user_id&user_id=eq.${USER_ID}" \
  -H "apikey: ${SERVICE_KEY}" -H "Authorization: Bearer ${SERVICE_KEY}")
if ! printf '%s' "$ROW" | grep -q "${USER_ID}"; then
  echo "Row was not readable after insert; do not assume this account is an operator." >&2
  exit 1
fi
echo "  admin row present for ${USER_ID}"

# Full end-to-end check: sign in as the account and ask the database whether it
# is an operator. This needs the account password, which is deliberately NOT
# required — an operator should never have to hand their password to a script in
# order to be promoted. Skipped cleanly when ADMIN_PASSWORD is unset.
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  cat <<EOF

OK: ${EMAIL} has an admin row, and it is readable.

  is_admin() was NOT verified end-to-end, because that requires this
  account's password. Sign in to the app and open the admin screen: if the
  CEO dashboard and the payment queue render, the gate is open. If they
  show "Not authorized", re-run with ADMIN_PASSWORD set.

EOF
  exit 0
fi

TOKEN=$(curl -s -X POST "${API}/auth/v1/token?grant_type=password" -H "apikey: ${ANON_KEY}" \
  -H 'Content-Type: application/json' -d "{\"email\":\"${EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.stdout.write(JSON.parse(s).access_token??"")}catch{}})')

if [ -z "$TOKEN" ]; then
  echo "Admin row created, but could not sign in to verify is_admin()." >&2
  echo "The promotion is in place; verify by opening the admin screen." >&2
  exit 1
fi

IS_ADMIN=$(curl -s -X POST "${API}/rest/v1/rpc/is_admin" \
  -H "apikey: ${ANON_KEY}" -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' -d '{}')

if [ "$IS_ADMIN" = "true" ]; then
  echo "OK: ${EMAIL} is now an operator. is_admin() = true."
else
  echo "Row created but is_admin() returned '${IS_ADMIN}'. Investigate before relying on it." >&2
  exit 1
fi
