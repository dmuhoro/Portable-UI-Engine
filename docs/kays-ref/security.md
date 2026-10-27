# Security — Kay's Wellness Centre SaaS

> Honest assessment of the current state. No euphemisms.

---

## 1. Session Lifecycle

### Token Format

The session is an HMAC-signed base64url JWT stored in the `kwc_session` cookie (`session.server.ts:14-22`).

**Payload (`SessionPayload`):**
```ts
{ userId: number; orgId: string; role: string; exp: number }
```

There is no `iat` (issued-at), no `jti` (token ID), and no refresh token. The token is self-contained and stateless.

### Signing

- Algorithm: HMAC-SHA256, truncated to 32 hex characters
- Key: `SESSION_SECRET` env var (minimum 32 chars, defaults to `"dev-secret-change-in-prod"`)
- Verification: `crypto.timingSafeEqual()` (`session.server.ts:33`)

### Expiry

| Property | Value |
|----------|-------|
| `exp` in payload | `Date.now() + 86_400_000` (24 hours from login) |
| Cookie `maxAge` | `86400` (24 hours) |
| Cookie flags | `httpOnly: true`, `secure: true`, `sameSite: "lax"`, `path: "/"` |

### What's Missing

- **No token revocation.** Once issued, a token is valid for 24 hours regardless of what happens. There is no server-side session store, no blacklist, no way to invalidate a token before `exp` without changing `SESSION_SECRET` (which invalidates *all* sessions).
- **No refresh rotation.** Users are not re-authenticated until the 24-hour expiry. If the cookie leaks, the attacker has 24 hours of access.
- **No logout endpoint.** There is no `clearCookie()` or server-side logout anywhere in the codebase. The only way to "log out" is for the user to delete the cookie manually or wait for expiry.
- **No `iat` check.** The token does not record when it was issued. There is no way to invalidate tokens issued before a certain date (e.g., after a credential compromise).

---

## 2. Environment Validation (`env.server.ts`)

### What Happens at Boot

On first access to any `getEnv()`-derived function, `env.server.ts:25-44` runs a single Zod `safeParse` over `process.env`. The validated result is cached in a module-level `validated` variable — it runs exactly once per process.

### Required Variables (will throw if missing)

| Variable | Validation | Default |
|----------|-----------|---------|
| `DATABASE_URL` | `z.string().url()` — must be a valid URL | **none** — throws on missing |
| `SESSION_SECRET` | `z.string().min(32)` | `"dev-secret-change-in-prod"` |

### Optional Variables (have defaults)

| Variable | Default |
|----------|---------|
| `DEFAULT_ADMIN_EMAIL` | `admin@kayswellnesscentre.org` |
| `DEFAULT_ADMIN_PASSWORD` | `admin0726` |
| `NODE_ENV` | `"development"` |
| `MAX_QUEUE_RETRIES` | `3` |
| `QUEUE_POLL_INTERVAL_MS` | `5000` |
| `ANALYTICS_REVENUE_VALUE` | `250` |
| `VERCEL_REGION` | *(undefined)* |
| `WHATSAPP_TOKEN` | *(undefined)* |
| `WHATSAPP_PHONE_NUMBER_ID` | *(undefined)* |

### What Happens If a Required Var Is Missing

`env.server.ts:29-34`:
```
console.error → "[env] Configuration validation failed:"
throw new Error → "Environment validation failed. Set the required variables."
```

This crashes the server process on first database access. The error propagates up through `getDb()` and the request fails with a 500. There is no graceful degradation for missing `DATABASE_URL` — the app is dead without it.

### The `SESSION_SECRET` Default Problem

`env.server.ts:9` defaults `SESSION_SECRET` to `"dev-secret-change-in-prod"`. Line 39-41 logs a warning if this value is still in use. But the warning does not prevent startup. In production, if `SESSION_SECRET` is not set:

1. All sessions are signed with a publicly known key (this file is in git)
2. Any attacker can forge a valid session cookie with any `userId`, `orgId`, and `role`
3. The `secure: true` flag on the cookie only prevents network interception — it does not prevent forgery

### `requireDatabaseUrl()` Bypasses Zod

`env.server.ts:62-68` reads `process.env.DATABASE_URL` directly instead of using the Zod-validated `getEnv()`. This is inconsistent — it checks for existence but not for URL validity.

### `config.server.ts` Bypasses Zod Entirely

`config.server.ts` wraps raw `process.env` in a `getServerConfig()` function without running it through the Zod schema. Any code using `getServerConfig()` instead of `getEnv()`-derived getters has no validation.

---

## 3. PII Handling in `logger.server.ts`

### What Counts as PII

`logger.server.ts:109`:
```ts
const PII_KEYS = new Set(["email", "password", "phone", "name", "raw_payload"]);
```

### How Redaction Works

`logger.server.ts:111-123`: The `redact()` function iterates over every metadata object passed to any log call. If a key matches `PII_KEYS`, the value is replaced with `"[REDACTED]"`. Nested objects are recursively redacted.

**Redacted fields are never written to logs** — not in development (console output), not in production (JSON to stdout).

### What PII Actually Reaches the Logger

PII only reaches the logger if a caller explicitly includes it in metadata. The logger itself does not read the database or session — it only receives what it's given.

**Callers that pass PII-adjacent data:**

| File | What's logged | PII risk |
|------|--------------|----------|
| `auth.server.ts:101-105` | `userId`, `orgId` on successful login | Low — IDs, not PII |
| `dispatch.server.ts:30-31` | `phone` on WhatsApp dispatch | **Medium** — phone number is logged if WhatsApp provider is not configured |
| `leads.server.ts` | `leadId` on various events | Low — ID only |
| `messaging.server.ts` | Message content in `getConversationHistory()` | **High** — conversation text is returned to callers who may log it |
| `reconciliation.server.ts` | Payment amounts, match scores | Low — financial data, not PII |

**The redaction is key-name-based, not value-based.** If a caller passes `{ metadata: "John's phone is 0712345678" }`, the string itself is not redacted because the key is `metadata`, not `phone`. The redaction is only effective when callers use the expected field names.

### Production vs Development Output

- **Production** (`isProduction() === true`): JSON to `process.stdout` — structured, machine-readable, PII keys redacted
- **Development**: `console.log` with human-readable prefix — same redaction applies

### `userId` and `orgId` Are Always Logged

`logger.server.ts:148-149`: `userId` and `orgId` (mapped from `tenant_id`) are written as top-level fields in every log entry if present. These are internal IDs, not PII, but they are never redacted.

---

## 4. Admin Auth Model — The Honest Version

### The Login System (Server-Side)

The login system (`auth.server.ts:66-107`) is a real auth system:

- Password hashing: PBKDF2 with 100,000 iterations, SHA-512, 16-byte random salt (`auth.server.ts:13-17`)
- Timing-safe comparison on password verification (`auth.server.ts:23`)
- Session token: HMAC-signed JWT with `userId`, `orgId`, `role` (`session.server.ts:14-22`)
- Role hierarchy enforced server-side: `requireRole()` in `permissions.server.ts` with numeric levels (100/50/10)

This works. It's not fancy, but it's a functional auth system with proper password hashing and signed sessions.

### PasscodeGate — Removed

The client-side hardcoded-passcode speed bump (`"0726"` in `PasscodeGate.tsx`) was **deleted in Sprint 42**. The diagnostics page is now gated exclusively by server-side RBAC (`requireRole(SUPER_ADMIN)`) plus the app-wide session-revocation check in `requireOrg()`. No client-side-only "auth" remains.

### The Combined Model's Real Limitations

| Limitation | Impact |
|-----------|--------|
| **No brute-force protection on login** | `auth.server.ts:login()` has no rate limiting, lockout, or delay after failed attempts. An attacker can try passwords as fast as the network allows. |
| **Stolen tokens valid only while session row lives** | A token is revoked if its `user_sessions` row is deleted (logout) or if `SESSION_SECRET` is rotated. `isSessionActive()` (fail closed) is enforced on every tenant-scoped call via `requireOrg()` (`tenant.server.ts`). See `session.server.ts:50-63`. |
| **`SESSION_SECRET` defaults to a known value** | If not set in production, any attacker can forge session tokens. The warning at `env.server.ts:39-41` does not prevent this. |
| **`DEFAULT_ADMIN_PASSWORD` is `"admin0726"`** | First-time seeded admin uses this password. If not changed immediately after first login, the account is compromisable. |
| **`seedDefaultOrgAndAdmin()` runs on every login** | `auth.server.ts:74` calls `seedDefaultOrgAndAdmin()` on every login attempt. This is idempotent (checks for existing orgs), but it runs a `SELECT` on every login — a minor performance waste, and a schema setup attempt on every auth request. |
| **Role is a plain string in the JWT** | `role: "admin"` is client-asserted in the token. If a user's role is changed server-side, the old token still carries the old role until expiry. Session row state is only checked for existence (revocation), not for current role. |
| **No CSRF on `createServerFn` POST** | POST requests use `sameSite: "lax"` cookies, which provides partial CSRF protection (not sent on cross-origin POST). But `createServerFn` POST bodies are JSON, and `lax` does not protect against all attack vectors (e.g., top-level navigations). |

---

## 5. Recommendations (Unordered)

1. **Set `SESSION_SECRET` in production** and remove the default. This is the single most critical fix.
2. **Change `DEFAULT_ADMIN_PASSWORD`** after first login, or force a password change on first login.
3. **Add a logout endpoint** — call `clearCookie(SESSION_COOKIE)` server-side.
4. **Add rate limiting to `login()`** — e.g., 5 attempts per IP per minute, with progressive delay.
5. ~~**Remove `PasscodeGate.tsx`**~~ — Done in Sprint 42; diagnostics gated by server-side RBAC + session revocation.
6. **Add `iat` to `SessionPayload`** and check it — enables session invalidation by date.
7. **Use `getEnv()` in `config.server.ts`** instead of raw `process.env`.
8. **Remove `seedDefaultOrgAndAdmin()` from `login()`** — run it once at startup or via a dedicated setup route, not on every auth request.

---

*Last reviewed: Sprint 42 (PasscodeGate removed; app-wide session revocation enforced in `requireOrg()`)*
