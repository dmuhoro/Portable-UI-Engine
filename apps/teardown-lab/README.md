# Teardown Lab (`apps/teardown-lab`) Specification

Please refer to the complete Phase 1 design composition specification at:
[`../../design/compositions/teardown-lab.md`](../../design/compositions/teardown-lab.md)

### Summary of Composition:
- **Purpose**: Rubric evaluation, automated scoring cards, and side-by-side component comparisons.
- **Breakpoints**: 320px (stacked compact scorecards), 768px (horizontal KPI strip + criteria list), 1280px (sticky sidebar score + criteria matrix + split benchmark comparison bench).
- **Core Components**: `<ui-checkbox>`, `<ui-button>`, `<ui-tabs>`, `<universal-data-table>`.
- **Token System**: W3C Design Tokens consumed via CSS custom properties in Shadow DOM roots.
