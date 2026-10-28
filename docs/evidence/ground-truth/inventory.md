# Ground Truth Inventory

## Core Files Inventory
- README.md - Present, claims reviewed
- package.json - Present, scripts: dev, build, preview, test, lint
- tsconfig.json - Present, strict: true
- vite.config.ts - Present, React plugin + Tailwind
- build.js - Present, esbuild pipeline
- engine.js - Present, core engine script
- theme.css - Present, design tokens
- universal-ai-bridge.js - Present
- universal-app-shell.js - Present
- universal-billing-funnel.js - Present
- universal-data-table.js - Present
- universal-form.js - Present
- universal-metric-grid.js - Present
- elements/ - Present, contains custom element definitions

## Scripts Inventory
- qa-pressure-test.js - Present, chaos QA engine
- scripts/verify-sync-live.ts - Present
- scripts/verify-realtime-live.ts - Present

## Tests
- tests/ - Directory exists

## Key Components
- universal-app-shell - responsive SaaS grid layout
- universal-form - schema-driven form
- universal-data-table - data grid
- universal-metric-grid - analytics card grid
- universal-saas-dashboard - composite dashboard orchestrator
- universal-billing-funnel - multi-step subscription wizard

## Git State
- Branch: audit/ui-00-baseline
- Upstream: origin/audit/ui-00-baseline matches
- Recent commits documented in git log

## Build Verification
- npm run build:engine passes
- node packages/tokens/scripts/build-tokens.js generates CSS/TS

## Known Issues (from Copilot verification)
- Token generator has duplicate primary mapping
- AGENTS.md contains Daftari conventions
- Multiple layers have deferred/unfinished work
