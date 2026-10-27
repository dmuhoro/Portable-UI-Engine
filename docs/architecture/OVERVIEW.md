# Architecture Overview

## System Design
Portable UI Engine is evolving into a monorepo-based design system:

```
packages/engine  -> Core Web Components (Shadow DOM, zero deps)
packages/tokens  -> W3C Design Tokens + generators
apps/*           -> Showcase apps consuming packages
tools/*          -> Development tooling and gates
```

## Core Principles
- Framework-agnostic Web Components
- Shadow DOM style isolation
- CSS custom properties for theming
- Token-driven design
- Evidence-first development
- Mechanical quality gates

## Data Flow
1. Tokens defined in packages/tokens/design-tokens.json (W3C format)
2. Generator produces CSS variables, TS types, Tailwind preset
3. Components consume tokens via CSS custom properties
4. Apps compose components with tokens
5. Design gate validates compliance

## Build System
- Root: Vite + build.js for engine bundling
- Packages: Independent, consumable
- Workspaces: pnpm/npm workspaces
