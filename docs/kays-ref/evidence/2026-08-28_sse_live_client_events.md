# 2026-08-28 — SSE Live Client Events (Sprint 39) Verification

## Command
`npx vitest run` (full suite) + `npx tsc --noEmit` + `npx eslint <touched files>`

## Observed Result
```
Test Files  69 passed (69)
     Tests  730 passed (730)
Duration  26.73s

tsc --noEmit  → exit 0
eslint (7 touched files) → 0 errors, 0 warnings
```

## Baseline vs This Sprint

| Metric | Baseline (Sprint 38) | Now |
|--------|---------------------|-----|
| Test files | 62 | 69 |
| Tests passing | 695 | 730 |

## New Tests Added

| File | Count | Coverage |
|------|-------|----------|
| `live-updates-endpoint.test.ts` | 4 | 401 without session org; SSE response headers (`text/event-stream`, `no-cache`, `x-accel-buffering: no`); `connected` frame present with **zero** `event:`-prefixed lines; polled row emitted as `id: 41` + `data: {"eventType":"lead:updated"...}` (chunk-exact read) after the 3s poll timer, `poll` invoked with `("org-1", 41)` from the `Last-Event-ID` header; `?lastEventId=9` fallback → `poll("org-1", 9)` |
| `use-live-events.test.tsx` | 4 | Fake `EventSource` + real `QueryClient`: subscribes to `/api/streams/live-updates`; `lead:updated` (id 7) invalidates `["leads"]` (queryFn refetched exactly once) and stores id 7 in `sessionStorage`; `connected` frame does not refetch; unmapped `webhook:delivered` ignored while id still persisted; resume URL `/api/streams/live-updates?lastEventId=3` from sessionStorage; reconnect with `2000ms` backoff on `onerror`, resuming from stored id |

## Real-Path Guarantee (Constitution Article V "proof exercises the real path")

- `live-updates-endpoint.test.ts` calls the **actual** exported h3 `GET` handler
  (`server/routes/api/streams/live-updates.ts`) with a real `H3Event`-shaped request and reads the
  **actual** `ReadableStream` it returns — this is the wire format a browser `EventSource` sees.
- `use-live-events.test.tsx` mounts the **real** `useLiveEvents` hook against a **real** TanStack
  `QueryClient`; the invalidate→refetch assertion proves the browser-side subscription path, not a
  mock of it.
- Wiring: triage (`src/routes/admin/triage.tsx`, `LEAD_LIVE_EVENTS`) and billing
  (`src/components/finance/BillingLedger.tsx`, `BILLING_LIVE_EVENTS`) call the hook in production
  code; both 30s `refetchInterval` loops removed.

## Related Commits (all SSH-signed, `%G?` = `G`)
- `8f60cab` fix(sse): uniform `id`+`data` frames (drop `event:` prefix; resume via header/query)
- `5a9237b` feat(sse): `useLiveEvents` hook (eventType-in-payload invalidation + resume)
- `44eb06e` feat(sse): subscribe triage desk; drop 30s lead polling
- `c8e1dea` feat(sse): subscribe billing ledger; drop 30s invoice polling
- `7503205` test(sse): endpoint protocol test + fake-EventSource hook test

## Docs Updated
- `docs/release-readiness.md` — row #56 PASS; blocker row removed; pre-pilot checklist #6 ✓;
  timestamp → Sprint 39.
- `docs/sprint-cross-reference.md` — Sprint 39 entry added.
- `docs/sprints/sprint-39-live-client-events-sse.md` — full sprint log.
- `CHANGELOG.md` — Sprint 39 Unreleased section.

## Verdict
PASS — full suite green. No assertions weakened (AGENTS.md rule 4). Release-readiness #56 is now
automated; a live two-tab smoke test remains optional.