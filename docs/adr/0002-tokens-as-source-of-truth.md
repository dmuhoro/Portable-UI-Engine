# ADR 0002: Tokens as Source of Truth

## Status
Accepted

## Context
Theme presets and tokens are currently scattered in theme.css. Need single source of truth.

## Decision
Store tokens in W3C Design Token JSON format in `packages/tokens/design-tokens.json`. Generate all outputs:
- CSS custom properties
- Tailwind preset
- TypeScript types

## Consequences
- Machine-readable, versionable
- Consistent across platforms
- Easier to validate contrast/accessibility
- Generator becomes part of pipeline
