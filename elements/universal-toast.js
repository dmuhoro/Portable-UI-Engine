/**
 * universal-toast.js
 * Fixed viewport notification manager with auto-dismissing toast popups.
 */

class UniversalToast extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._toasts = [];
    this._timers = new Map();
    this._toastCounter = 0;
    this._boundGlobalHandler = this._handleGlobalToastEvent.bind(this);
  }

  static get observedAttributes() {
    return ['position', 'duration'];
  }

  get toasts() {
    return this._toasts;
  }

  set toasts(val) {
    this._parseAndSetToasts(val);
  }

  get duration() {
    const attr = this.getAttribute('duration');
    const parsed = attr ? parseInt(attr, 10) : 4000;
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 4000;
  }

  get position() {
    const pos = this.getAttribute('position') || 'top-right';
    const valid = ['top-right', 'top-left', 'bottom-right', 'bottom-left'];
    return valid.includes(pos) ? pos : 'top-right';
  }

  connectedCallback() {
    this._renderShell();
    window.addEventListener('universal-toast-show', this._boundGlobalHandler);
  }

  disconnectedCallback() {
    window.removeEventListener('universal-toast-show', this._boundGlobalHandler);
    this._clearAllTimers();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    if (name === 'position') {
      this._updatePositionClass();
    }
  }

  showToast({ type = 'info', title = '', message = '', duration } = {}) {
    const id = `toast-${++this._toastCounter}-${Date.now()}`;
    const toastDuration = duration ?? this.duration;
    const toast = { id, type, title, message, duration: toastDuration };
    this._toasts = [...this._toasts, toast];
    this._renderToasts();
    this._startTimer(id, toastDuration);
    return id;
  }

  clearAll() {
    this._toasts.forEach((toast) => this._dismissToast(toast.id, false));
    this._toasts = [];
    this._clearAllTimers();
    this._renderToasts();
  }

  _handleGlobalToastEvent(e) {
    if (e.detail && typeof e.detail === 'object') {
      this.showToast(e.detail);
    }
  }

  _parseAndSetToasts(val) {
    let parsed = val;

    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (err) {
        console.warn('UniversalToast: Failed to parse toasts JSON string.', err);
        parsed = [];
      }
    }

    this._clearAllTimers();
    this._toasts = Array.isArray(parsed) ? parsed : [];
    this._toasts.forEach((toast) => {
      if (toast.id && toast.duration) {
        this._startTimer(toast.id, toast.duration);
      }
    });
    this._renderToasts();
  }

  _startTimer(id, duration) {
    if (this._timers.has(id)) {
      clearTimeout(this._timers.get(id));
    }
    const timer = setTimeout(() => this._dismissToast(id, true), duration);
    this._timers.set(id, timer);
  }

  _clearAllTimers() {
    this._timers.forEach((timer) => clearTimeout(timer));
    this._timers.clear();
  }

  _dismissToast(id, emitEvent = true) {
    const toast = this._toasts.find((t) => t.id === id);
    if (!toast) return;

    if (this._timers.has(id)) {
      clearTimeout(this._timers.get(id));
      this._timers.delete(id);
    }

    this._toasts = this._toasts.filter((t) => t.id !== id);
    this._renderToasts();

    if (emitEvent) {
      this.dispatchEvent(
        new CustomEvent('toast-dismiss', {
          detail: { toastId: id, type: toast.type },
          bubbles: true,
          composed: true,
        })
      );
    }
  }

  _emitDismiss(toast) {
    this.dispatchEvent(
      new CustomEvent('toast-dismiss', {
        detail: { toastId: toast.id, type: toast.type },
        bubbles: true,
        composed: true,
      })
    );
  }

  _escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  _getTypeAccent(type) {
    const map = {
      success: 'var(--color-success, #16a34a)',
      danger: 'var(--color-danger, #dc2626)',
      warning: 'var(--color-warning, #d97706)',
      info: 'var(--color-primary, #2563eb)',
    };
    return map[type] || map.info;
  }

  _updatePositionClass() {
    this.classList.remove('position-top-right', 'position-top-left', 'position-bottom-right', 'position-bottom-left');
    this.classList.add(`position-${this.position}`);
  }

  _renderShell() {
    this._updatePositionClass();
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          position: fixed;
          z-index: 9999;
          pointer-events: none;
          font-family: var(--font-sans, system-ui, -apple-system, sans-serif);
        }

        :host(.position-top-right) {
          top: var(--spacing-4, 16px);
          right: var(--spacing-4, 16px);
        }

        :host(.position-top-left) {
          top: var(--spacing-4, 16px);
          left: var(--spacing-4, 16px);
        }

        :host(.position-bottom-right) {
          bottom: var(--spacing-4, 16px);
          right: var(--spacing-4, 16px);
        }

        :host(.position-bottom-left) {
          bottom: var(--spacing-4, 16px);
          left: var(--spacing-4, 16px);
        }

        .toast-container {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-3, 12px);
          max-width: 380px;
          width: 100%;
          pointer-events: none;
        }

        :host(.position-bottom-right) .toast-container,
        :host(.position-bottom-left) .toast-container {
          flex-direction: column-reverse;
        }

        .toast-item {
          display: flex;
          align-items: flex-start;
          gap: var(--spacing-3, 12px);
          padding: var(--spacing-4, 16px);
          background-color: var(--color-bg-surface, #ffffff);
          color: var(--color-text-primary, #0f172a);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
          pointer-events: auto;
          animation: toast-in var(--transition-fast, 150ms ease) forwards;
        }

        .toast-accent {
          width: 4px;
          align-self: stretch;
          border-radius: var(--radius-full, 9999px);
          flex-shrink: 0;
        }

        .toast-content {
          flex: 1;
          min-width: 0;
        }

        .toast-title {
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-semibold, 600);
          margin: 0 0 var(--spacing-1, 4px) 0;
        }

        .toast-message {
          font-size: var(--font-size-xs, 12px);
          color: var(--color-text-secondary, #475569);
          margin: 0;
          line-height: var(--line-height-normal, 1.5);
        }

        .toast-close {
          background: none;
          border: none;
          color: var(--color-text-muted, #94a3b8);
          cursor: pointer;
          font-size: var(--font-size-lg, 18px);
          line-height: 1;
          padding: 0;
          flex-shrink: 0;
          transition: color var(--transition-fast, 150ms ease);
        }

        .toast-close:hover {
          color: var(--color-text-primary, #0f172a);
        }

        @keyframes toast-in {
          from {
            opacity: 0;
            transform: translateX(12px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      </style>
      <div class="toast-container" part="container"></div>
    `;
    this._renderToasts();
  }

  _renderToasts() {
    const container = this.shadowRoot?.querySelector('.toast-container');
    if (!container) return;

    container.innerHTML = this._toasts
      .map((toast) => {
        const accent = this._getTypeAccent(toast.type);
        return `
          <div class="toast-item" data-id="${this._escapeHtml(toast.id)}" role="alert">
            <div class="toast-accent" style="background-color: ${accent};"></div>
            <div class="toast-content">
              ${toast.title ? `<p class="toast-title">${this._escapeHtml(toast.title)}</p>` : ''}
              ${toast.message ? `<p class="toast-message">${this._escapeHtml(toast.message)}</p>` : ''}
            </div>
            <button type="button" class="toast-close" aria-label="Dismiss notification">&times;</button>
          </div>
        `;
      })
      .join('');

    container.querySelectorAll('.toast-close').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const item = e.target.closest('.toast-item');
        const id = item?.getAttribute('data-id');
        if (id) {
          const toast = this._toasts.find((t) => t.id === id);
          this._dismissToast(id, false);
          if (toast) this._emitDismiss(toast);
        }
      });
    });
  }
}

if (!customElements.get('universal-toast')) {
  customElements.define('universal-toast', UniversalToast);
}
