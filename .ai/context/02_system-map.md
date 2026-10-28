# System Map

> Where code lives. Condensed from `docs/architecture.md` §3, §7 and the actual tree.

## Root

```
src/
  __tests__/          ← Vitest suite (58 files, 667 tests passing)
  routes/             ← TanStack file-based routes
    __root.tsx        ← root layout
    index.tsx         ← landing
    services.tsx, our-story.tsx, resources.tsx, contact.tsx,
    register.tsx, privacy-policy.tsx, terms.tsx
    admin/
      login.tsx, dashboard.tsx, triage.tsx, finance.tsx, diagnostics.tsx
      settings/{billing,data,developer,operations}.tsx
      system/diagnostics.tsx
    api/
      health.ts, calendar-sync.ts
      cron/automation-orchestrator.ts
      streams/live-updates.ts
      webhooks/whatsapp.ts
  lib/                ← server + shared logic
    *.server.ts       ← core infra, auth, tenant, subs, messaging, integrations
    api/*.server.ts   ← createServerFn API layer
    marketing/*.server.ts
    schemas/client-validators.ts
  components/         ← React components (finance/, leads/, ...)
  data/, hooks/, scripts/
  server.ts, start.ts, router.tsx, routeTree.gen.ts (AUTO-GENERATED)
```

## Money Paths (where payments are recorded)

| Path | File | Locks |
|------|------|-------|
| Manual invoice | `src/lib/api/billing.server.ts:generateInvoice` | `invoice_seq:{orgId}` |
| Manual payment | `src/lib/api/billing.server.ts:recordPayment` | `payment:{orgId}:{invoiceId}` |
| M-Pesa CSV recon | `src/lib/reconciliation.server.ts:reconcilePayment` | `reconcile:{orgId}` |
| Subscription checkout | `src/lib/checkout.server.ts:initiateCheckout` | `checkout:{orgId}` |
| STK Push (NEW) | `src/lib/api/mpesa.server.ts` (to create) | `mpesa_stk:{orgId}` |

## Webhook Entrypoints (h3 eventHandlers in routes/api/webhooks/)

| File | Purpose |
|------|---------|
| `whatsapp.ts` | WhatsApp Cloud API — GET verify + POST inbound, signature check, media ingest |
| `mpesa.ts` (NEW) | M-Pesa Daraja STK Push callback — POST, callback-secret auth, idempotent payment |

## Tests by Area

| Area | Test file(s) |
|------|-------------|
| Tenant isolation | `tenant-isolation-p0.test.ts` (22 adversarial) |
| Billing | `billing.test.ts`, `billing-locks.test.ts` |
| Scheduling | `scheduling-injection.test.ts`, `concurrency.test.ts`, `slot-generation.test.ts` |
| Reconciliation | `reconciliation.test.ts` |
| WhatsApp dispatch | `dispatch.test.ts`, `messaging.test.ts`, `rate-limit.test.ts` |
| Encryption | `encryption.test.ts` |
| RBAC | `rbac-completeness.test.ts`, `permissions.test.ts` |
| Subscription | `subscriptions.test.ts`, `metering.test.ts`, `trials.test.ts` |
| Queue | `notification-queue.test.ts`, `queue-diagnostics.test.ts` |
| E2E | `e2e-simulation.test.ts` |

## Docs Map

```
docs/
  architecture.md, code-standards.md, db-contracts.md, decisions.md,
  pilot-scope-day-1.md, release-readiness.md, security.md, security-subsystems.md,
  sprint-cross-reference.md
  sprints/            ← sprint notes (sprint-1 … sprint-34)
  adr/                ← NEW: formal ADR records
  engineering/        ← NEW: CONSTITUTION.md + build principles
  evidence/           ← NEW: evidence logs
  releases/           ← NEW: release notes
  runbooks/           ← NEW: operational runbooks
```