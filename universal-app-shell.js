/**
 * universal-app-shell.js
 * Portable UI Engine - Native Web Component App Shell Layout
 * Utilizes Shadow DOM and <slot> elements for isolation and flex layout.
 */
class UniversalAppShell extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._drawerOpen = true;
  }

  static get observedAttributes() {
    return ['drawer-open'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'drawer-open' && oldValue !== newValue) {
      this._drawerOpen = newValue !== null && newValue !== 'false';
      this._updateDrawerState();
    }
  }

  connectedCallback() {
    this.render();
    this._setupEventListeners();
    this._updateDrawerState();
  }

  toggleDrawer() {
    this._drawerOpen = !this._drawerOpen;
    if (this._drawerOpen) {
      this.setAttribute('drawer-open', '');
    } else {
      this.removeAttribute('drawer-open');
    }
    this.dispatchEvent(
      new CustomEvent('drawer-toggle', {
        detail: { open: this._drawerOpen },
        bubbles: true,
        composed: true,
      })
    );
  }

  _updateDrawerState() {
    const layout = this.shadowRoot?.querySelector('.shell-layout');
    const toggleBtn = this.shadowRoot?.querySelector('.drawer-toggle-btn');
    if (layout) {
      if (this._drawerOpen) {
        layout.classList.add('drawer-open');
        layout.classList.remove('drawer-closed');
      } else {
        layout.classList.remove('drawer-open');
        layout.classList.add('drawer-closed');
      }
    }
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', String(this._drawerOpen));
    }
  }

  _setupEventListeners() {
    const toggleBtn = this.shadowRoot.querySelector('.drawer-toggle-btn');
    const backdrop = this.shadowRoot.querySelector('.drawer-backdrop');

    toggleBtn?.addEventListener('click', () => this.toggleDrawer());
    backdrop?.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        this.toggleDrawer();
      }
    });

    // Handle ESC key to close drawer on mobile view
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this._drawerOpen && window.innerWidth <= 768) {
        this.toggleDrawer();
      }
    });
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          height: 100vh;
          overflow: hidden;
          box-sizing: border-box;
          font-family: var(--font-sans, system-ui, sans-serif);
          color: var(--color-text-primary, #0f172a);
          background-color: var(--color-bg-app, #f8fafc);
        }

        .shell-layout {
          display: grid;
          grid-template-rows: var(--header-height, 64px) 1fr;
          grid-template-columns: var(--drawer-width, 260px) 1fr;
          grid-template-areas:
            "header header"
            "drawer main";
          width: 100%;
          height: 100%;
          transition: grid-template-columns var(--transition-normal, 250ms ease);
        }

        .shell-layout.drawer-closed {
          grid-template-columns: 0px 1fr;
        }

        /* Header Navigation */
        .shell-header {
          grid-area: header;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 var(--spacing-4, 16px);
          background-color: var(--color-bg-surface, #ffffff);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
          z-index: 20;
          box-shadow: var(--shadow-sm, 0 1px 2px 0 rgba(0,0,0,0.05));
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: var(--spacing-3, 12px);
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: var(--spacing-3, 12px);
        }

        .drawer-toggle-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 38px;
          height: 38px;
          padding: 0;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          background-color: var(--color-bg-surface, #ffffff);
          color: var(--color-text-primary, #0f172a);
          cursor: pointer;
          transition: background-color var(--transition-fast, 150ms ease), border-color var(--transition-fast, 150ms ease);
        }

        .drawer-toggle-btn:hover {
          background-color: var(--color-bg-hover, #f1f5f9);
          border-color: var(--color-border-strong, #cbd5e1);
        }

        .drawer-toggle-btn svg {
          width: 20px;
          height: 20px;
          fill: none;
          stroke: currentColor;
          stroke-width: 2;
          stroke-linecap: round;
          stroke-linejoin: round;
        }

        /* Sidebar Navigation Drawer */
        .shell-drawer {
          grid-area: drawer;
          background-color: var(--color-bg-surface, #ffffff);
          border-right: 1px solid var(--color-border, #e2e8f0);
          overflow-y: auto;
          overflow-x: hidden;
          transition: transform var(--transition-normal, 250ms ease), width var(--transition-normal, 250ms ease);
          z-index: 10;
        }

        .drawer-inner {
          width: var(--drawer-width, 260px);
          height: 100%;
          padding: var(--spacing-4, 16px);
          box-sizing: border-box;
        }

        .drawer-backdrop {
          display: none;
        }

        /* Main Content Workspace */
        .shell-main {
          grid-area: main;
          overflow-y: auto;
          padding: var(--spacing-6, 24px);
          background-color: var(--color-bg-app, #f8fafc);
          box-sizing: border-box;
        }

        /* Responsive Breakpoint Mobile Adjustments */
        @media (max-width: 768px) {
          .shell-layout {
            grid-template-columns: 1fr;
            grid-template-areas:
              "header"
              "main";
          }

          .shell-drawer {
            position: fixed;
            top: var(--header-height, 64px);
            left: 0;
            bottom: 0;
            width: var(--drawer-width, 260px);
            transform: translateX(-100%);
            box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1));
            z-index: 30;
          }

          .shell-layout.drawer-open .shell-drawer {
            transform: translateX(0);
          }

          .drawer-backdrop {
            display: block;
            position: fixed;
            top: var(--header-height, 64px);
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(15, 23, 42, 0.4);
            opacity: 0;
            pointer-events: none;
            transition: opacity var(--transition-normal, 250ms ease);
            z-index: 25;
          }

          .shell-layout.drawer-open .drawer-backdrop {
            opacity: 1;
            pointer-events: auto;
          }

          .shell-main {
            padding: var(--spacing-4, 16px);
          }
        }
      </style>

      <div class="shell-layout drawer-open">
        <header class="shell-header">
          <div class="header-left">
            <button type="button" class="drawer-toggle-btn" aria-label="Toggle navigation drawer" aria-expanded="true">
              <svg viewBox="0 0 24 24">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <slot name="brand"></slot>
          </div>
          <div class="header-right">
            <slot name="header-actions"></slot>
          </div>
        </header>

        <div class="drawer-backdrop"></div>
        <aside class="shell-drawer" aria-label="Sidebar Navigation">
          <div class="drawer-inner">
            <slot name="drawer"></slot>
          </div>
        </aside>

        <main class="shell-main">
          <slot></slot>
        </main>
      </div>
    `;
  }
}

if (!customElements.get('universal-app-shell')) {
  customElements.define('universal-app-shell', UniversalAppShell);
}
