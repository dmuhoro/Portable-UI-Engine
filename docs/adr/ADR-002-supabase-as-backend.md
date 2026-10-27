# ADR-002: Supabase as Backend

**Status:** Accepted  
**Date:** 2026-06-07

## Context
Daftari needs a backend for: authentication, cross-device sync, and
long-term data storage (financial records for credit readiness scoring).

## Decision
Use Supabase (managed Postgres + Auth + Row Level Security).
Share the same Supabase instance as EasyTutor with daftari_ table prefix.

## Consequences
**Positive:**
- RLS enforces data isolation at database level — not application level
- Auth is production-grade out of the box
- Shared instance reduces infrastructure cost
- Supabase free tier covers pilot phase (500MB DB, 50K MAU)

**Negative:**
- Vendor dependency — migration would require schema export + new client
- Free tier limits apply (mitigated by offline-first design that reduces API calls)
