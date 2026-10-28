#!/usr/bin/env bash
# Fail-closed guard: nothing that looks like a credential may sit in public/.
#
# Why this exists: public/ is served as static assets. A Daraja Postman
# collection downloaded from the developer portal was placed there and deployed
# to production, where it was publicly downloadable at
# https://daftari-amber.vercel.app/<file> with HTTP 200. Anything in this
# directory is public, including sandbox credentials.
#
# The sandbox keys in that file are now burned and must be rotated, but the
# mistake is worth preventing structurally rather than by remembering.
#
# Fails (exit 1) on a match. Run before every build and deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC="${ROOT}/public"

if [ ! -d "$PUBLIC" ]; then
  echo "guard: no public/ directory, nothing to check"
  exit 0
fi

# Filenames that indicate a credential bundle, plus a content scan for the
# literal field names Daraja/Safaricom use to hand out secrets.
NAME_PATTERN='postman|insomnia|credential|secret|\.env|key|token|safaricom|daraja'
CONTENT_PATTERN='consumer[_-]?secret|consumer[_-]?key|"passkey"|"password"|client[_-]?secret|Basic [A-Za-z0-9+/]{16,}'

offenders=()

while IFS= read -r -d '' f; do
  base="$(basename "$f")"
  if printf '%s' "$base" | grep -qiE "$NAME_PATTERN"; then
    offenders+=("${f#${ROOT}/}  (filename matches credential patterns)")
    continue
  fi
  # Skip binaries and large assets; only text files are scanned.
  if file -b --mime-type "$f" | grep -qE '^(text|application/(json|javascript|xml))'; then
    if grep -qiE "$CONTENT_PATTERN" "$f" 2>/dev/null; then
      offenders+=("${f#${ROOT}/}  (content matches credential field names)")
    fi
  fi
done < <(find "$PUBLIC" -type f -print0)

if [ "${#offenders[@]}" -gt 0 ]; then
  cat >&2 <<EOF

FATAL: possible credential material in public/ — refusing to continue.

public/ is served as static assets, so every file here is downloadable by
anyone who knows the URL. The following would be published:

EOF
  printf '  - %s\n' "${offenders[@]}" >&2
  cat >&2 <<'EOF'

Move the file outside the repo (e.g. a gitignored .secrets-local/) or delete
it, then re-run. To use the credentials, pipe them straight into
\`supabase secrets set\` without committing or serving them:

  supabase secrets set --project-ref <ref> DARAA_KEY='<value>'

If this file was ever deployed, treat the credentials inside it as public and
rotate them in the Daraja portal.

EOF
  exit 1
fi

echo "guard: public/ is clean (${#offenders[@]} offenders)"
