/**
 * universal-saas-dashboard.js
 * Portable UI Engine - Composite SaaS Dashboard Custom Element
 * Orchestrates sub-components (<universal-metric-grid> and <universal-data-table>).
 * Features a deep property setter (dashboard.state = newMasterData) to forward
 * payloads synchronously to child elements.
 */
class UniversalSaaSDashboard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._state = {
      metrics: [],
      tableHeaders: [],
      tableRows: []
    };
  }

  static get observedAttributes() {
    return ['state'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'state' && oldValue !== newValue) {
      this._parseAndSetState(newValue);
    }
  }

  get state() {
    return this._state;
  }

  set state(newState) {
    let parsed = newState;
    if (typeof newState === 'string') {
      try {
        parsed = JSON.parse(newState);
      } catch (e) {
        console.warn('UniversalSaasDashboard: Invalid JSON state string provided.', e);
        return;
      }
    }

    if (parsed && typeof parsed === 'object') {
      this._state = {
        metrics: parsed.metrics || [],
        tableHeaders: parsed.tableHeaders || (parsed.tableData?.headers) || [],
        tableRows: parsed.tableRows || (parsed.tableData?.rows) || (Array.isArray(parsed.tableData) ? parsed.tableData : [])
      };
      this._propagateStateToChildren();
    }
  }

  connectedCallback() {
    this.render();
    this._propagateStateToChildren();
  }

  _parseAndSetState(val) {
    if (!val) return;
    try {
      const parsed = JSON.parse(val);
      this.state = parsed;
    } catch (e) {
      console.warn('UniversalSaasDashboard: Failed to parse attribute state JSON.', e);
    }
  }

  _propagateStateToChildren() {
    const metricGrid = this.shadowRoot?.querySelector('universal-metric-grid');
    const dataTable = this.shadowRoot?.querySelector('universal-data-table');

    if (metricGrid) {
      metricGrid.payload = this._state.metrics || [];
    }

    if (dataTable) {
      // Structure format for universal-data-table
      const tablePayload = {
        headers: this._state.tableHeaders || [],
        rows: this._state.tableRows || []
      };
      dataTable.payload = tablePayload;
    }

    this.dispatchEvent(
      new CustomEvent('dashboard-state-change', {
        detail: { state: this._state },
        bubbles: true,
        composed: true,
      })
    );
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          box-sizing: border-box;
          font-family: var(--font-sans, system-ui, sans-serif);
          color: var(--color-text-primary, #0f172a);
        }

        .dashboard-container {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-6, 24px);
          width: 100%;
        }

        .section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--spacing-1, 4px);
        }

        .section-title {
          font-size: var(--font-size-base, 16px);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-text-primary, #0f172a);
          margin: 0;
          display: flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
        }

        .section-badge {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-medium, 500);
          color: var(--color-primary, #2563eb);
          background-color: var(--color-primary-light, #eff6ff);
          padding: 2px 8px;
          border-radius: var(--radius-full, 9999px);
        }
      </style>

      <div class="dashboard-container">
        <!-- Top Metrics Grid Section -->
        <section aria-label="Key Performance Metrics">
          <div class="section-header" style="margin-bottom: 12px;">
            <h2 class="section-title">
              <span>Key Performance Metrics</span>
              <span class="section-badge">Live Real-Time</span>
            </h2>
          </div>
          <universal-metric-grid></universal-metric-grid>
        </section>

        <!-- Main Data Table Section -->
        <section aria-label="Main Records Explorer">
          <universal-data-table></universal-data-table>
        </section>
      </div>
    `;
  }
}

if (!customElements.get('universal-saas-dashboard')) {
  customElements.define('universal-saas-dashboard', UniversalSaaSDashboard);
}
