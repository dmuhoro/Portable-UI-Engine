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

No unreleased changes.
