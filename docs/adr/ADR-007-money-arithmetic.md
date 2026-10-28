# ADR-007: Centralized Money Arithmetic

**Status:** Accepted  
**Date:** 2026-06-18

## Context
JavaScript floating-point arithmetic produces incorrect results for currency:
  0.1 + 0.2 === 0.30000000000000004  // true in JS

For a financial application serving informal vendors, incorrect profit
calculations are a critical failure mode that destroys user trust.

## Decision
All KES arithmetic must go through src/lib/money.ts.
The KES branded type prevents raw numbers from being used as amounts.
All amounts are stored and displayed as whole shillings (integer).
Math.round() is applied at every arithmetic boundary.

## Why not a decimal library?
decimal.js and big.js add ~30KB to the bundle. For whole-shilling KES
amounts (no paise in practice), Math.round-based arithmetic is sufficient
and eliminates the dependency.

## Enforcement
ESLint rule (future): ban direct + - * / operators on variables named
'amount', 'profit', 'revenue', 'expense'. All calculations through money.ts.
