# Changelog

## [2.1.0] - 2026-10-27

### Added

- Added the Warm Precision, Technical Oceanic, and Swiss Minimalist token themes, with generated compatibility aliases for existing `universal-*` components.
- Added nine accessible `ui-*` primitives: button, input, checkbox, select, dialog, tooltip, toast, tabs, and menu.
- Added native form participation for input and checkbox controls, including submission, validation, and reset behavior.
- Added the searchable component gallery, live token inspector, rubric-based Teardown Lab, and simulated Run Theater.
- Added axe-core WCAG A/AA browser checks for all showcase apps and theme directions.

### Changed

- Made `packages/engine` independently buildable and emitted ESM/IIFE distributions for root and package consumers.
- Separated the Vite showcase build output from engine bundles so production builds preserve both artifacts.
- Enabled strict TypeScript checking for shipped token types and the application version constant.
- Replaced the previous project-mismatched CI commands with Portable UI Engine quality gates.

### Fixed

- Corrected self-referencing CSS variable aliases that prevented theme text colors from resolving.
- Corrected dark-theme contrast for inverse text, danger actions, and operational labels.
- Made the test command use the installed Chrome runner and added browser verification for showcase interactions.

## [Unreleased]

### Added
- **AI Studio Design Phase 1** - Three design directions (Warm Precision/Atelier Monolith, Technical Oceanic/Electric Slate, Swiss Minimalist/High-Contrast Editorial) with complete specs in `design/directions/`
- **Component Design Briefs** - 8 component briefs across Batch A (button, input, select, checkbox), Batch B (dialog, tooltip, toast), Batch C (tabs, menu) in `design/briefs/`
- **Showcase App Compositions** - Detailed design specs for apps/docs, apps/teardown-lab, apps/run-theater in `design/compositions/`
- **Infrastructure Integration** - Merged audit/ui-00-baseline infrastructure (AGENTS.md, CONSTITUTION.md, ADRs, packages/engine, packages/tokens, tools/design-lint, elements/, sprints/, tasks/, docs/evidence/) with AI Studio design work
- **Sprint Documentation** - Added UI-04 (mergeable) and UI-05 (consumable) sprint specs with evidence framework
- **UI-05: Consumable** - Manifest (`design/contracts/components.json`), package contract tests (pack/import), Next.js consumer proof (`examples/nextjs-consumer`), scope guard, agent skill (`docs/agent/UI-ENGINE-SKILL.md`), consuming guide updates
- **UI-04: Mergeable & Trusted** - CI gates (lint/design:lint/negative-gate/quick-start/bundle-size), preflight/diagnosis evidence, merge-commit flow

### Changed
- Unified branch history integrating infrastructure foundation with design specifications
- **Docs** - Sprint index/tracking updated, UI-04/05 closeout TODO added, Next.js offline workaround documented
