#!/usr/bin/env bash
# Shared helper: read Supabase project API keys into shell variables without
# ever printing them.
#
# Exists because this parsing was duplicated across scripts, and a hand-typed
# copy of the ternary silently produced `Array.isArray(k)?k.data??k` (a
# condition with no else-branch, i.e. a syntax error) in two of them. One
# sourced definition removes the whole class of mistake.
#
# Usage:
#   source "$(dirname "$0")/_supabase-keys.sh"
#   supa_keys_init "$REF"          # sets ANON_KEY and SERVICE_KEY
#
# The API keys are already in the environment for anyone who can run these
# scripts; this only makes sure none of them end up in a log or a transcript.

supa_keys_init() {
  local ref="$1"
  local keys_json
  keys_json=$(supabase projects api-keys --project-ref "$ref" --output json 2>/dev/null)
  if [ -z "$keys_json" ]; then
    echo "FATAL: could not read API keys for $ref (is the Supabase CLI linked?)" >&2
    return 2
  fi

  local pick
  pick() {
    printf '%s' "$keys_json" | node -e '
let s = "";
process.stdin.on("data", d => s += d).on("end", () => {
  const parsed = JSON.parse(s);
  const list = Array.isArray(parsed) ? parsed : (parsed.data ?? parsed);
  const row = list.find(x => x.name === process.argv[1]) ?? list.find(x => x.role === process.argv[1]);
  process.stdout.write(row?.api_key ?? row?.key ?? "");
});
' "$1"
  }

  ANON_KEY=$(pick anon)
  SERVICE_KEY=$(pick service_role)

  if [ -z "$ANON_KEY" ] || [ -z "$SERVICE_KEY" ]; then
    echo "FATAL: could not resolve both anon and service_role keys" >&2
    return 2
  fi
}
