# Product Roadmap

## Current milestone: Design System Implementation

The current milestone converts the approved design handoff into a reliable, distributable Web Component system.

### Delivered in Sprint UI-03

- Three tokenized design themes: Warm Precision, Technical Oceanic, and Swiss Minimalist.
- Nine `ui-*` primitive elements with browser behavior tests.
- Searchable component gallery with theme switching and a CSS token inspector.
- Teardown Lab with saved rubric scoring, computed contrast and target-size readings, and print export.
- Run Theater with clearly labeled simulated telemetry, operational controls, and node filtering.
- Design lint, Chrome browser verification, strict token typechecking, and dual engine builds.

### Follow-up work

- Expand automated accessibility checks with axe-core and reduced-motion assertions across every component state.
- Add API documentation and examples for every legacy `universal-*` element.
- Add focused component tests for select collision behavior, dialog focus restoration, and assistive technology announcements.
- Evaluate whether to replace legacy `universal-*` implementations or maintain them as a compatibility layer.
- Establish package publication and release automation after the branch is reviewed and merged.

Showcase telemetry is a local demonstration. It does not represent a production data pipeline or cluster connection.
