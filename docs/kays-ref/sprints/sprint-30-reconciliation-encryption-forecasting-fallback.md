# Sprint 30 — Autonomous Ledger Reconciliation, Zero-Knowledge PII Encryption, Pipeline Forecasting, Communication Fallback Routing

**Theme:** Intelligent financial automation and data protection: autonomous M-Pesa/bank
transaction reconciliation against pending invoices, AES-256-GCM zero-knowledge PII
encryption for patient intake notes, conversion velocity analytics with revenue-at-risk
forecasting, and multi-channel communication fallback routing with circuit breaker protection.

## Pillars

### 1. Autonomous Ledger Reconciliation Engine
- `src/lib/reconciliation.server.ts` — Intercepts inbound M-Pesa/bank payment messages and auto-reconciles against pending invoices:
  - `parseInboundPayment(message)` — Regex-based extraction of transaction references, amounts, and phone numbers from Safaricom M-Pesa format (`SBI*`, `Q*` prefixed refs) and bank reference formats (`REF:`, `TXN:`, `REFERENCE:`).
  - `reconcilePayment(orgId, parsed)` — Cross-references parsed payment against pending invoices by amount matching (±0.01 tolerance), with phone number disambiguation when multiple candidates exist.
  - `processInboundPaymentMessage(orgId, messageBody)` — Single-step parse + reconcile API.
  - `getReconciliationLog(orgId, limit)` — Audit trail of all reconciliation attempts.
- **Atomic operations:** Advisory lock on `reconcile:{orgId}`, `FOR UPDATE` on invoice rows, automatic payment recording + invoice status update on match, SSE live push on successful reconciliation.
- **DB Schema** — `reconciliation_log` table with columns: organization_id, inbound_reference, inbound_amount, inbound_phone, matched_invoice_id, matched_payment_id, status (pending/matched/auto_paid/unmatched), metadata (JSONB).

### 2. Zero-Knowledge PII Encryption Vault
- `src/lib/encryption.server.ts` — AES-256-GCM encryption at application boundary for patient intake notes:
  - `encryptPII(orgId, plaintext)` — Encrypts using org-derived key via `scrypt` key derivation, random IV, and authenticated encryption. Returns `ENC:{json}` format.
  - `decryptPII(orgId, ciphertext)` — Decrypts with the org's active key; throws on wrong key or corrupted data.
  - `encryptFields(orgId, record, fields)` — Batch encrypt specified fields on any record object.
  - `decryptFields(orgId, record, fields)` — Batch decrypt specified fields; skips non-encrypted values.
  - `isEncrypted(value)` — Type guard for `ENC:` prefixed strings.
  - `rotateOrgKey(orgId)` — Generates new encryption key, deactivates old key; previous ciphertexts remain decryptable until key cache expires.
  - `wipeKeyCache()` — Clears in-memory key cache (for testing).
- **Key management:** Org-scoped keys stored in `org_encryption_keys` table, versioned for rotation, cached in memory with 5-minute TTL. Database admins cannot read patient notes — zero-knowledge architecture.
- **DB Schema** — `org_encryption_keys` table with columns: organization_id, key_version, key_hash, active, UNIQUE(organization_id, key_version).

### 3. Pipeline Conversion Velocity & Revenue-at-Risk Forecasting
- `src/lib/forecasting.server.ts` — Historical cohort analytics for executive decision-making:
  - `computeConversionVelocity(orgId)` — Stage-to-stage transition metrics using window functions on `lead_interactions` (avg/median hours, sample size per transition).
  - `computeRevenueAtRisk(orgId)` — Leads stalled beyond expected velocity thresholds: low (<24h), medium (24-72h), high (72-168h), critical (>168h).
  - `computePipelineForecast(orgId)` — Full pipeline forecast with conversion velocity, revenue at risk, and summary stats (total leads, conversion rate, projected monthly revenue).
- Uses `PERCENTILE_CONT(0.5)` for median calculation, `LAG()` window functions for transition detection, and time-weighted revenue projections.

### 4. Multi-Channel Communication Fallback Routing
- `src/lib/fallback.server.ts` — Resilient message delivery with automatic channel fallback:
  - `recordDeliveryAttempt(orgId, channel, success)` — Updates channel health metrics; opens circuit breaker after 5 consecutive failures (15-minute cooldown).
  - `getAvailableChannels(orgId)` — Returns channels with closed circuit breakers, prioritized: webhook → WhatsApp → SMS.
  - `sendWithFallback(orgId, recipient, message, primaryChannel, sendFn)` — Tries primary channel first; on failure, cascades through available channels until delivery succeeds or all fail.
  - `getChannelHealthReport(orgId)` — Dashboard-ready health metrics for all channels.
  - `resetChannelCircuit(orgId, channel)` — Manual circuit breaker reset for admin intervention.
- **Circuit breaker pattern:** Tracks success/fail counts per channel, automatically disables degraded channels, and re-enables after cooldown period.
- **DB Schema** — `channel_health` table with columns: organization_id, channel (webhook/sms/whatsapp), success_count, fail_count, last_success_at, last_failure_at, circuit_open, circuit_open_until, UNIQUE(organization_id, channel).

## Test Coverage

| File | Tests |
|---|---|
| `reconciliation.test.ts` | 12 — M-Pesa parsing, bank parsing, single/multi-invoice matching, phone disambiguation, unmatched handling, log retrieval, end-to-end |
| `encryption.test.ts` | 15 — Round-trip encryption, field operations, key init/rotation, isEncrypted, wrong-key rejection, decryption failure, cache management |
| `forecasting.test.ts` | 10 — Velocity computation, risk level classification (critical/high/medium/low), pipeline summary, zero leads, revenue projection scaling |
| `fallback.test.ts` | 15 — Channel health tracking, circuit breaker open/close, available channels filtering, fallback cascade, exception handling, all-channels-failed, manual reset |

**Total:** 407 tests across 44 files — all passing.

## Database Changes

```sql
CREATE TABLE reconciliation_log (
  id SERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  inbound_reference VARCHAR(100) NOT NULL,
  inbound_amount NUMERIC(12,2) NOT NULL,
  inbound_phone VARCHAR(30),
  matched_invoice_id INTEGER REFERENCES invoices(id),
  matched_payment_id INTEGER REFERENCES payments(id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE org_encryption_keys (
  id SERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  key_version INTEGER NOT NULL DEFAULT 1,
  key_hash VARCHAR(128) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(organization_id, key_version)
);

CREATE TABLE channel_health (
  id SERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('webhook', 'sms', 'whatsapp')),
  success_count INTEGER NOT NULL DEFAULT 0,
  fail_count INTEGER NOT NULL DEFAULT 0,
  last_success_at TIMESTAMP WITH TIME ZONE,
  last_failure_at TIMESTAMP WITH TIME ZONE,
  circuit_open BOOLEAN NOT NULL DEFAULT false,
  circuit_open_until TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(organization_id, channel)
);
```

## Key Architectural Decisions

1. **Zero-knowledge encryption:** Patient intake notes are encrypted at the application layer before persistence. Database administrators and DevOps teams cannot read sensitive patient data — only authorized clinic staff with org context can decrypt.

2. **Phone-based disambiguation:** When multiple invoices match the same amount, the reconciliation engine queries lead phone numbers to find the correct match, falling back to most-recent-first when phone data is unavailable.

3. **Circuit breaker over retry loops:** Rather than infinite retries on degraded channels, the fallback system uses a circuit breaker pattern with exponential cooldown — preventing cascade failures and giving infrastructure time to recover.

4. **Synchronous pipeline stats in Promise.all:** The forecasting engine runs three async computations in parallel (velocity, risk, pipeline stats) via `Promise.all`, but the pipeline stats query is passed directly as a synchronous `db.unsafe()` call that starts before the other async functions resolve past their `await getDb()`.
