# AI Studio Directive

**Scope:** Google AI Studio work ONLY. No repo restructuring/builds - I handle those.

## Tasks for AI Studio

### Task 1: Design Directions for Elite Look
Create 2-3 distinct design directions exploring:
- Typography scale and hierarchy
- Color palette (beyond current presets)
- Spacing/radius/motion
- Component aesthetics

Output: `design/directions/direction-{n}.md` with moodboard, tokens JSON, rationale.

### Task 2: Design Briefs
For each priority component/feature, create briefs in `design/briefs/`:
- Screenshot/mockup description
- Tokens needed
- Behavior notes
- Acceptance criteria
- Keyboard/a11y requirements

### Task 3: Showcase App Compositions
Prototype layouts for:
- `apps/docs` - Component gallery homepage
- `apps/teardown-lab` - Rubric UI
- `apps/run-theater` - Mission control aesthetic

Focus: Look and feel only. I will implement to match briefs.

## Handoff Format
Drop files in `design/briefs/` or `design/directions/` with clear names. Include screenshots if possible.

## Notes
- Respect Shadow DOM constraints
- Work with CSS custom properties from tokens
- Prioritize accessibility and clarity
