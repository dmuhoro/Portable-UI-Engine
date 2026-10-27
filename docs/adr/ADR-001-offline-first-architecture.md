# ADR-001: Offline-First Architecture with Dexie.js

**Status:** Accepted  
**Date:** 2026-06-07  
**Deciders:** Daniel Muhoro

## Context
Daftari's target users (Kenyan informal vendors) operate in environments with
unreliable mobile data. Network requests may fail mid-transaction. Any
architecture that requires a network connection for core operations would
be unusable for a significant portion of Hellen's working day.

## Decision
All UI reads come from Dexie.js (IndexedDB). All writes go to Dexie first,
then queue for Supabase sync. The UI never waits for the network.

## Consequences
**Positive:**
- App works fully on airplane mode
- Zero loading spinners for core operations (< 100ms response)
- User never loses a transaction due to connectivity

**Negative:**
- Two sources of truth must be kept in sync (Dexie + Supabase)
- Conflict resolution needed for concurrent edits (handled by local_id dedup)
- Dexie storage is capped (~50-250MB depending on device)

## Alternatives considered
- **Online-first with optimistic UI:** Faster to build, unusable in low-connectivity
- **LocalStorage only:** No structured querying, 5MB limit
- **Service worker cache only:** Cannot store structured transactional data
