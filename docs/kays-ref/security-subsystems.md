# Security Subsystems

> Current state of encryption, RBAC, session management, and webhooks. Stated plainly — no euphemisms.

---

## 1. Encryption (`encryption.server.ts`)

### Algorithm

AES-256-GCM with per-org derived keys. Constants:

```
ALGORITHM = "aes-256-gcm"
IV_LENGTH = 16 bytes
TAG_LENGTH = 16 bytes
KEY_LENGTH = 32 bytes
SALT = "kays-wellness-pii-v1" (hardcoded, not per-org)
```

### Key Management

Each organization gets its own encryption key, derived from:

```ts
deriveKey(orgId, passphrase, version) = scryptSync(`${orgId}:${passphrase}:v${version}`, SALT, KEY_LENGTH)
```

- `passphrase`: a random 32-byte hex string, SHA-256 hashed and stored in `org_encryption_keys.key_hash`
- `version`: integer incremented on rotation
- `active`: boolean — only one key version is active at a time

**Key lifecycle:**
1. `getActiveKey(orgId)` — checks 5-minute in-memory cache, then queries DB for active key
2. If no key exists: `initializeOrgKey(orgId)` generates one (version 1)
3. On cache miss: queries `org_encryption_keys` for the specific version

### Key Rotation

`rotateOrgKey(orgId)` (`encryption.server.ts:190-222`):
1. Sets all existing keys for the org to `active = false`
2. Generates a new random passphrase
3. Inserts new key at `version = max_version + 1` with `active = true`
4. Clears the in-memory cache for that org
5. Returns the new version number

**Critical limitation:** Rotation does NOT re-encrypt existing ciphertexts. Data encrypted with version 1 remains encrypted with version 1. `decryptPII()` reads `payload.keyVersion` from the ciphertext and fetches the correct key version for decryption. This means old data remains decryptable even after rotation — the rotation only affects new encryptions.

**Is this a problem?** Not for confidentiality — the old key is still in the DB and usable. Rotation is useful only if the current active key is compromised and you want to stop future encryptions with it. It does NOT provide forward secrecy.

### Encryption/Decryption Flow

```ts
// Encryption
const payload: EncryptedPayload = { iv, tag, data, keyVersion };
return `ENC:${JSON.stringify(payload)}`;

// Decryption
const payload: EncryptedPayload = JSON.parse(ciphertext.slice(4));
const { key } = await getKeyByVersion(orgId, payload.keyVersion);
// ... decrypt with AES-256-GCM ...
```

Format: `ENC:{"iv":"hex","tag":"hex","data":"hex","keyVersion":1}`

### In-Memory Cache

```ts
orgKeyCache = Map<string, { key: Buffer; version: number; ts: number }>()
KEY_CACHE_TTL_MS = 5 * 60 * 1000  // 5 minutes
```

Two entries per key: `orgId` (active) and `orgId:v{N}` (specific version). `wipeKeyCache()` clears everything.

### What's Encrypted

The `encryptFields()` and `decryptFields()` helpers accept a list of field names to encrypt/decrypt on any record. Currently, **no code in the codebase actually calls `encryptPII()` or `decryptPII()` on live data** — the infrastructure exists but is not wired into any lead, invoice, or message flow.

**Status:** Encryption infrastructure is built and tested (`encryption.test.ts`), but PII fields are stored in plaintext in the database. The encryption subsystem is ASPIRATIONAL — it works but is not in use.

---

## 2. RBAC (`permissions.server.ts`)

### Role Definitions

```ts
ROLES = {
  SUPER_ADMIN: "super_admin",   // level 100
  CLINIC_OWNER: "admin",        // level 50
  CLINIC_STAFF: "staff",        // level 10
}
```

### Where Roles Are Checked

| Guard | File | What it protects |
|-------|------|-----------------|
| `requireRole(ROLES.SUPER_ADMIN)` | `diagnostics.server.ts:38` | `getQueueTelemetry` |
| `requireRole(ROLES.SUPER_ADMIN)` | `diagnostics.server.ts:59` | `forceRetryQueueItems` |
| `requireRole(ROLES.SUPER_ADMIN)` | `diagnostics.server.ts:85` | `getFailedQueueItems` |
| `requireRole(ROLES.SUPER_ADMIN)` | `telemetry.server.ts` | `getMilestoneStats` |
| `requireRole(ROLES.SUPER_ADMIN, ROLES.CLINIC_OWNER)` | `leads.server.ts:253` | `deleteLead` |
| `requireRole(ROLES.SUPER_ADMIN, ROLES.CLINIC_OWNER)` | `billing.server.ts:227` | `generateInvoiceForCheckedIn` |
| `requireRole(ROLES.SUPER_ADMIN, ROLES.CLINIC_OWNER)` | `billing.server.ts:253` | `fetchInvoices` |
| `requireRole(ROLES.SUPER_ADMIN, ROLES.CLINIC_OWNER)` | `billing.server.ts:279` | `addPayment` |

### What's NOT Server-Gated

These capabilities have NO `requireRole()` check on the server:

| Capability | Server function | Any authenticated user can... |
|-----------|----------------|------------------------------|
| Submit lead | `submitLead` | Create leads in any org they belong to |
| Update lead | `updateLead` | Change status/priority of any lead |
| Fetch leads | `fetchLeads` | View all leads in their org |
| Book slot | `bookSlot` | Book appointments |
| Log interaction | `logInteraction` | Record interactions |
| Trigger automation | `triggerAutomation` | Run the automation orchestrator |
| Save clinic config | `saveClinicConfig` | Change business hours, slot duration |
| Create resource | `createResourceFn` | Add providers/rooms |
| Fetch analytics | `getAnalytics` | View all analytics |
| Register webhook | `registerWebhook` | Register outbound webhooks |

**This means any `staff` user can do almost everything.** The RBAC system distinguishes between SUPER_ADMIN/CLINIC_OWNER and STAFF only for: delete lead, billing operations, queue diagnostics, and milestone stats. Everything else is unguarded.

### Client-Side Role Checks (UI Only)

These functions in `permissions.server.ts` are used in React components to hide/show UI elements:

- `canAccessFinance(role)` — hides finance tabs for staff
- `canAccessDataExport(role)` — hides data export for staff
- `canDeleteData(role)` — hides delete buttons for staff
- `canAccessAdminSettings(role)` — hides admin settings for staff

**These are purely cosmetic.** A staff user who calls the server functions directly (e.g., via `fetch` or DevTools) can still perform these operations. The server does NOT enforce these checks.

**DECISION NEEDED:** Should `staff` users be restricted from: updating leads, booking slots, triggering automation, saving clinic config? Currently only billing and diagnostics are gated. If the pilot includes staff users, this is a gap.

---

## 3. Session/JWT (`session.server.ts`)

### Token Structure

```ts
SessionPayload = {
  userId: number;      // from users.id
  orgId: string;       // from organizations.id (UUID)
  role: string;        // 'super_admin' | 'admin' | 'staff'
  exp: number;         // Date.now() + 86_400_000 (24 hours)
}
```

### Signing

```
token = base64url(JSON(payload)) + "." + HMAC-SHA256(encoded, SESSION_SECRET).slice(0, 32)
```

- Algorithm: HMAC-SHA256
- Truncated to 32 hex characters (not full 64)
- `SESSION_SECRET` from env (minimum 32 chars, defaults to `"dev-secret-change-in-prod"`)

### Verification

1. Split token on `.`
2. Re-compute HMAC of the encoded part
3. `crypto.timingSafeEqual()` comparison
4. Parse JSON payload
5. Check `Date.now() > payload.exp` — reject if expired

### Cookie Settings

```
name: kwc_session
httpOnly: true
secure: true
sameSite: "lax"
path: "/"
maxAge: 86400  (24 hours)
```

### What's Missing

- **No `iat` (issued-at)** — cannot invalidate tokens issued before a certain time
- **No `jti` (token ID)** — cannot revoke individual tokens
- **No refresh token** — single token, single 24-hour window
- **No logout** — no `clearCookie()` call exists anywhere in the codebase
- **No server-side session store** — the JWT is the only session state
- **Role changes not reflected** — if a user's role is changed in the DB, the old JWT still carries the old role until expiry

---

## 4. Webhooks (`webhooks.server.ts`)

### Registration

`registerWebhook(orgId, url, events)` generates a random 32-byte hex secret and stores it in `webhook_configs`. The secret is used for HMAC signing.

### Signature Algorithm

```ts
signPayload(payload, secret) = HMAC-SHA256(payload, secret).digest("hex")
```

Sent as header: `X-Clinic-Signature: sha256={hex_signature}`

### Verification

```ts
verifyWebhookSignature(payload, signature, secret):
  expected = HMAC-SHA256(payload, secret).digest("hex")
  sig = signature.startsWith("sha256=") ? signature.slice(7) : signature
  timingSafeEqual(sig, expected)
```

Supports both `sha256=hex` and raw hex format.

### Replay Protection

**There is none.** The webhook system does not include:
- Nonces or timestamps in the signed payload
- Deduplication of received webhooks
- Expiry of signatures

The signed payload is: `{"event": "...", "timestamp": "...", "payload": {...}}`. The `timestamp` field is included in the body but is NOT included in the signature — wait, actually it IS included because `signPayload` signs the entire JSON body string. But the receiving end has no mechanism to reject old timestamps.

### Delivery & Retry

- `dispatchWebhook()` sends to all active webhook configs matching the event type (or `*`)
- Retry: exponential backoff via `POWER(2, retry_count) minutes` (`webhooks.server.ts:170`)
- Max retries: 3 (default)
- Timeout: 10 seconds (`AbortSignal.timeout(10_000)`)
- Statuses: `pending` → `success` / `retrying` / `failed`
- 5xx responses trigger retry; 4xx does not

### Delivery Tracking

Every delivery is recorded in `webhook_deliveries` with: status, response_code, response_time_ms, error_message, retry_count. `getDeliveryStats()` returns aggregate counts. `retryPendingDeliveries()` re-sends eligible retries.

---

## 5. Summary of Gaps

| Subsystem | Gap | Risk |
|-----------|-----|------|
| Encryption | Not wired into any live data flow — PII stored in plaintext | Medium — infrastructure exists but unused |
| Encryption | Key rotation doesn't re-encrypt old data — old ciphertexts remain decryptable with old keys | Low — old keys stay in DB |
| RBAC | Most server functions have no role check — any authenticated user can do almost anything | High if staff users exist in pilot |
| RBAC | Client-side role checks (`canAccessFinance` etc.) are cosmetic only | Low — server is the real gate |
| Session | No token revocation, no logout, no refresh | Medium — 24-hour window |
| Session | Role changes not reflected until token expiry | Low — unlikely to change mid-session |
| Webhooks | No replay protection on inbound webhooks | Medium — depends on webhook sender |
| Webhooks | Signature covers body but receiver has no timestamp validation | Low — body includes timestamp but isn't checked |

---

*Documented from source: Sprint 34*
