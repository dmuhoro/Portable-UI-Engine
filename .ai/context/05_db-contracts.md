# DB Contracts Brief

> Condensed from `docs/db-contracts.md`. Canonical file wins on conflict.

## Conventions

- Tenant column: `organization_id UUID` on most tables; `tenant_id UUID` on `notification_queue`,
  `audit_logs`, `live_events` (documented inconsistency — do NOT replicate in new tables).
- Writes: only files that INSERT/UPDATE/DELETE are listed.
- All DDL lives in `db.server.ts:ensureSchema()` — `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE`
  guarded by information_schema checks. No separate migration system.

## Tenant-Scoping Rule

Every new table MUST have `organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE`
(or appropriate) + indexes. STK Push table follows this pattern.

## Coupling Risks (know before editing)

| Table | Writers |
|-------|---------|
| `clinic_leads` | api/leads, api/scheduling, api/resources — **HIGH** |
| `notification_queue` | queue, api/diagnostics — LOW |
| `invoices`/`payments` | api/billing, reconciliation, api/mpesa (NEW) — MEDIUM |

When `api/mpesa` writes payments, route through shared helpers (`recordPayment`) + the same locks so
receipt-number minting stays race-free.

## Table Checklist for New STK Push Table

```sql
CREATE TABLE IF NOT EXISTS mpesa_stk_push_requests (
  id SERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  invoice_id INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
  lead_id INTEGER REFERENCES clinic_leads(id) ON DELETE SET NULL,
  amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
  phone VARCHAR(30) NOT NULL,
  account_reference VARCHAR(50) NOT NULL,
  transaction_desc VARCHAR(100) NOT NULL DEFAULT '',
  merchant_request_id VARCHAR(50),
  checkout_request_id VARCHAR(50),
  result_code INTEGER,
  result_desc TEXT,
  mpesa_receipt_number VARCHAR(30),
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','success','failed')),
  raw_response JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mpesa_stk_org_created ON mpesa_stk_push_requests (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mpesa_stk_checkout ON mpesa_stk_push_requests (checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_mpesa_stk_status ON mpesa_stk_push_requests (status);
```