# Sprint UI-03: Component System and Showcase Delivery

**Status:** In Progress  
**Date:** 2026-10-27  
**Goal:** Turn the AI Studio design handoff into a token-backed, accessible, tested Web Component system and usable showcase apps.

## Design decisions

- Direction 1 (Warm Precision) is the default light theme because the docs gallery and teardown lab use it.
- Direction 2 (Technical Oceanic) is the dark operational theme for Run Theater.
- Direction 3 (Swiss Minimalist) is retained as an optional high-contrast theme.
- Existing `universal-*` elements remain compatible. New reusable primitives use the `ui-*` names from the approved design briefs.
- Token JSON remains the source of truth. CSS and TypeScript are generated artifacts.

## Delivery layers

1. **Design handoff and token contract:** track the supplied briefs, resolve semantic tokens and theme presets, verify generated output.
2. **Primitive batch A:** button, input, checkbox, select; accessible keyboard behavior, Shadow DOM, reflected attributes, composed events, and behavior tests.
3. **Primitive batches B/C:** dialog, tooltip, toast, tabs, menu; implement documented interactions and reduced-motion behavior with tests.
4. **Design gate:** lint all engine elements and add reproducible evidence; make errors actionable and ensure the gate passes.
5. **Showcase apps:** docs gallery, teardown lab scoring/comparison, and Run Theater operational demo with responsive layouts and real interactions.
6. **Release and closeout:** documentation, sprint and changelog, full verification, atomic commits, push, and report.

## Acceptance criteria

- All nine design-brief primitives are registered and documented.
- Each primitive has keyboard/accessibility behavior and automated tests for its public contract.
- All component styling uses generated tokens; reduced-motion and visible focus behavior are present.
- The design gate, token generation, tests, and production build pass.
- Showcase apps implement the behaviors stated in their composition docs without claiming unmeasured compliance or performance.
- Sprint status, task list, changelog, and evidence match the verified repository state.
