# Code Standards

> Observed conventions, not invented ones. Where two files disagree, the conflict is flagged.

---

## 1. File Naming

### `.server.ts` suffix

Files that import `node:crypto`, `node:process`, or call `getDb()` must use the `.server.ts` suffix. This tells TanStack Start to exclude them from the client bundle.

**Convention in use:**
- `src/lib/*.server.ts` — infrastructure (db, auth, session, logger, encryption, permissions)
- `src/lib/api/*.server.ts` — `createServerFn` handler files (the API layer)
- `src/lib/marketing/*.server.ts` — domain logic (leads, automation, reviews) called by api/ handlers
- `src/lib/subscriptions.server.ts`, `src/lib/metering.server.ts`, etc. — standalone domain modules

**Not a `.server.ts`:**
- `src/hooks/*.ts` — client-side React hooks (call `createServerFn` handlers from the client)
- `src/components/*.tsx` — React components
- `src/hooks/clinic-os-types.ts` — shared type definitions

### Component naming

- PascalCase for component files: `ThemeToggle.tsx`, `BillingLedger.tsx`, `NetworkStatus.tsx`
- Sub-directories under `src/components/`: `finance/`, `leads/`, `site/`, `ui/`

### Hook naming

- `use` prefix: `useLeads.ts`, `useAuth.ts`, `useNetworkStatus.ts`, `useClinicOSSubmit.ts`
- One exception: `use-hotkey.ts` uses kebab case (the file itself exports `useHotkey`)

---

## 2. `createServerFn` Pattern

Every API handler follows this structure:

```ts
export const someAction = createServerFn({ method: "POST" })  // or "GET"
  .inputValidator(z.object({ ... }))                          // Zod schema
  .handler(async ({ data }) => {
    if (!isDbAvailable()) return { status: "db_unavailable" as const };
    const { orgId, log } = requireOrg();                      // tenant scoping
    const db = await getDb();
    // ... query ...
    return { status: "ok" as const, ... };
  });
```

**Observed return types:** Every handler returns a discriminated union with a `status` field as a string literal. The convention is `{ status: "ok" as const }` or `{ status: "db_unavailable" as const }`.

---

## 3. Zod Schema Placement

Two conventions coexist:

| Pattern | Example | Files |
|---------|---------|-------|
| **Inline at top of file** — schema defined where it's used, not exported | `const submitSchema = z.object({...})` | `leads.server.ts:32`, `billing.server.ts:218` |
| **Exported for reuse** — schema exported, type derived from it | `export const updateClinicConfigSchema = z.object({...})` | `clinic-config.server.ts:37`, `registration.server.ts:12` |

**DECISION NEEDED:** There is no consistent rule for when a schema is exported vs inline. The pattern appears to be: export only if another file imports it. `clinic-config.server.ts` exports its schema; `leads.server.ts` does not. Neither convention is wrong, but the codebase should pick one rule and stick to it.

---

## 4. Error Handling — Two Patterns in Conflict

### Pattern A: Return status objects (leads.server.ts style)

```ts
if (!isDbAvailable()) {
  return { status: "db_unavailable" as const };
}
// ... do work ...
return { status: "created" as const };
```

Used in: `leads.server.ts`, `billing.server.ts` (createServerFn handlers), `interactions.server.ts`, `automation.server.ts`, `clinic-config.server.ts`, `resources.server.ts`, `diagnostics.server.ts`

Errors are caught implicitly — the handler never throws, it returns a status field.

### Pattern B: Throw on failure (scheduling.server.ts style)

```ts
const acquired = await getConcurrentLock(lockKey);
if (!acquired) {
  return { status: "concurrency_conflict" as const };
}
try {
  // ... work ...
} finally {
  await releaseConcurrentLock(lockKey);
}
```

Used in: `scheduling.server.ts` (bookSlot, reserveSlot), `billing.server.ts` (generateInvoice, recordPayment as plain functions)

**DECISION NEEDED:** The scheduling/billing layer throws `new Error()` from plain async functions (`generateInvoice`, `recordPayment`), which then propagate as 500s to the caller. The `createServerFn` handlers that call these functions (e.g., `generateInvoiceForCheckedIn`) catch via `try { requireRole(...) } catch { return { status: "forbidden" } }` but do NOT wrap the `generateInvoice()` call in a try/catch — meaning a lock failure results in an unhandled throw and a 500 response to the client.

This is inconsistent with the leads.server.ts pattern where every path returns a status. **The codebase should decide: all handlers return status objects, or all handlers throw on error. Mixing both means some failure modes produce 500s while others produce `{ status: "error" }`.**

---

## 5. Logger Usage Convention

### From `createServerFn` handlers

```ts
import { logger, EVENTS } from "../logger.server";
const { orgId, log } = requireOrg();      // log is a child logger pre-bound to orgId
log.info("Something happened", {
  event: EVENTS.SOME_EVENT,               // always use a named event constant
  leadId: 123,                            // structured metadata
  duration_ms: Date.now() - start,        // timing when relevant
});
```

### From plain async functions (not createServerFn)

```ts
import { logger, EVENTS } from "../logger.server";
logger.info("Something happened", {
  event: EVENTS.SOME_EVENT,
  orgId: orgId.slice(0, 8),              // truncate orgId in logs
});
```

**Convention:** Always use a named `EVENTS` constant — never pass a raw string as the event. The 50+ event constants in `logger.server.ts` are the canonical list.

### What NOT to log

`logger.server.ts:109` redacts keys: `email`, `password`, `phone`, `name`, `raw_payload`. But this is key-name-based — if you pass `{ userMessage: "John called from 07123..." }`, the value is NOT redacted because the key is `userMessage`, not `phone`.

**Rule:** Never pass PII as a value under a non-redacted key name. Use the PII key names if the value is PII, or don't log it.

---

## 6. Tenant Scoping Pattern

Every `createServerFn` handler must:

1. Call `requireOrg()` to get `{ orgId, log }`
2. Use `orgId` in every SQL query as `$N` (never hardcode, never skip)

```ts
const { orgId, log } = requireOrg();
const rows = await db.unsafe(
  `SELECT ... WHERE organization_id = $1`,
  [orgId],
);
```

**Two exception patterns:**
- `getServerStatus()` in `diagnostics.server.ts` — does NOT call `requireOrg()` (intentionally unscoped)
- `scheduling.server.ts:bookSlot` — receives `organizationId` in the input validator instead of via `requireOrg()` (this is the one handler where the client asserts the orgId, which is a weaker security model)

**DECISION NEEDED:** `bookSlot` accepts `organizationId` from the client input rather than reading it from the session via `requireOrg()`. This means a client can theoretically book a slot in any org if they supply a different UUID. All other handlers use `requireOrg()`. This should be flagged as a potential gap.

---

## 7. Import Convention

Server files import from siblings with relative paths:
```ts
import { getDb } from "../db.server";
import { requireOrg } from "../tenant.server";
import { logger, EVENTS } from "../logger.server";
```

Client hooks import from the api layer using `@/` aliases:
```ts
import { fetchLeads } from "@/lib/api/leads.server";
import { getCurrentSession } from "@/lib/auth-check.server";
```

**Note:** Client hooks directly import `.server.ts` files. This works because TanStack Start's build strips `.server.ts` from the client bundle — but only if the import chain doesn't cross into a non-server context. The hooks work because they're called from components that run in the server-rendered context first.

---

## 8. Component Conventions

- All components are functional (no class components)
- State management: `useState` for local, TanStack Query for server state
- Optimistic updates: implemented in `useLeads.ts` via `onMutate`/`onError`/`onSettled`
- Offline support: `localStorage` queue in `useClinicOSSubmit.ts` with online/offline event listeners
- No context providers — hooks return data, components consume directly

---

*Last verified: Sprint 34*
