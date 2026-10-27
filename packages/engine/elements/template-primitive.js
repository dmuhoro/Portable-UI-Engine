/**
 * Portable UI Engine - Skeleton Primitive Template
 * Use this starter template to create new framework-agnostic Web Components.
 * 
 * Rules:
 * 1. Must extend native HTMLElement.
 * 2. Must attach open Shadow DOM.
 * 3. Must consume CSS tokens from theme.css via var(--token).
 * 4. Must handle string/object attributes defensibly using try/catch.
 * 5. Must emit standard CustomEvent objects with { bubbles: true, composed: true }.
 */

export class UniversalTemplatePrimitive extends HTMLElement {
  constructor() {
    super();

    // 1. Attach Shadow DOM in open mode for style encapsulation
    this.attachShadow({ mode: 'open' });

    // Internal state initialization
    this._data = null;
    this._hasParseError = false;
  }

  // 2. Define attributes to observe for dynamic reactivity
  static get observedAttributes() {
    return ['title', 'payload'];
  }

  // 3. Attribute change callback pipeline
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;

    if (name === 'payload') {
      this._parseAndSetPayload(newValue);
    } else if (name === 'title') {
      this._render();
    }
  }

  connectedCallback() {
    this._render();
  }

  // 4. Public Property Getter & Setter with Defensive Type Handling
  get payload() {
    return this._data;
  }

  set payload(val) {
    this._parseAndSetPayload(val);
  }

  /**
   * Safe JSON Parsing Strategy
   * Accepts raw objects or stringified JSON with clean error recovery
   */
  _parseAndSetPayload(val) {
    let parsed = val;
    let parseError = false;

    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (err) {
        console.warn('UniversalTemplatePrimitive: Failed to parse JSON string.', err);
        parsed = null;
        parseError = true;
      }
    }

    this._hasParseError = parseError;
    this._data = parsed;
    this._render();
  }

  /**
   * Dispatch custom DOM events up to host application
   */
  _emitAction(actionName, detailData = {}) {
    this.dispatchEvent(
      new CustomEvent(actionName, {
        detail: {
          timestamp: new Date().toISOString(),
          ...detailData
        },
        bubbles: true,
        composed: true // Allows event to cross Shadow DOM boundary
      })
    );
  }

  /**
   * Component Render Engine
   */
  _render() {
    const titleAttr = this.getAttribute('title') || 'Default Component Title';

    // 5. Template Layout with Enforced CSS Custom Properties
    const style = `
      <style>
        :host {
          display: block;
          font-family: var(--font-sans, system-ui, -apple-system, sans-serif);
          color: var(--color-text-primary, #0f172a);
          box-sizing: border-box;
        }

        .primitive-container {
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 12px);
          padding: var(--spacing-5, 20px);
          box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
          transition: all var(--transition-fast, 150ms ease);
        }

        .primitive-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--spacing-3, 12px);
        }

        .primitive-title {
          font-size: var(--font-size-base, 16px);
          font-weight: var(--font-weight-bold, 700);
          margin: 0;
          color: var(--color-text-primary, #0f172a);
        }

        .action-btn {
          background-color: var(--color-primary, #2563eb);
          color: var(--color-text-inverse, #ffffff);
          border: none;
          border-radius: var(--radius-md, 6px);
          padding: var(--spacing-2, 8px) var(--spacing-4, 16px);
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          cursor: pointer;
          transition: background-color var(--transition-fast, 150ms ease);
        }

        .action-btn:hover {
          background-color: var(--color-primary-hover, #1d4ed8);
        }

        .empty-state {
          padding: var(--spacing-4, 16px);
          text-align: center;
          border-radius: var(--radius-md, 6px);
          font-size: var(--font-size-xs, 12px);
        }

        .empty-error {
          background-color: var(--color-danger-bg, #fef2f2);
          border: 1px solid rgba(220, 38, 38, 0.2);
          color: var(--color-danger, #dc2626);
        }

        .empty-neutral {
          background-color: var(--color-bg-app, #f8fafc);
          color: var(--color-text-muted, #94a3b8);
        }
      </style>
    `;

    // Handle defensive error rendering
    let contentMarkup = '';

    if (this._hasParseError) {
      contentMarkup = `
        <div class="empty-state empty-error">
          <strong>⚠️ Invalid Data Format Provided</strong>
          <p style="margin: 4px 0 0 0;">Failed to parse JSON string input.</p>
        </div>
      `;
    } else if (!this._data) {
      contentMarkup = `
        <div class="empty-state empty-neutral">
          <p style="margin: 0;">No Active Records Available</p>
        </div>
      `;
    } else {
      contentMarkup = `
        <div class="primitive-content">
          <pre style="font-family: var(--font-mono, monospace); font-size: 12px; margin: 0;">${JSON.stringify(this._data, null, 2)}</pre>
        </div>
      `;
    }

    this.shadowRoot.innerHTML = `
      ${style}
      <div class="primitive-container">
        <div class="primitive-header">
          <h3 class="primitive-title">${titleAttr}</h3>
          <button type="button" class="action-btn" id="trigger-action">Trigger Event</button>
        </div>
        ${contentMarkup}
      </div>
    `;

    // Bind event handlers
    const btn = this.shadowRoot.querySelector('#trigger-action');
    if (btn) {
      btn.addEventListener('click', () => {
        this._emitAction('app-primitive-action', {
          title: titleAttr,
          payload: this._data
        });
      });
    }
  }
}

// Guard custom element registration
if (!customElements.get('universal-template-primitive')) {
  customElements.define('universal-template-primitive', UniversalTemplatePrimitive);
}
