# Frontend Readiness Audit

**Status:** Audit-only pass — no code changes.
**Scope:** The frontend surface and what a real UI rebuild (React + Next.js +
shadcn/ui + Tailwind) would need to consume. Backend correctness is assumed
solid and is out of scope here.
**Date:** 2026-08-08
**Source of truth:** live `openapi.json` from the deployed
`traderos-production.up.railway.app` (44 paths / 11 schemas), the actual route
handlers in `interfaces/api/{server,operator,retail,attribution,security}.py`,
and the dashboard bundle in `interfaces/api/dashboard/`. Nothing here is from
memory of past sprints.

---

## 1. Current dashboard inventory (`interfaces/api/dashboard/`)

Three files, 810 lines total: `index.html` (153), `app.js` (488), `style.css`
(169). It is a **single-page, polling-first static bundle** served by FastAPI's
`StaticFiles` at `/dashboard/` (`server.py:418-422`), with `/` redirecting
there. No build step, no framework, no componentization.

### 1.1 Panels (from `index.html`)

| # | Panel `id` | Purpose | Width |
|---|-----------|---------|-------|
| 1 | `workflow-panel` | Operator workflow: current step, step history, "Advance" control | span-2 |
| 2 | `portfolio-panel` | Equity / cash / positions value / total PnL + canvas equity chart | 1 |
| 3 | `risk-panel` | Kill-switch state, circuit, failures, readiness checks, preflight, engage/disengage buttons | 1 |
| 4 | `ops-panel` | Operational health: HA role/lease, on-call status/deliveries, trading user, secrets | 1 |
| 5 | `positions-panel` | Table: user, market, qty, entry, current, PnL, realized | span-2 |
| 6 | `orders-panel` | Table: market, side, qty, type, status | span-2 |
| 7 | `trades-panel` | Table: time, user, market, side, qty, price, status | span-2 |
| 8 | `strategies-panel` | Strategy catalog: create form + lifecycle action buttons | span-2 |
| 9 | `report-panel` | Session report (JSON / Markdown) | span-2 |
| 10 | `events-panel` | Live event log (SSE) | span-2 |

Plus a **topbar** (orchestrator badge, mode badge, kill-switch badge, role
badge, API-key login box) and a **footer** (SSE connection state, last
refresh time).

### 1.2 Data sources each panel calls (`app.js`)

| Panel | Call(s) | Render fn | Method |
|-------|---------|-----------|--------|
| (topbar) | `GET /v1/auth/me` | `refreshAuth` | — |
| workflow | `GET /v1/workflow` | `renderWorkflow` | GET |
| portfolio | `GET /v1/portfolio`, `GET /v1/equity-curve` | `renderPortfolio`, `renderEquityCurve` | GET |
| risk | `GET /v1/kill-switch`, `GET /v1/readiness`, `GET /v1/preflight` | `renderRisk`, `renderReadiness`, `renderPreflight` | GET |
| ops | `GET /v1/orchestrator/status` | `renderOperationalHealth` | GET |
| positions | `GET /v1/positions` | `renderPositions` | GET |
| orders | `GET /v1/orders` | `renderOrders` | GET |
| trades | `GET /v1/trades` | `renderTrades` | GET |
| strategies | `GET /v1/strategies` | `renderStrategies` | GET |
| report | `GET /v1/reports/session[?fmt=markdown]` | `renderReport` | GET |
| events | `GET /v1/events` (SSE) | `appendEvent` | SSE |

A single `refreshPanels()` fires the first ten REST calls in parallel
(`Promise.allSettled`) on every refresh; failures surface as `api_error`
entries in the event log rather than crashing.

### 1.3 Actions it triggers (mutating calls)

| Control | Call | RBAC gating in JS |
|---------|------|-------------------|
| Sign in / Sign out | sets/clears `X-API-Key` in `localStorage` | role from `/v1/auth/me` |
| Workflow "Advance" | `POST /v1/workflow/advance` `{step, actor, strategy?}` | requires operate/admin |
| Engage kill switch | `POST /v1/kill-switch/engage` | requires admin |
| Disengage kill switch | `POST /v1/kill-switch/disengage` | requires admin |
| Create strategy | `POST /v1/strategies` `{name, template}` | requires operate/admin |
| Enable / disable / promote / archive strategy | `POST /v1/strategies/{name}/<action>` `{}` | requires operate/admin |

All JS-side gating is **cosmetic** — the real enforcement is server-side via
`Depends(require_*)`.

### 1.4 Design tokens — verbatim from `style.css`

```css
:root {
  --bg: #0d1117;
  --panel: #161b22;
  --panel-2: #1c232d;
  --border: #2b3441;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #2f81f7;
  --green: #3fb950;
  --red: #f85149;
  --amber: #d29922;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
```

- **Body font:** `14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Panel headings:** `14px`, uppercase, `letter-spacing: .05em`, muted color
- **Metric values:** `18px`, weight `600`, `var(--mono)`
- **Logo:** `20px` weight `700`, accent color
- **Tables:** `13px`; buttons/inputs `13px`; badges/steps/history/log `12px`
- **Spacing:** grid gap `16px`, panel padding `14px 16px`, topbar `12px 20px`
  (sticky), metrics gap `10px`, row gap `8px`; base unit is ~4px (8/10/12/14/16/20).
- **Radii:** panels `8px`, buttons/inputs/metrics `6px`, badges/steps `999px`
- **Layout:** 2-column grid (`grid-template-columns: 1fr 1fr`), `span-2` for
  wide panels, `max-width: 1400px` centered.
- **Semantic colors:** green = ok/long/positive, red = danger/negative, amber =
  warning/idle, accent blue = interactive/links.

These tokens are a deliberate GitHub-dark clone of the `12_ui-context.md`
future palette (see §3) and should be **carried forward or deliberately
replaced** — not guessed at. Note `style.css` uses `--accent: #2f81f7` /
`--text: #e6edf3` where the design-intent doc specifies `--accent-blue:
#58a6ff` / `--text-primary: #c9d1d9`; the shipped palette is already a minor
variant.

---

## 2. API surface inventory (`/v1/*`)

Source of truth: deployed `openapi.json` (44 paths) + handler code. All
response bodies are **hand-built dicts** — there are **no Pydantic response
models** for the operator surface, so OpenAPI documents request bodies and
validation errors only, not response shapes.

### 2.1 Read-only endpoints

| Method & path | Query/body | Response (from handler) | Auth |
|---|---|---|---|
| `GET /metrics` | — | Prometheus text format (501 if lib missing) | none |
| `GET /v1/healthz` | — | `{status:"alive"}` | public |
| `GET /v1/auth/me` | — | `{authenticated, required, role, roles}` | public |
| `GET /v1/health` | — | `{status, mode, running, ready}` | public |
| `GET /v1/orchestrator/status` | — | `get_status()` incl. `operational{ha,oncall,trading_user_id}`, `secret_rotation` | read |
| `GET /v1/papertrade/sessions` | — | `{sessions:[{id,status,capital}]}` | read |
| `GET /v1/audit` | `limit` (1..100) | `{entries:[{action,actor,resource,timestamp}]}` — **detail omitted** | read |
| `GET /v1/metrics` | — | `{metrics, warning?}` | read |
| `GET /v1/manifest` | `service?` | `{runs:[{service,action,status,duration_ms}]}` | read |
| `GET /v1/events` | — | SSE stream (`text/event-stream`) | read |
| `GET /v1/positions` | — | `{trading_user_id, positions:[{id,market_id,quantity,entry_price,current_price,pnl,realized_pnl,updated_at}]}` | read |
| `GET /v1/orders` | — | `{trading_user_id, orders:[…raw broker dict…]}` | read |
| `GET /v1/trades` | `limit` (default 100) | `{trading_user_id, trades:[{id,market_id,side,quantity,price,status,filled_price,filled_at,external_order_id,created_at}]}` | read |
| `GET /v1/portfolio` | — | `{total_equity,cash,positions_value,total_pnl,position_count}` | read |
| `GET /v1/equity-curve` | — | `{points:[{timestamp,equity}]}` | read |
| `GET /v1/pnl` | — | `{realized_pnl,unrealized_pnl,total_pnl}` | read |
| `GET /v1/kill-switch` | — | `{engaged,reason,circuit_open,consecutive_failures,daily_realized_pnl}` | read |
| `GET /v1/preflight` | — | `{passed,checks,failures,timestamp}` | read |
| `GET /v1/readiness` | — | `{ready, checks:{preflight,data_feeds,broker}}` | read |
| `GET /v1/workflow` | — | `{current_step,next_step,status,session_id,history}` | read |
| `GET /v1/live/check` | — | `check().to_dict()` (free-form) | read |
| `GET /v1/strategies` | — | `{strategies:[{name,template,params,status,version,created_at}]}` | read |
| `GET /v1/strategies/{name}` | — | single strategy dict | read |
| `GET /v1/strategies/{name}/review` | — | `{name,template,version,status,params,created_at,backtests:[…]}` | read |
| `GET /v1/reports/session` | `fmt=json\|markdown` | dict **or** `text/markdown` | read |
| `GET /v1/retail/me` | session token | `{user, risk_profile, orders_enabled}` | session |
| `GET /v1/attribution/replay` | `start*`, `end*` (ISO datetimes) | `{start,end,total_realized_pnl,total_blocked,total_unfilled,chains,mode}` | read |

### 2.2 Mutating endpoints

| Method & path | Request body | Response | Auth |
|---|---|---|---|
| `POST /v1/backtest` | `BacktestRequest{strategy*, candles?}` | synthetic metrics (constant synthetic candles) | read |
| `POST /v1/orchestrator/start` | — | `{status,mode}` | admin |
| `POST /v1/orchestrator/stop` | — | `{status}` | admin |
| `POST /v1/papertrade/session` | `CreatePaperSessionRequest{market_ids?}` | `PaperSessionResponse{id,status,capital}` | operate |
| `POST /v1/workflow/advance` | `WorkflowAdvanceRequest{step*,actor?,strategy?,session_id?,dry_run?}` | `{step,ok,result,detail,current_step}` | operate |
| `POST /v1/kill-switch/engage` | — | `{engaged}` (sends CRITICAL alert) | admin |
| `POST /v1/kill-switch/disengage` | — | `{engaged}` (sends WARNING alert) | admin |
| `POST /v1/strategies` | `StrategyCreateRequest{name*,template*,params?}` | `{name,template,status}` | operate |
| `POST /v1/strategies/compare` | `StrategyCompareRequest{names*}` | `{ranking,metrics}` | operate |
| `POST /v1/strategies/{name}/enable\|disable\|promote\|archive` | — | `{name,status}` (clone returns `{name,template,status}`) | operate |
| `POST /v1/strategies/{name}/clone` | `StrategyCloneRequest{name*}` | `{name,template,status}` | operate |
| `POST /v1/retail/register` | `RegisterRequest{username*,password*,role?}` | `{id,username,role}` (409 conflict) | public+sessions |
| `POST /v1/retail/login` | `LoginRequest{username*,password*}` | `{token,user}` (401 bad creds) | public+sessions |
| `POST /v1/retail/logout` | session token | `{logged_out}` | session |
| `POST /v1/retail/orders` | `RetailOrderRequest{market_id*,side*,quantity*,close_price*}` | `{allowed,order_id,signal_id,reason}`; 403 non-paper, 400 blocked, 422 bad market | session |

### 2.3 Auth model — **flag for the frontend**

- **Current: API-key based.** Every operator route depends on
  `require_read`/`require_operate`/`require_admin` (`security.py:75-77`),
  which resolves the role from an `X-API-Key` header against env-configured
  keys (`TRADEROS_ADMIN_API_KEY`, `TRADEROS_OPERATOR_API_KEY`,
  `TRADEROS_VIEWER_API_KEY`). When **no** keys are configured, auth is
  **open** (`enabled=false`, `security.py:75-76`). A fail-closed boundary
  middleware additionally 401s non-public `/v1` paths when auth is on
  (`security.py:151`). The current dashboard ships this model: it stores the
  key in `localStorage` and sends `X-API-Key`.
- **B1 user/session model already exists but is not browser-facing for the
  operator surface.** `AccountService` (`domain/services/account_service.py`)
  has `authenticate`, `create_session`, `validate_session`, `revoke_session`,
  PBKDF2 password hashing, and per-user API keys. **Session-based login
  already exists** — but only under the `/v1/retail` seam
  (`POST /v1/retail/login` → `{token}`, consumed via `X-Session-Token`
  header). On the deployed PG instance it returns **501 "Account service not
  configured"** (`retail.py:52-55`), because only a `SQLiteUserRepository`
  exists — no PG user repository.
- **For a real frontend:** a browser login flow is **not yet exposed** for the
  operator surface. Two options exist today: (a) keep `X-API-Key` (requires
  key management outside the product), or (b) wire a session/JWT-style login
  for the operator dashboard — the building blocks (`AccountService`, session
  validation) exist, but the **operator-facing login endpoint and a PG user
  repository do not**. This is a gap to build, not to assume away.

---

## 3. Reconciliation vs `12_ui-context.md` planned nav

| Planned screen (from `12_ui-context.md`) | Backend support today | Verdict | Evidence |
|---|---|---|---|
| **Dashboard Home** | Operator workflow, portfolio, positions, orders, trades, kill switch, readiness, preflight, operational health, events | **FULLY SUPPORTED** | `/v1/workflow`, `/v1/portfolio`, `/v1/positions`, `/v1/orders`, `/v1/trades`, `/v1/kill-switch`, `/v1/readiness`, `/v1/preflight`, `/v1/orchestrator/status`, `/v1/events` |
| **Market Overview** (real-time status of tracked symbols) | **No market/candle/quote endpoint exists.** SSE snapshot only carries orchestrator workflow + kill-switch state; no per-symbol price/volume feed. | **NO BACKEND YET** | no OHLCV/quote/`/symbols` route in `openapi.json`; `data_ingestion` is internal |
| **Research Lab** (knowledge graph: observations/hypotheses/experiments/lessons) | Nothing — no research/knowledge endpoints | **NO BACKEND YET** | absent from `openapi.json` |
| **Strategy Vault** (registry + backtest history) | Registry CRUD + lifecycle + review + compare all present. **Backtest history is thin**: `POST /v1/backtest` runs on constant synthetic candles; only `/v1/strategies/{name}/review` exposes recent backtest results. | **PARTIALLY SUPPORTED** | `/v1/strategies`, `/v1/strategies/{name}`, `…/enable`, `…/disable`, `…/promote`, `…/archive`, `…/clone`, `…/compare`, `…/review`, `POST /v1/backtest` |
| **Risk Center** (exposure, limits, kill switch) | Kill switch, readiness, preflight, pnl, positions, and per-user risk attribution (`trading_user_id`) | **FULLY SUPPORTED** | `/v1/kill-switch`, `/v1/readiness`, `/v1/preflight`, `/v1/pnl`, `/v1/positions`, `/v1/orchestrator/status.operational` |
| **Portfolio** (positions, PnL, allocation) | Positions, trades, portfolio summary, equity curve, pnl | **FULLY SUPPORTED** | `/v1/portfolio`, `/v1/positions`, `/v1/trades`, `/v1/equity-curve`, `/v1/pnl` |
| **Settings** (config, data sources, API keys) | Only self-describing auth (`/v1/auth/me`) + read-only secret-rotation stats. No config mutation, no data-source management, no key management endpoint. | **PARTIALLY SUPPORTED** | `/v1/auth/me`, `secret_rotation` in `/v1/orchestrator/status` |

**Since the doc was written, the backend has shipped** the HA/on-call/secrets
panel data (`/v1/orchestrator/status.operational`), per-user risk attribution
(`trading_user_id` on positions/orders/trades), and B3/B4 retail sessions +
causal attribution replay (`/v1/retail/*`, `/v1/attribution/replay`) — none of
which `12_ui-context.md` anticipated. These enrich **Dashboard Home**, **Risk
Center**, and **Portfolio**; they do not create Market Overview or Research Lab.

---

## 4. Day-one gaps a real UI project would hit

### 4.1 CORS — **blocker for a separately-hosted frontend**
- `server.py:156-166` enables `CORSMiddleware` only for origins in the
  `CORS_ORIGINS` env var (comma-separated; `"*"` for all). On the **deployed
  Railway instance `CORS_ORIGINS` is unset** → the allow-list is empty. A
  cross-origin request to `/v1/portfolio` from a browser returns **no
  `Access-Control-Allow-Origin` header** (verified live). A Next.js app on
  Vercel calling this API will be **blocked by CORS out of the box**. Must
  set `CORS_ORIGINS` to the frontend origin (or a proxy).
- Auth is currently **open** on the deployed instance (no API keys configured,
  `/v1/auth/me` → `required:false`), so the gap is CORS, not auth — but
  enabling auth later compounds this.

### 4.2 Inconsistent shapes / undocumented fields a frontend would trip on
- **`GET /v1/orders` returns raw broker dicts**, and the shapes are not
  normalized: paper service returns `{id, symbol, qty, side, type}`
  (`paper_trading_service.py:117-122`), Alpaca returns `{id, symbol, qty,
  side, type}` (`alpaca_broker.py:307-313`). The dashboard already has to
  hedge: `o.market_id || o.symbol`, `o.order_type || o.type`
  (`app.js:255-256`), and its **Qty column reads `o.quantity` while the API
  actually returns `qty`**, and `o.status` which broker dicts do not emit —
  so **Qty and Status render empty in the shipped dashboard**. A real
  frontend needs a stable, documented order schema.
- **`GET /v1/audit` drops `detail`** (`server.py:361-368` returns only
  action/actor/resource/timestamp though `AuditService.record` stores a
  `detail`); replay/attribution consumes the full trail internally. Audit
  consumers cannot see *why* an entry happened.
- **`GET /v1/metrics`** returns `{metrics: {}, warning: …}` when the
  orchestrator is not running vs `{metrics: …}` when it is — shape varies by
  runtime state.
- **`POST /v1/backtest`** runs against **synthetic constant candles** built
  in the handler (`server.py:280-294`) — a frontend showing a backtest result
  would display fabricated-in-place numbers, not real data.
- **Error envelope is inconsistent**: FastAPI validation failures return the
  stock `{"detail": [{loc,msg,type}]}` shape, while app-level errors return
  `{"error": {code, message}}` (`server.py:130-136`). SSE push failures appear
  only in the in-browser event log. A frontend error-handler must branch on
  both.
- **`GET /v1/reports/session?fmt=markdown`** returns `text/markdown` (a
  `Response`, not JSON) — content-type switches with a query param.
- **Free-form responses with no schema**: `/v1/live/check`
  (`check().to_dict()`), `/v1/strategies/{name}/review`, `/v1/manifest`
  (timestamps/run_ids omitted), `/v1/attribution/replay` chains. No Pydantic
  response models exist for any operator route, so a generated TypeScript
  client (`openapi-typescript`) gets **request types only, response types = `unknown`**.

### 4.3 Pagination
- Only two endpoints accept `limit` (`/v1/audit` capped 1..100,
  `/v1/trades` default 100). `/v1/positions`, `/v1/orders`, `/v1/strategies`,
  `/v1/manifest`, `/v1/papertrade/sessions` return **unbounded** lists. There
  is **no cursor/offset pagination, no sorting, no filtering** anywhere —
  relevant once positions/trades/audit grow.

### 4.4 Accessibility / responsive readiness — **confirmed gap, nothing exists**
- Explicitly confirmed: there is **no frontend yet** beyond the static bundle.
  The static `index.html` has no ARIA landmarks/roles, tables have no
  `scope`, interactive elements rely on default focus, no keyboard nav
  management, no reduced-motion handling, and the canvas chart has no text
  alternative. CSS is a fixed 2-column grid with **no media queries** —
  not responsive. `12_ui-context.md` mandates contrast ≥4.5:1, chart text
  alternatives, keyboard nav, ARIA — all are **unimplemented and must be
  built from scratch** in the new UI.

### 4.5 Other
- `EventSource`/SSE (`/v1/events`) is the only real-time channel; it is
  in-process (`events.py`, max 50 buffered events, drops oldest on slow
  consumers). No WebSocket.
- **Authenticated SSE from a browser is now supported** via a short-lived,
  single-purpose, single-use token (`GET /v1/events/token` minted with the
  normal `X-API-Key`, consumed at the SSE route, TTL 60 s, TTL configurable via
  `EVENT_TOKEN_TTL_SECONDS`, key from `SSE_TOKEN_SECRET` or per-process). The
  dashboard `connectSse()` mints when auth is required and subscribes with
  `?token=`. All other endpoints still demand the header seam; the token opens
  exactly the events route and nothing else.
- **Known limitation (documented, NOT fixed by design):** the dashboard stores
  the API key in `localStorage` (`app.js:79`) — XSS-able; a real login flow
  should use session cookies or HttpOnly storage. Out of scope for the 7-route
  contract work; flag for the Next.js build.

### 4.6 Resolved since this audit was written (commit to come)
- **CORS:** `CORS_ORIGINS` is now set on production
  (`https://traderos-production.up.railway.app,http://localhost:3000`) and
  verified live (pre-flight OPTIONS + cross-origin GET return
  `access-control-allow-origin`, disallowed origins get no header).
- **Orders shape:** `/v1/orders` now returns `quantity`/`order_type`/`status`
  via `_normalize_order` at the response seam (normalized once; legacy
  `qty`/`type`/`order_id`/`market_id` tolerated). The dashboard reads these
  fields.
- **Typed response models:** pydantic v2 response models for the 7 in-scope
  routes (`schemas.py`) are wired with `response_model=` and exposed in
  `/openapi.json` (`PortfolioResponse`, `PositionsResponse`, `OrdersResponse`,
  `TradesResponse`, `KillSwitchResponse`, `ReadinessResponse`,
  `StrategiesResponse`, `EventTokenResponse`).
- **Error envelope unified:** all 7 in-scope endpoints (and FastAPI validation
  failures) return the single `{"error": {"code", "message"}}` envelope; the
  shape is documented in the OpenAPI `info.description`.

Still **not** done and out of the 7-route scope: pagination, the
`localStorage` XSS risk, PG-backed operator login (B1), the Market
Overview/Research Lab screens, and the separate Next.js build.

---

## Summary

- **Fully supported screens:** Dashboard Home, Risk Center, Portfolio.
- **Partially supported:** Strategy Vault, Settings.
- **No backend yet:** Market Overview, Research Lab.
- **Old blockers now cleared (7-route contract work):** CORS on the deployed
  instance, untyped response models, raw broker dicts on `/v1/orders`, and
  browser-usable authenticated SSE all shipped and are verified (see §4.6).
- **Remaining blockers for a *separate* Next.js frontend today:** no
  browser-friendly session login for the operator surface (B1 exists
  backend-side, retail-only, and 501s on PG), plus the `localStorage`-key XSS
  risk that must be designed out (cookies/HttpOnly), pagination, and the two
  screens with no backend (Market Overview, Research Lab).
