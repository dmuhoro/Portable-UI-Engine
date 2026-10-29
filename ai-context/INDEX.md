# Daftari — AI Engineering Team

This folder contains specialized engineer agents for the Daftari SDLC.
Load the relevant agent(s) at the start of any Opencode session.

## Agent Routing Table

| Task type | Primary agent | Supporting agent |
|---|---|---|
| Architectural decision | architect.md | — |
| New React component | frontend.md | i18n.md |
| Schema change (Dexie or Supabase) | data.md | architect.md |
| Security review | security.md | data.md |
| Writing tests | test.md | — |
| M-Pesa / Daraja / SMS | integrations.md | data.md |
| CI/CD, deployment, versioning | devops.md | — |
| Adding i18n keys | i18n.md | frontend.md |
| Feature scope decision | product.md | architect.md |
| Bundle size, query performance | performance.md | frontend.md |

## Authority Hierarchy (who overrides whom)
architect.md        ← final word on offline-first, dependencies, ADRs
└── security.md   ← overrides frontend and data on auth/RLS/PII
└── data.md  ← overrides frontend on schema and sync
└── product.md  ← overrides all on scope (prevents overbuilding)
└── frontend.md, test.md, i18n.md, devops.md, performance.md, integrations.md

## How to invoke

Single agent:
  "Acting as the engineer in ai-context/security.md, review this component."

Multiple agents:
  "Acting as ai-context/data.md and ai-context/test.md, write the schema
   change and tests for the product catalog feature."

Full team review:
  "Route this task to the appropriate agents in ai-context/ and execute."

## Non-negotiables (enforced by ALL agents, no exceptions)

1. The UI never waits for the network. All reads from Dexie. Always.
2. All KES arithmetic through src/lib/money.ts. Never raw JS operators on amounts.
3. All UI text through t() from useTranslation. Never hardcoded strings.
4. All Dexie access through src/lib/repository.ts. Never import db.ts in features.
5. Every new i18n key in BOTH sw.json and en.json. Same commit.
6. No new npm dependencies without explicit human approval.
7. No PII in logs. Ever. (Names, phone numbers, amounts, business names.)
