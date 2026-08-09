/**
 * universal-metric-grid.js
 * Portable UI Engine - Native Dashboard Metric Cards Custom Element
 * Accepts JSON array of metric objects via 'payload' attribute or JS property.
 * Renders responsive cards with trend visual indicators using native CSS design tokens.
 */
class UniversalMetricGrid extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._payload = [];
  }

  static get observedAttributes() {
    return ['payload'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'payload' && oldValue !== newValue) {
      this._parseAndSetPayload(newValue);
    }
  }

  get payload() {
    return this._payload;
  }

  set payload(val) {
    this._payload = val;
    this._parseAndSetPayload(val);
  }

  connectedCallback() {
    this.render();
    this._renderCards();
  }

  _parseAndSetPayload(val) {
    let parsed = val;
    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (e) {
        console.warn('UniversalMetricGrid: Failed to parse JSON payload string.', e);
        parsed = [];
      }
    }
    this._payload = Array.isArray(parsed) ? parsed : [];
    this._renderCards();
  }

  _renderCards() {
    const container = this.shadowRoot?.querySelector('.grid-container');
    if (!container) return;

    if (!this._payload || this._payload.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No metrics data available.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this._payload
      .map(metric => this._buildMetricCardHtml(metric))
      .join('');
  }

  _buildMetricCardHtml(metric) {
    const title = this._escapeHtml(metric.title || 'Metric');
    const value = this._escapeHtml(metric.value || '0');
    const change = this._escapeHtml(metric.change || '');
    const trend = (metric.trend || 'neutral').toLowerCase();
    const context = this._escapeHtml(metric.context || '');

    const isUp = trend === 'upward' || trend === 'up' || change.startsWith('+');
    const isDown = trend === 'downward' || trend === 'down' || change.startsWith('-');

    let badgeClass = 'trend-neutral';
    let icon = '•';

    if (isUp) {
      badgeClass = 'trend-upward';
      icon = '↑';
    } else if (isDown) {
      badgeClass = 'trend-downward';
      icon = '↓';
    }

    return `
      <article class="metric-card">
        <div class="card-header">
          <h3 class="metric-title">${title}</h3>
          ${change ? `<span class="trend-badge ${badgeClass}">${icon} ${change}</span>` : ''}
        </div>
        <div class="card-body">
          <div class="metric-value">${value}</div>
          ${context ? `<div class="metric-context">${context}</div>` : ''}
        </div>
      </article>
    `;
  }

  _escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
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

        .grid-container {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: var(--spacing-4, 16px);
          width: 100%;
        }

        .metric-card {
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          padding: var(--spacing-4, 16px) var(--spacing-5, 20px);
          box-shadow: var(--shadow-sm, 0 1px 2px 0 rgba(0,0,0,0.05));
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          transition: transform var(--transition-fast, 150ms ease), box-shadow var(--transition-fast, 150ms ease);
        }

        .metric-card:hover {
          box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0,0,0,0.1));
          border-color: var(--color-border-strong, #cbd5e1);
        }

        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--spacing-2, 8px);
        }

        .metric-title {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          color: var(--color-text-secondary, #475569);
          text-transform: uppercase;
          letter-spacing: 0.03em;
          margin: 0;
        }

        .trend-badge {
          display: inline-flex;
          align-items: center;
          gap: 2px;
          padding: 2px 8px;
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-bold, 700);
          border-radius: var(--radius-full, 9999px);
          line-height: var(--line-height-tight, 1.25);
        }

        .trend-upward {
          background-color: var(--color-success-bg, #f0fdf4);
          color: var(--color-success, #16a34a);
          border: 1px solid rgba(22, 163, 74, 0.2);
        }

        .trend-downward {
          background-color: var(--color-danger-bg, #fef2f2);
          color: var(--color-danger, #dc2626);
          border: 1px solid rgba(220, 38, 38, 0.2);
        }

        .trend-neutral {
          background-color: var(--color-bg-hover, #f1f5f9);
          color: var(--color-text-secondary, #475569);
          border: 1px solid var(--color-border, #e2e8f0);
        }

        .card-body {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .metric-value {
          font-size: var(--font-size-2xl, 24px);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-text-primary, #0f172a);
          letter-spacing: -0.02em;
          line-height: var(--line-height-tight, 1.25);
        }

        .metric-context {
          font-size: var(--font-size-xs, 12px);
          color: var(--color-text-muted, #94a3b8);
          font-weight: var(--font-weight-medium, 500);
        }

        .empty-state {
          grid-column: 1 / -1;
          padding: var(--spacing-6, 24px);
          text-align: center;
          color: var(--color-text-muted, #94a3b8);
          font-size: var(--font-size-sm, 14px);
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px dashed var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
        }
      </style>

      <div class="grid-container"></div>
    `;
  }
}

if (!customElements.get('universal-metric-grid')) {
  customElements.define('universal-metric-grid', UniversalMetricGrid);
}
