# Domain Model

> Entities and their tenant-scoping verdicts. Condensed from `docs/db-contracts.md`.

## Tenant Root

**organizations** — NOT scoped (it IS the tenant root). Columns: id UUID PK, name, slug UNIQUE,
timezone, settings JSONB, subscription_tier/status/expires_at, leads_used, storage_used_bytes,
trial_* , onboarding_*.

## Tenant-Scoped Entities

| Entity | Table | Tenant col | Writers |
|--------|-------|-----------|---------|
| Users | `users` | `organization_id` | auth, registration |
| Leads | `clinic_leads` | `organization_id` | **3 files: api/leads, api/scheduling, api/resources — HIGH coupling** |
| Availability | `clinic_availability` | `organization_id` | auth (seed), scheduling |
| Automation | `automation_state` | `organization_id` | api/automation |
| Clinic config | `clinic_configuration` | `organization_id` | api/clinic-config |
| Resources | `resources` | `organization_id` | api/resources |
| Invoices | `invoices` | `organization_id` | api/billing |
| Payments | `payments` | `organization_id` | api/billing |
| Interactions | `lead_interactions` | `organization_id` | api/interactions |
| Slot reservations | `slot_reservations` | `organization_id` | api/scheduling |
| Webhook configs/deliveries | `webhook_configs`, `webhook_deliveries` | `organization_id` | webhooks |
| Message ledger | `message_ledger` | `organization_id` | messaging |
| Reconciliation | `reconciliation_log` | `organization_id` | reconciliation |
| Enc keys | `org_encryption_keys` | `organization_id` | encryption |
| Channel health | `channel_health` | `organization_id` | fallback |
| Milestones | `product_milestones` | `organization_id` | telemetry |
| Checkout | `checkout_sessions` | `organization_id` | checkout |
| Retention | `retention_tasks` | `organization_id` | marketing/automation |
| Satisfaction | `satisfaction_prompts`, `feedback_responses`, `review_submissions`, `review_guard_config` | `organization_id` | marketing/reviews |
| STK Push (NEW) | `mpesa_stk_push_requests` | `organization_id` | api/mpesa |

## Known `tenant_id` Inconsistency (do NOT replicate)

| Table | Note |
|-------|------|
| `notification_queue` | `tenant_id`, no FK to organizations |
| `audit_logs` | `tenant_id`, FK to organizations |
| `live_events` | `tenant_id`, FK to organizations |

New tables MUST use `organization_id` + FK.

## Money Model

- **Invoice:** `invoices` — status `draft → issued → paid → void`, `INV-YYYY-NNNNN`
- **Payment:** `payments` — method `cash | mobile_money | card`, `KWC-YYYY-NNNNN`
- **Reconciliation:** `reconciliation_log` — status `pending | matched | auto_paid | unmatched`
- **Checkout:** `checkout_sessions` — status `pending | processing | completed | failed | expired`
- **STK Push (NEW):** `mpesa_stk_push_requests` — status `pending | success | failed`, tracked by
  `checkout_request_id`, merchant/checkout refs, result code, receipt number. On success → payment
  via the same `recordPayment` locks, idempotent by `checkout_request_id + receipt`.

## Coupling Risks

| Table | Writers | Risk |
|-------|---------|------|
| `clinic_leads` | api/leads, api/scheduling, api/resources | **HIGH** — coordinate all three |
| `notification_queue` | queue, api/diagnostics | LOW |
| `invoices`/`payments` | api/billing, reconciliation, **api/mpesa (NEW)** | MEDIUM — STK success writes a payment + marks invoice paid through shared helpers |