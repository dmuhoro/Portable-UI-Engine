/**
 * universal-modal-dialog.js
 * Accessible modal overlay with focus trapping, keyboard dismissal, and slots.
 */

class UniversalModalDialog extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._isOpen = false;
    this._previousFocus = null;
    this._closeReason = 'button';
    this._boundKeyHandler = this._handleKeyDown.bind(this);
    this._boundBackdropClick = this._handleBackdropClick.bind(this);
  }

  static get observedAttributes() {
    return ['open', 'title', 'size'];
  }

  get size() {
    const size = this.getAttribute('size') || 'md';
    return ['sm', 'md', 'lg'].includes(size) ? size : 'md';
  }

  connectedCallback() {
    this._renderShell();
    if (this.hasAttribute('open')) {
      this._showModal(false);
    }
  }

  disconnectedCallback() {
    this._teardownModal();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;

    if (name === 'open') {
      if (this.hasAttribute('open')) {
        this._showModal(true);
      } else {
        this._hideModal(this._closeReason);
      }
    } else if (name === 'title') {
      this._updateTitle();
    } else if (name === 'size') {
      this._updateSize();
    }
  }

  open() {
    this._closeReason = 'button';
    this.setAttribute('open', '');
  }

  close() {
    this._closeReason = 'button';
    this.removeAttribute('open');
  }

  _requestClose(reason) {
    this._closeReason = reason;
    this.removeAttribute('open');
  }

  _renderShell() {
    const title = this.getAttribute('title') || '';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: contents;
          font-family: var(--font-sans, system-ui, -apple-system, sans-serif);
        }

        .backdrop {
          display: none;
          position: fixed;
          inset: 0;
          z-index: 10000;
          background-color: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          align-items: center;
          justify-content: center;
          padding: var(--spacing-4, 16px);
        }

        .backdrop.visible {
          display: flex;
        }

        .dialog {
          background-color: var(--color-bg-surface, #ffffff);
          border-radius: var(--radius-lg, 8px);
          box-shadow: var(--shadow-xl, var(--shadow-lg, 0 25px 50px -12px rgba(0, 0, 0, 0.25)));
          border: 1px solid var(--color-border, #e2e8f0);
          width: 100%;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .dialog.size-sm { max-width: 400px; }
        .dialog.size-md { max-width: 560px; }
        .dialog.size-lg { max-width: 800px; }

        .dialog-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--spacing-4, 16px) var(--spacing-5, 20px);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
        }

        .dialog-title {
          font-size: var(--font-size-lg, 18px);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-text-primary, #0f172a);
          margin: 0;
        }

        .dialog-close {
          background: none;
          border: none;
          font-size: var(--font-size-xl, 20px);
          color: var(--color-text-muted, #94a3b8);
          cursor: pointer;
          line-height: 1;
          padding: var(--spacing-1, 4px);
          transition: color var(--transition-fast, 150ms ease);
        }

        .dialog-close:hover {
          color: var(--color-text-primary, #0f172a);
        }

        .dialog-body {
          padding: var(--spacing-5, 20px);
          overflow-y: auto;
          flex: 1;
          color: var(--color-text-primary, #0f172a);
        }

        .dialog-footer {
          padding: var(--spacing-4, 16px) var(--spacing-5, 20px);
          border-top: 1px solid var(--color-border, #e2e8f0);
        }

        .dialog-footer:empty {
          display: none;
        }
      </style>
      <div class="backdrop" part="backdrop">
        <div class="dialog size-${this.size}" role="dialog" aria-modal="true" aria-labelledby="dialog-title" part="dialog">
          <div class="dialog-header">
            <slot name="header">
              <h2 class="dialog-title" id="dialog-title">${this._escapeHtml(title)}</h2>
            </slot>
            <button type="button" class="dialog-close" aria-label="Close dialog">&times;</button>
          </div>
          <div class="dialog-body">
            <slot></slot>
          </div>
          <div class="dialog-footer">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    `;

    this.shadowRoot.querySelector('.dialog-close')?.addEventListener('click', () => {
      this._requestClose('button');
    });

    this.shadowRoot.querySelector('.backdrop')?.addEventListener('click', this._boundBackdropClick);
  }

  _updateTitle() {
    const titleEl = this.shadowRoot?.querySelector('#dialog-title');
    if (titleEl) {
      titleEl.textContent = this.getAttribute('title') || '';
    }
  }

  _updateSize() {
    const dialog = this.shadowRoot?.querySelector('.dialog');
    if (dialog) {
      dialog.className = `dialog size-${this.size}`;
    }
  }

  _showModal(emitEvent) {
    if (this._isOpen) return;
    this._isOpen = true;
    this._previousFocus = document.activeElement;

    const backdrop = this.shadowRoot?.querySelector('.backdrop');
    if (backdrop) backdrop.classList.add('visible');

    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', this._boundKeyHandler);

    requestAnimationFrame(() => {
      const focusable = this._getFocusableElements();
      if (focusable.length) {
        focusable[0].focus();
      } else {
        this.shadowRoot?.querySelector('.dialog-close')?.focus();
      }
    });

    if (emitEvent) {
      this.dispatchEvent(
        new CustomEvent('modal-open', {
          detail: { timestamp: new Date().toISOString() },
          bubbles: true,
          composed: true,
        })
      );
    }
  }

  _hideModal(reason) {
    if (!this._isOpen) return;
    this._isOpen = false;

    const backdrop = this.shadowRoot?.querySelector('.backdrop');
    if (backdrop) backdrop.classList.remove('visible');

    document.body.style.overflow = '';
    document.removeEventListener('keydown', this._boundKeyHandler);

    if (this._previousFocus && typeof this._previousFocus.focus === 'function') {
      this._previousFocus.focus();
    }
    this._previousFocus = null;

    this.dispatchEvent(
      new CustomEvent('modal-close', {
        detail: { reason },
        bubbles: true,
        composed: true,
      })
    );
  }

  _teardownModal() {
    document.body.style.overflow = '';
    document.removeEventListener('keydown', this._boundKeyHandler);
    this._isOpen = false;
  }

  _handleBackdropClick(e) {
    if (e.target === this.shadowRoot?.querySelector('.backdrop')) {
      this._requestClose('backdrop');
    }
  }

  _handleKeyDown(e) {
    if (!this._isOpen) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      this._requestClose('escape');
      return;
    }

    if (e.key === 'Tab') {
      this._trapFocus(e);
    }
  }

  _getFocusableElements() {
    const dialog = this.shadowRoot?.querySelector('.dialog');
    if (!dialog) return [];

    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return Array.from(dialog.querySelectorAll(selector)).filter(
      (el) => !el.disabled && el.offsetParent !== null
    );
  }

  _trapFocus(e) {
    const focusable = this._getFocusableElements();
    if (focusable.length === 0) {
      e.preventDefault();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  _escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

if (!customElements.get('universal-modal-dialog')) {
  customElements.define('universal-modal-dialog', UniversalModalDialog);
}
