# UI Engine Skill File for AI Agents

## Purpose
Guide coding agents (Opencode, Codex, Claude) to correctly use the Portable UI Engine.

## Rules
1. **Use ui-* primitives only** - Import from `@universal-ui/engine` or local packages
2. **Use design tokens** - Never hardcode colors, spacing, or motion. Use CSS custom properties from `packages/tokens`
3. **Shadow DOM aware** - Components are encapsulated; style via CSS custom properties
4. **Design gate required** - Run `design-lint` before closing any UI task
5. **A11y first** - Follow keyboard navigation and ARIA patterns from briefs

## Manifest
Component manifest: `design/contracts/components.json`

## Commands
```bash
npm run design:lint      # Check design gate
npm run build:engine     # Build engine
npm run test            # Run tests
```

## Forbidden Patterns
❌ `color: #ff0000` or hardcoded hex/rgb
✅ `color: var(--color-text-primary)`

❌ `padding: 16px`
✅ `padding: var(--spacing-md)`

## Correct Usage
```html
<ui-button variant="primary">Click me</ui-button>
<ui-input label="Email" type="email"></ui-input>
```
