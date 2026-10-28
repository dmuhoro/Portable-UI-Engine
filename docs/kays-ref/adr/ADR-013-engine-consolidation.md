# ADR-013 — Engine Consolidation: kays-wellness-centre Is the Single Engine

**Status:** Accepted
**Date:** 2026-08-25
**Applies to:** All repos in the healthcare niche

---

## Context

Three repositories exist in the same niche:

- `dmuhoro/kays-wellness-centre` — TanStack Start + raw Postgres clinic-ops SaaS with **667 tests
  passing across 58 files**, WhatsApp bilingual dispatch, M-Pesa reconciliation, subscriptions,
  metering, RBAC, tenant isolation (22 adversarial tests), queue, SSE, webhooks, encryption.
- `dmuhoro/greenleaf-dental` — Next.js 16 + Supabase UI shell with a strong Supabase schema
  (multi-clinic, M-Pesa STK Push migration, RLS) but **one placeholder test** and no WhatsApp / no
  M-Pesa webhook routes.
- `dmuhoro/dentalos-kenya` — static React UI prototype (dashboard/patients/billing mockups) on hardcoded data.

An earlier strategy (proposed by an external agent) suggested greenleaf-dental was "the engine" and
kays-wellness-centre was "just a content site." **This is contradicted by the code.** kays is the
complete, tested engine; greenleaf is the untested UI shell.

## Decision

1. **kays-wellness-centre is the single engine** for the healthcare niche. All future clinic-ops work
   happens here.
2. **greenleaf-dental is a donor only.** Its M-Pesa STK Push migration and Daraja API patterns are
   ported into kays. No new feature is built on greenleaf as a runtime.
3. **dentalos-kenya is a UI donor only.** Its dashboard/patient/billing screen designs may be ported
   later as tenant themes; it is never a runtime.
4. No code is merged between build systems (TanStack vs Next.js vs Vite/Wouter are incompatible as
   code — they merge as design/schema material into one engine).

## Consequences

- Development effort concentrates on kays (one codebase, tenant-configured, serving Dr. Jackie).
- Test coverage is preserved (667 tests stay green; new code adds to them).
- The M-Pesa STK Push schema is ported with kays conventions: `organization_id` scoping (not
  `clinic_id`), kays locks/helpers, kays env names.
- Repos are not deleted — they remain as donor references.

## Alternatives Rejected

- **greenleaf as engine** — would require rebuilding WhatsApp, billing, RBAC, tenant isolation, and a
  full test suite on an untested base. Weeks of regression risk for zero gain.
- **dentalos as engine** — static mockups, no backend at all.
- **Running three apps** — duplicate infrastructure, no shared tenant model, no consolidation value.