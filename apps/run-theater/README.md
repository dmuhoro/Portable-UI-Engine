# Run Theater (`apps/run-theater`) Specification

Please refer to the complete Phase 1 design composition specification at:
[`../../design/compositions/run-theater.md`](../../design/compositions/run-theater.md)

### Summary of Composition:
- **Purpose**: Mission control telemetry dashboard, streaming pipeline logs, and cluster node orchestration.
- **Breakpoints**: 320px (compact telemetry + accordion steps), 768px (2x2 KPI + full-width pipeline + terminal log), 1280px (sticky mission topbar + 4-column KPI strip + 60/40 orchestration split + node matrix).
- **Core Components**: `<universal-metric-grid>`, `<universal-data-table>`, `<ui-button>`, `<ui-toast>`, `<ui-tooltip>`.
- **Token System**: W3C Design Tokens consumed via CSS custom properties in Shadow DOM roots.
