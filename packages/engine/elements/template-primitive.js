/**
 * Starter template for Portable UI Engine elements.
 * Components use Shadow DOM, generated CSS tokens, defensive parsing, and composed events.
 */
export class UniversalTemplatePrimitive extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._data = null;
    this._hasParseError = false;
  }

  static get observedAttributes() { return ['title', 'payload']; }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    if (name === 'payload') this._parseAndSetPayload(newValue);
    else this._render();
  }

  connectedCallback() { this._render(); }

  get payload() { return this._data; }
  set payload(value) { this._parseAndSetPayload(value); }

  _parseAndSetPayload(value) {
    try {
      this._data = typeof value === 'string' ? JSON.parse(value) : value;
      this._hasParseError = false;
    } catch {
      this._data = null;
      this._hasParseError = true;
    }
    this._render();
  }

  _emitAction(actionName, detail = {}) {
    this.dispatchEvent(new CustomEvent(actionName, {
      detail: { timestamp: new Date().toISOString(), ...detail },
      bubbles: true,
      composed: true,
    }));
  }

  _render() {
    const style = document.createElement('style');
    style.textContent = `
      :host { display: block; color: var(--color-text-primary); font-family: var(--font-sans); }
      *, *::before, *::after { box-sizing: border-box; }
      .container { padding: var(--spacing-lg); border: 1px solid var(--color-border-subtle); border-radius: var(--radius-md); background: var(--color-surface-base); box-shadow: var(--shadow-sm); }
      header { display: flex; justify-content: space-between; align-items: center; gap: var(--spacing-md); margin-block-end: var(--spacing-md); }
      h3 { margin: 0; font-size: var(--font-size-lg); }
      button { min-height: var(--interaction-target-min); padding: var(--spacing-xs) var(--spacing-md); border: 0; border-radius: var(--radius-sm); background: var(--color-brand-primary); color: var(--color-text-inverse); cursor: pointer; transition: background var(--transition-fast); }
      button:hover { background: var(--color-brand-hover); }
      button:focus-visible { outline: var(--border-focus-width) solid var(--color-border-focus); outline-offset: var(--border-focus-width); }
      .empty { padding: var(--spacing-md); border-radius: var(--radius-sm); background: var(--color-canvas-subtle); color: var(--color-text-secondary); }
      .error { background: var(--color-feedback-danger-subtle); color: var(--color-feedback-danger); }
      pre { overflow: auto; font-family: var(--font-mono); }
      @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
    `;
    const container = document.createElement('section');
    container.className = 'container';
    const header = document.createElement('header');
    const title = document.createElement('h3');
    title.textContent = this.getAttribute('title') || 'Default Component Title';
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Trigger Event';
    button.addEventListener('click', () => this._emitAction('app-primitive-action', { title: title.textContent, payload: this._data }));
    header.append(title, button);

    const content = document.createElement('div');
    if (this._hasParseError) {
      content.className = 'empty error';
      content.setAttribute('role', 'alert');
      content.textContent = 'Invalid data format. The JSON payload could not be parsed.';
    } else if (this._data == null) {
      content.className = 'empty';
      content.textContent = 'No active records available.';
    } else {
      const pre = document.createElement('pre');
      pre.textContent = JSON.stringify(this._data, null, 2);
      content.append(pre);
    }
    container.append(header, content);
    this.shadowRoot.replaceChildren(style, container);
  }
}

if (!customElements.get('universal-template-primitive')) {
  customElements.define('universal-template-primitive', UniversalTemplatePrimitive);
}
