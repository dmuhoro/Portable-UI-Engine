# ADR-008: Audit Chain — SHA256 over Canonical Serialization

**Status:** Accepted
**Date:** 2026-07-29
**Driver:** WP-10.1 / Ω.1 — replace non-deterministic `hash()` with deterministic SHA256; content-integrity hash recomputation in `verify_chain()`

## Context

The audit chain links entries via `previous_hash`. The original implementation used Python's built-in `hash()` function — which is non-deterministic across interpreter restarts (PYTHONHASHSEED randomization), not cryptographically secure, and platform-dependent. Additionally, the pipe-delimiter serialization (`"|".join(parts)`) creates an ambiguity bug: any field containing `|` silently corrupts the canonical payload.

The original `verify_chain()` only checked link integrity (`entry[i].previous_hash == entry[i-1].hash`) but did **not** recompute each entry's hash from its field values. This meant tampering with `action`, `actor`, `resource`, `detail`, or `timestamp` of an existing entry went undetected. Programme Ω.1 fixed this: `verify_chain()` now recomputes every entry's expected hash from its own fields and compares against the stored hash.

## Decision

1. Replace `hash()` with `hashlib.sha256().hexdigest()` over a canonical JSON-serialized payload of all seven auditable fields.
2. Canonical serialization uses `json.dumps(fields, separators=(",", ":"), ensure_ascii=True)` — a list (not dict) preserves field order and eliminates delimiter-collision bugs.
3. `verify_chain()` in every backend recomputes each entry's expected hash from the entry's own fields and compares against the stored hash PLUS verifies the previous_hash link. This detects any mutation of id, action, actor, resource, detail, timestamp, previous_hash, or hash.
4. Do **not** retroactively rehash existing entries in the database. Entries recorded before this ADR was deployed retain their original `hash()` values. This creates a verifiable chain boundary at the deployment timestamp.

## Pre-fix Chain Boundary

- **Legacy entries** (pre-ADR-008): hash computed with `hash("|".join(parts))` — non-deterministic, pipe-delimiter serialization.
- **Post-fix entries** (ADR-008 onward): hash computed with SHA256 over canonical JSON — deterministic, cryptographically secure, content-integrity verified.
- `verify_chain()` recomputes the expected hash using the **current** method (SHA256). Legacy entries will **fail** verification because `hash()` is non-deterministic across restarts. This is an accepted consequence: the pre-fix chain is considered a best-effort audit trail, not a cryptographically verifiable one.
- Operators with access to the pre-fix database can manually verify legacy entries by running the same `hash()` call within a single interpreter session (pre-fix entries recorded in the same process are verifiable until restart).

## Consequences

- **Positive:** Deterministic, collision-resistant, tamper-evident audit hashes. Content-integrity verification catches mutation of any auditable field. Pipe-delimiter bug eliminated. Cryptographically secure. Verified deterministic across PYTHONHASHSEED values (0, 1, 42, 12345, 99999).
- **Negative:** Existing audit entries recorded before this ADR cannot be re-verified after an interpreter restart. The chain has a permanent seam at the deployment boundary.
- **Mitigation:** Record a chain-boundary audit entry at deployment time that explicitly links the last legacy hash to the first SHA256 entry, documenting the transition.

## Implementation

- `infrastructure/audit.py` exports `compute_audit_hash(...)` used by all three audit backends (InMemory, SQLite, PostgreSQL).
- Canonical form: `json.dumps([id, action, actor, resource, detail, timestamp_iso, previous_hash], separators=(",", ":"))`.
- Hash: `hashlib.sha256(canonical.encode("utf-8")).hexdigest()`.
- `verify_chain()` in each backend: iterates all entries, recomputes hash from fields via `compute_audit_hash()`, compares to stored hash, and checks `previous_hash` link integrity.
- Six-field mutation tests (InMemory + SQLite backends): each auditable field action, actor, resource, detail, timestamp, previous_hash individually mutated and detected.
- Multi-seed verification: hash computation is proven identical across PYTHONHASHSEED=0,1,42,12345,99999 via subprocess isolation.
