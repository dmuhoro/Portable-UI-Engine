# Vercel Deploy — TraderOS Static Dashboard

This repo's operator dashboard (`src/traderos/interfaces/api/dashboard/`) is a vanilla HTML/CSS/JS SPA served by FastAPI at `/dashboard/`. To host the UI on Vercel (separate from the Railway API), deploy the static files with the included `vercel.json` rewrites.

## 1) What this does

- Serves the existing dashboard as a static site on Vercel.
- Rewrites `/v1/*`, `/api/*`, and `/metrics` to the Railway production API (`https://traderos-production.up.railway.app`). This keeps the auth boundary on the API (fail-closed) and avoids CORS friction for same-origin requests when using rewrites.
- Adds conservative security headers (no sniff, strict referrer policy, frame deny).

The dashboard already handles Basic auth (username/password) against the API's auth scheme. No server-side logic moves to Vercel — only static assets.

## 2) Deploy (recommended)

### Option A — Vercel CLI

```bash
npm i -g vercel
vercel login
cd /path/to/TraderOS
# Deploy static output from src/traderos/interfaces/api/dashboard
vercel --cwd src/traderos/interfaces/api/dashboard --prod
```

Or from repo root, point output directory:

```bash
vercel --output-directory src/traderos/interfaces/api/dashboard --prod
```

### Option B — Vercel Git integration

1. Import this Git repo into Vercel.
2. Set **Framework Preset** = `Other` (no build).
3. Set **Output Directory** = `src/traderos/interfaces/api/dashboard`.
4. Deploy. Vercel will use `vercel.json` at repo root.

## 3) Environment

No secrets required on Vercel (all auth/API calls go to Railway). If you want to override the API base in local dev (without rewrites), you can set `VITE_API_BASE_URL` in a local `.env`, but the shipped static build uses relative paths and Vercel rewrites in production.

## 4) Verification

```bash
# Follow redirect to /dashboard/
curl -sL -o /dev/null -w "final=%{url_effective} code=%{http_code}\n" <your-vercel-url>/
# Check security headers
curl -sI <your-vercel-url>/ | grep -E "(X-Content-Type-Options|Referrer-Policy|X-Frame-Options)"
# Health check via rewrite (should proxy to Railway)
curl -s <your-vercel-url>/v1/healthz
```

Expected: root redirects to `/dashboard/` (200), headers present, `/v1/healthz` returns `{"status":"alive"}`.

## 5) Notes

- Constitution 10.12: no secrets committed. Auth remains server-side (Railway). This deployment keeps the API as the system boundary (ADR-aligned).
- Rewrites proxy requests — the browser sees same origin, so no CORS preflight complexity for the existing dashboard code.
- If Railway API domain changes, update `destination` URLs in `vercel.json` (single source of truth at repo root).
