# ADR-005: Multi-Category Business Architecture

**Status:** Accepted  
**Date:** 2026-06-18

## Context
Daftari started as a chapati-vendor-specific tool. The vision expanded
to serve all of Kenya's informal sector (7 categories, 20+ subcategories).

## Decision
Business categories are defined as a typed constant in businessCategories.ts.
Each category carries its own expense categories, product templates, and
payment method defaults. The business record stores category + subcategory.
The UI personalizes based on these fields.

## Consequences
**Positive:**
- Single codebase serves all informal business types
- Expense categories are relevant to each user's actual business
- Quick-add items reflect what the user actually sells
- Extensible — new categories added by extending the constant

**Negative:**
- Onboarding flow is longer (4 steps vs 1)
- Template products must be maintained per subcategory
- UI must handle all category permutations without breaking
