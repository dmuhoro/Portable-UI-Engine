# ADR-004: SMS Parsing over Daraja API for MVP

**Status:** Accepted  
**Date:** 2026-06-07

## Context
The primary pilot user (Hellen) receives M-Pesa payments via Send Money
(P2P transfer), not via a registered till number. Daraja C2B only works
for registered Lipa Na M-Pesa till/paybill holders.

## Decision
MVP ships with SMS parsing (paste confirmation SMS → extract amount).
Daraja C2B is deferred to Phase 2 when vendor has a till number.
The source field in daftari_transactions reserves a 'daraja' slot.

## Consequences
**Positive:**
- Zero external API dependencies in MVP
- Works for all M-Pesa payment types (including Send Money)
- No Safaricom registration required from the user
- Fully offline capable

**Negative:**
- Manual step (user must paste SMS) — friction vs full automation
- User can paste incorrect SMS — mitigated by confirmation screen with edit

## Rollback
Schema already has source = 'daraja' slot. Daraja integration requires:
Supabase Edge Function + Safaricom developer account + till number.
No schema migration needed when Phase 2 ships.
