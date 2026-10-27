# Code Standards Brief

> Condensed from `docs/code-standards.md`. Follow these when writing code.

## File Naming

- `.server.ts` suffix for anything importing `node:crypto`/`node:process` or calling `getDb()`.
- `src/lib/*.server.ts` — infra; `src/lib/api/*.server.ts` — createServerFn handlers;
  `src/lib/marketing/*.server.ts` — domain logic.
- PascalCase components, `use`-prefix hooks.

## createServerFn Pattern

```ts
export const someAction = createServerFn({ method: "POST" })
  .inputValidator(z.object({ ... }))
  .handler(async ({ data }) => {
    if (!isDbAvailable()) return { status: "db_unavailable" as const };
    const { orgId, log } = requireOrg();
    const db = await getDb();
    // ...
    return { status: "ok" as const, ... };
  });
```

Return a discriminated union with a literal `status` field.

## Logging

- Always use named `EVENTS` constants from `logger.server.ts` — never raw strings.
- Use `log` (child logger from `requireOrg()`) inside handlers; use `logger` elsewhere.
- Never pass PII under a non-redacted key name. Redacted keys: `email, password, phone, name, raw_payload`.

## Tenant Scoping

- `requireOrg()` → `{ orgId, log }`; bind `orgId` in every query as `$N`.
- Exceptions: `getServerStatus()` (intentionally unscoped), `bookSlot` (orgId from client — flagged gap).

## Known Style Conflicts (don't expand scope — follow the dominant pattern)

- Return-status vs throw: createServerFn handlers return status objects; plain async functions
  (`generateInvoice`, `recordPayment`) throw. Follow whichever the file you touch already uses.
- Zod schema placement: inline unless another file imports it.

## Imports

- Server files: relative paths (`../db.server`).
- Client hooks: `@/` aliases (`@/lib/api/leads.server`).