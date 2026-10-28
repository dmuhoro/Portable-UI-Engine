# ADR-006: Dexie.js as Local Database

**Status:** Accepted  
**Date:** 2026-06-07

## Context
Offline-first requires structured local data storage with querying capability.

## Decision
Use Dexie.js v3 as the IndexedDB abstraction layer.

## Rationale
- Typed schema with TypeScript generics
- Compound indexes for efficient date-range queries
- Version migration system for schema evolution
- 4KB minified — negligible bundle impact
- Well-maintained, 10+ years production history

## Alternatives considered
- **Raw IndexedDB:** No typed interface, verbose API, error-prone
- **SQLite (wa-sqlite):** WASM bundle ~3MB, overkill for this data model
- **PouchDB:** Designed for CouchDB sync, unnecessary complexity
