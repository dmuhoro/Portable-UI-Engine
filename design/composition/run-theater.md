# Showcase App Composition: Mission Control Run Theater (`apps/run-theater`)

A mission-control operational theater and real-time execution dashboard. Built for streaming telemetry, node cluster orchestration, live inference pipelines, and pipeline failure intervention.

---

## 1. Visual Look & Feel and Layout Architecture

The Run Theater embraces a dark, ultra-precise "Deep Oceanic / Mission Control" aesthetic (derived from Design Direction 2). The background is deep maritime slate (`#0B1120`), framing high-contrast telemetry panels with glowing cobalt indicators (`#38BDF8`) and status indicators that communicate operational health instantly. Typography strictly enforces tabular figures (`font-mono tabular-nums`) to prevent numeric jitter during streaming updates.

```
+--------------------------------------------------------------------------------------------------------+
| [RUN THEATER]                   Pipeline: #RUN-88421   Cluster: US-EAST-1A   SLA: 99.99%   [HALT RUN]  |  <-- Mission Top Bar
+--------------------------------------------------------------------------------------------------------+
|                                                                                                        |
|  +--------------------------------------------------------------------------------------------------+  |
|  | MISSION TELEMETRY KPI BAR                                                                        |  |
|  |  Active Nodes: 128/128  | Ingestion: 94.2k ops/s | P99 Latency: 14.2ms | Error Rate: 0.001%       |  |
|  +--------------------------------------------------------------------------------------------------+  |
|                                                                                                        |
|  +-------------------------------------------------------+  +---------------------------------------+  |
|  | PIPELINE STAGE ORCHESTRATION                          |  | LIVE SYSTEM LOG STREAM                |  |
|  |-------------------------------------------------------|  |---------------------------------------|  |
|  | [1] Ingestion Gateway ........... (v) COMPLETE 1.2s   |  | 10:48:02.112 [INFO] Ingestion ack 200 |  |
|  | [2] Schema Normalization ........ (v) COMPLETE 0.4s   |  | 10:48:02.480 [INFO] Tokenizing batch  |  |
|  | [3] Vector Embeddings ........... (>) RUNNING  8.9s   |  | 10:48:03.001 [INFO] Cache hit 94.2%   |  |
|  |     Progress: [===================>       ] 64%       |  | 10:48:04.144 [INFO] Stream chunk #42  |  |
|  | [4] Model Inference ............. ( ) PENDING         |  | 10:48:05.890 [WARN] Node 4 throttled  |  |
|  | [5] Response Delivery ........... ( ) PENDING         |  | 10:48:06.120 [INFO] Auto-scale +2 pod |  |
|  +-------------------------------------------------------+  +---------------------------------------+  |
|                                                                                                        |
|  +--------------------------------------------------------------------------------------------------+  |
|  | CLUSTER NODE TOPOLOGY MATRIX (<universal-data-table> or <ui-data-table>)                         |  |
|  |--------------------------------------------------------------------------------------------------|  |
|  | Node ID      | Region      | Protocol | CPU Usage | Memory   | Active Jobs | Health Status       |  |
|  | node-us-01   | us-east-1a  | gRPC-Web | 42.1%     | 2.4 / 8G | 14          | Operational         |  |
|  | node-us-02   | us-east-1a  | HTTP/2   | 38.6%     | 2.1 / 8G | 11          | Operational         |  |
|  | node-us-03   | us-east-1b  | gRPC-Web | 78.4%     | 6.2 / 8G | 39          | Rebalancing         |  |
|  +--------------------------------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Token Mappings

| Component Region | Token CSS Custom Property | Token Fallback Value | Purpose in Mission Control |
| :--- | :--- | :--- | :--- |
| **Canvas** | `var(--color-canvas-default)` | `#0B1120` | Midnight oceanic operations field |
| **Telemetry Card** | `var(--color-surface-base)` | `#131D33` | Elevated control console surface |
| **Console Dividers** | `var(--color-border-subtle)` | `#1E293B` | Structural frame divisions |
| **Active Highlight** | `var(--color-border-focus)` | `#38BDF8` | Cyan directional beacon |
| **Execution Brand** | `var(--color-brand-primary)` | `#2563EB` | Cobalt action buttons |
| **Metrics Typography**| `var(--typography-family-mono)` | `'JetBrains Mono', monospace` | Jitter-free numeric stream figures |
| **Success Telemetry** | `var(--color-feedback-success)` | `#10B981` | Stage complete / node healthy |
| **Running Telemetry** | `var(--color-brand-primary)` | `#38BDF8` | In-progress active operation |
| **Warning Telemetry** | `var(--color-feedback-warning)` | `#F59E0B` | Node throttled / threshold alert |

---

## 3. Responsive Breakpoint Layouts

### 1280px (Desktop Wide)
- **Top Bar**: Sticky one-row 3-zone layout with live run ID, cluster badge, SLA counter, and prominent "Halt Run" danger trigger.
- **Top KPI Bar**: Single continuous 4-column metric strip across full width.
- **Mid Section**: 60/40 horizontal split—60% pipeline stage orchestration card on left, 40% live scrolling console log on right.
- **Bottom Section**: Full-width interactive cluster node matrix table with search filtering and column sorting.

### 768px (Tablet)
- **KPI Bar**: 2x2 metric grid.
- **Mid Section**: Stacks vertically. Pipeline stage orchestration takes full width; live log stream renders below with fixed 240px height and auto-scroll pin toggle.
- **Node Matrix**: Horizontal scrolling enabled with sticky left column for Node ID.

### 320px (Mobile)
- **Top Bar**: Compact header with status indicator and emergency menu trigger.
- **KPI Bar**: 2x2 grid with 18px figures.
- **Pipeline Stages**: Collapsed view showing current running stage with step progress bar; completed/pending steps accessible via expandable accordion.
- **Log Stream**: Toggleable drawer overlay to save primary viewport space.

---

## 4. Shadow DOM Architecture & Implementation Notes

- **Real-Time Data Streaming Contract**: Telemetry values are bound directly via property assignments (`dashboard.telemetry = streamData`) to eliminate JSON stringification overhead in hot render loops ($>60\text{Hz}$).
- **Encapsulated Terminal Emulator**: The live system log component utilizes Shadow DOM with custom monospaced styling and an internal virtualized list to handle $>10,000$ log lines without memory leaks or UI sluggishness.
- **Non-Color Signaling**: Every status metric pairs color with explicit text labels ("Operational", "Rebalancing", "Degraded") and distinct glyph shapes to comply with WCAG 1.4.1.

---

## 5. Token Configuration JSON

```json
{
  "theaterLayout": {
    "canvas": "var(--color-canvas-default)",
    "kpiGrid": {
      "columns": 4,
      "surface": "var(--color-surface-base)",
      "border": "1px solid var(--color-border-subtle)",
      "font": "var(--typography-family-mono)"
    },
    "logStream": {
      "surface": "var(--color-surface-sunken)",
      "border": "1px solid var(--color-border-subtle)",
      "maxHeight": "380px",
      "font": "var(--typography-family-mono)"
    }
  }
}
```
