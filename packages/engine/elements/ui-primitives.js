const sharedStyles = `
  :host { display: inline-block; color: var(--color-text-primary); font-family: var(--font-sans); }
  :host([hidden]) { display: none !important; }
  *, *::before, *::after { box-sizing: border-box; }
  button, input, select { font: inherit; }
  button { color: inherit; }
  :focus-visible { outline: var(--border-focus-width) solid var(--color-border-focus); outline-offset: var(--border-focus-width); }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
`;

function emit(element, name, detail = {}) {
  element.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
}

function safeItems(value, fallback = []) {
  if (Array.isArray(value)) return value;
  if (typeof value === 'string') {
    try {
      const result = JSON.parse(value);
      return Array.isArray(result) ? result : fallback;
    } catch {
      return fallback;
    }
  }
  return fallback;
}

function escapeMarkup(value) {
  return String(value).replace(/[&<>\"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', "'": '&#39;' })[character]);
}

function mount(host, css, markup) {
  host.shadowRoot.innerHTML = `<style>${sharedStyles}${css}</style>${markup}`;
}

export class UIButton extends HTMLElement {
  static observedAttributes = ['variant', 'size', 'disabled', 'type', 'loading'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  render() {
    mount(this, `
      :host { display: inline-flex; }
      button { display: inline-flex; align-items: center; justify-content: center; gap: var(--spacing-2xs); box-sizing: border-box; min-height: var(--interaction-target-min); padding: var(--spacing-xs) var(--spacing-md); border: 1px solid transparent; border-radius: var(--radius-sm); background: var(--color-brand-primary, var(--color-text-primary)); color: var(--color-text-inverse); cursor: pointer; font-family: var(--typography-family-body, var(--font-sans)); font-size: var(--typography-scale-sm, var(--font-size-sm)); font-weight: var(--typography-weight-medium, 500); letter-spacing: -0.01em; transition: background var(--motion-duration-fast, var(--transition-fast)) var(--motion-easing-standard, ease); user-select: none; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; touch-action: manipulation; }
      button:hover:not(:disabled):not([aria-busy="true"]) { background: var(--color-brand-hover, #292524); }
      button:active:not(:disabled):not([aria-busy="true"]) { background: var(--color-brand-active, #44403C); transform: scale(0.98); }
      button:disabled, button[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; pointer-events: none; }
      button[aria-busy="true"] { cursor: wait; }
      :host([size="small"]) button { min-height: var(--layout-control-height-compact, 30px); padding: var(--spacing-2xs) var(--spacing-sm); font-size: var(--font-size-xs); }
      :host([size="large"]) button { min-height: 44px; padding: var(--spacing-sm) var(--spacing-lg); }
      :host([variant="secondary"]) button { background: var(--color-surface-sunken, #F4F4F5); border-color: var(--color-border-subtle); color: var(--color-text-primary); }
      :host([variant="secondary"]) button:hover:not(:disabled):not([aria-busy="true"]) { background: var(--color-surface-base); }
      :host([variant="outline"]) button { background: transparent; border-color: var(--color-border-default); color: var(--color-text-primary); }
      :host([variant="outline"]) button:hover:not(:disabled):not([aria-busy="true"]) { background: var(--color-surface-sunken); }
      :host([variant="ghost"]) button { background: transparent; border-color: transparent; color: var(--color-text-primary); }
      :host([variant="ghost"]) button:hover:not(:disabled):not([aria-busy="true"]) { background: var(--color-surface-sunken); }
      :host([variant="danger"]) button { background: var(--color-feedback-danger); color: var(--color-text-inverse); }
      :host([variant="danger"]) button:hover:not(:disabled):not([aria-busy="true"]) { filter: brightness(0.9); }
      .spinner { width: 1em; height: 1em; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; }
      @keyframes spin { to { transform: rotate(360deg); } }
      @media (prefers-reduced-motion: reduce) { button, .spinner { transition: none !important; animation: none !important; transform: none !important; } }
    `, `<button part="button" type="${escapeMarkup(this.getAttribute('type') || 'button')}"><span class="spinner" hidden></span><slot name="icon-start"></slot><slot></slot><slot name="icon-end"></slot></button>`);
    const button = this.shadowRoot.querySelector('button');
    const spinner = this.shadowRoot.querySelector('.spinner');
    const loading = this.hasAttribute('loading');
    button.disabled = this.hasAttribute('disabled');
    button.setAttribute('aria-disabled', this.hasAttribute('disabled') ? 'true' : 'false');
    button.setAttribute('aria-busy', loading ? 'true' : 'false');
    if (loading) spinner.removeAttribute('hidden');
    else spinner.setAttribute('hidden', '');
    button.onclick = null;
    button.addEventListener('click', event => {
      if (button.disabled || loading) { event.preventDefault(); event.stopPropagation(); return; }
      emit(this, 'ui-button-click', { originalEvent: event, variant: this.getAttribute('variant') || 'primary' });
    });
  }
}

export class UIInput extends HTMLElement {
  static formAssociated = true;
  static observedAttributes = ['label', 'value', 'type', 'placeholder', 'disabled', 'required', 'error', 'name', 'clearable', 'aria-label', 'help', 'maxlength'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._value = ''; this._formDisabled = false; try { this._internals = this.attachInternals(); } catch { this._internals = null; } }
  connectedCallback() { this.render(); }
  attributeChangedCallback(name, _old, value) {
    if (name === 'value') this._value = value || '';
    if (this.isConnected) this.render();
  }
  get value() { return this.shadowRoot.querySelector('input')?.value ?? this._value; }
  set value(value) { this._value = String(value ?? ''); if (this.isConnected) this.render(); }
  render() {
    const id = escapeMarkup(`field-${this.getAttribute('name') || 'input'}-${Math.random().toString(36).slice(2, 6)}`);
    const label = this.getAttribute('label') || '';
    const error = this.getAttribute('error') || '';
    const help = this.getAttribute('help') || '';
    const hasValue = Boolean(this._value || this.getAttribute('value'));
    mount(this, `
      :host { position: relative; display: block; font-family: var(--typography-family-body, var(--font-sans)); }
      .wrapper { display: grid; gap: var(--spacing-2xs); }
      .label { color: var(--color-text-secondary); font-size: var(--font-size-sm); font-weight: var(--typography-weight-medium, 500); }
      .field-wrap { position: relative; display: flex; align-items: center; gap: var(--spacing-2xs); }
      input { width: 100%; min-height: 44px; padding: var(--spacing-xs) var(--spacing-sm); padding-inline-end: ${this.hasAttribute('clearable') ? 'calc(var(--interaction-target-min) + var(--spacing-xs))' : 'var(--spacing-sm)'}; border: 1px solid var(--color-border-subtle); border-radius: var(--radius-sm); background: var(--color-surface-base); color: var(--color-text-primary); font-size: var(--typography-scale-sm, var(--font-size-sm)); }
      input::placeholder { color: var(--color-text-tertiary); }
      input:hover:not(:disabled) { border-color: var(--color-border-default); }
      input:focus-visible { outline: var(--border-focus-width) solid var(--color-border-focus); outline-offset: 2px; }
      input[aria-invalid="true"] { border-color: var(--color-feedback-danger); }
      input:disabled { opacity: 0.45; cursor: not-allowed; }
      .error { color: var(--color-feedback-danger); font-size: var(--font-size-xs); }
      .help { color: var(--color-text-tertiary); font-size: var(--font-size-xs); }
      .clear { position: absolute; right: var(--spacing-2xs); min-width: var(--interaction-target-min); min-height: var(--interaction-target-min); border: 0; border-radius: var(--radius-sm); background: transparent; cursor: pointer; color: var(--color-text-secondary); touch-action: manipulation; }
      .clear:hover { background: var(--color-surface-sunken); }
      slot[name="icon-start"], slot[name="icon-end"] { display: inline-flex; align-items: center; color: var(--color-text-secondary); }
      @media (prefers-reduced-motion: reduce) { input, .clear { transition: none !important; } }
    `, `<div class="wrapper"><label class="label" for="${id}">${label ? escapeMarkup(label) : '<slot name="label"></slot>'}</label><div class="field-wrap"><slot name="icon-start"></slot><input id="${id}" type="${escapeMarkup(this.getAttribute('type') || 'text')}" name="${escapeMarkup(this.getAttribute('name') || '')}" placeholder="${escapeMarkup(this.getAttribute('placeholder') || '')}" aria-label="${escapeMarkup(this.getAttribute('aria-label') || label || 'Text input')}" aria-invalid="${Boolean(error)}" ${error ? `aria-describedby="${id}-error ${id}-help"` : help ? `aria-describedby="${id}-help"` : ''} ${this.hasAttribute('required') ? 'required' : ''} ${this.hasAttribute('disabled') || this._formDisabled ? 'disabled' : ''} ${this.getAttribute('maxlength') ? `maxlength="${escapeMarkup(this.getAttribute('maxlength'))}"` : ''} /><slot name="icon-end"></slot>${this.hasAttribute('clearable') && hasValue ? `<button class="clear" type="button" aria-label="Clear value">×</button>` : ''}</div>${error ? `<span class="error" id="${id}-error" role="alert">${escapeMarkup(error)}</span>` : ''}${help && !error ? `<span class="help" id="${id}-help">${escapeMarkup(help)}</span>` : ''}</div>`);
    const input = this.shadowRoot.querySelector('input');
    input.value = this._value || this.getAttribute('value') || '';
    this._updateFormValue(input);
    input.addEventListener('input', () => { this._value = input.value; this._updateFormValue(input); if (this.hasAttribute('clearable')) this.render(); emit(this, 'ui-input-change', { name: input.name, value: input.value }); });
    input.addEventListener('change', () => { this._value = input.value; emit(this, 'change', { name: input.name, value: input.value }); });
    this.shadowRoot.querySelector('.clear')?.addEventListener('click', () => { input.value = ''; this._value = ''; this._updateFormValue(input); input.focus(); if (this.hasAttribute('clearable')) this.render(); emit(this, 'ui-input-change', { name: input.name, value: '', source: 'clear' }); });
  }
  _updateFormValue(input) {
    if (!this._internals) return;
    this._internals.setFormValue(input.value);
    if (input.required && !input.value) this._internals.setValidity({ valueMissing: true }, 'Please fill out this field.', input);
    else this._internals.setValidity({});
  }
  formResetCallback() { this._value = this.getAttribute('value') || ''; if (this.isConnected) this.render(); }
  formStateRestoreCallback(state) { this.value = String(state ?? ''); }
  formDisabledCallback(disabled) { this._formDisabled = disabled; if (this.isConnected) this.render(); }
}

export class UICheckbox extends HTMLElement {
  static formAssociated = true;
  static observedAttributes = ['label', 'checked', 'disabled', 'indeterminate', 'name', 'value', 'required'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._formDisabled = false; try { this._internals = this.attachInternals(); } catch { this._internals = null; } }
  connectedCallback() { this._defaultChecked = this.hasAttribute('checked'); this.render(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  get checked() { return this.shadowRoot.querySelector('input')?.checked ?? this.hasAttribute('checked'); }
  set checked(value) { this.toggleAttribute('checked', Boolean(value)); }
  get indeterminate() { return this.shadowRoot.querySelector('input')?.indeterminate ?? this.hasAttribute('indeterminate'); }
  set indeterminate(value) { this.toggleAttribute('indeterminate', Boolean(value)); if (this.isConnected) this.render(); }
  render() {
    mount(this, `
      :host { display: inline-block; font-family: var(--typography-family-body, var(--font-sans)); }
      label { display: inline-flex; align-items: flex-start; gap: var(--spacing-xs); min-height: 44px; cursor: pointer; touch-action: manipulation; }
      .control { position: relative; display: inline-flex; align-items: center; justify-content: center; width: var(--spacing-md); height: var(--spacing-md); margin-top: 2px; flex-shrink: 0; }
      input { position: absolute; opacity: 0; width: 44px; height: 44px; cursor: pointer; }
      .box { width: var(--spacing-md); height: var(--spacing-md); border: 1px solid var(--color-border-default); border-radius: var(--radius-xs); background: var(--color-surface-base); }
      input:checked + .box { background: var(--color-brand-primary); border-color: var(--color-brand-primary); }
      input:indeterminate + .box { background: var(--color-brand-primary); border-color: var(--color-brand-primary); }
      .checkmark { position: absolute; width: 12px; height: 12px; color: var(--color-text-inverse); display: none; }
      input:checked + .box + .checkmark.check { display: block; }
      input:indeterminate + .box + .checkmark.dash { display: block; }
      input:focus-visible + .box { outline: var(--border-focus-width) solid var(--color-border-focus); outline-offset: 2px; }
      input:disabled { cursor: not-allowed; }
      input:disabled + .box { opacity: 0.45; }
      input:disabled ~ span { opacity: 0.6; cursor: not-allowed; }
      @media (prefers-reduced-motion: reduce) { .box, input { transition: none !important; } }
    `, `<label><span class="control"><input type="checkbox" name="${escapeMarkup(this.getAttribute('name') || '')}" value="${escapeMarkup(this.getAttribute('value') || 'on')}" aria-label="${escapeMarkup(this.getAttribute('aria-label') || this.getAttribute('label') || '')}" /><span class="box"></span><svg class="checkmark check" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,6 5,9 10,3"></polyline></svg><svg class="checkmark dash" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="9" y2="6"></line></svg></span><span>${this.hasAttribute('label') ? escapeMarkup(this.getAttribute('label')) : '<slot></slot>'}</span></label>`);
    const input = this.shadowRoot.querySelector('input');
    input.checked = this.hasAttribute('checked');
    input.indeterminate = this.hasAttribute('indeterminate');
    input.disabled = this.hasAttribute('disabled') || this._formDisabled;
    input.required = this.hasAttribute('required');
    this._updateFormValue(input);
    input.addEventListener('change', () => {
      this.toggleAttribute('checked', input.checked);
      if (input.indeterminate) this.removeAttribute('indeterminate');
      input.indeterminate = false;
      this._updateFormValue(input);
      emit(this, 'ui-checkbox-change', { checked: input.checked, indeterminate: false, name: input.name, value: input.value });
    });
  }
  _updateFormValue(input) {
    if (!this._internals) return;
    this._internals.setFormValue(input.checked ? input.value : null);
    if (input.required && !input.checked) this._internals.setValidity({ valueMissing: true }, 'Please select this option.', input);
    else this._internals.setValidity({});
  }
  formResetCallback() { this.checked = this._defaultChecked; this.indeterminate = false; if (this.isConnected) this.render(); }
  formStateRestoreCallback(state) { this.checked = state === this.getAttribute('value') || state === 'on'; this.indeterminate = false; }
  formDisabledCallback(disabled) { this._formDisabled = disabled; if (this.isConnected) this.render(); }
}

export class UISelect extends HTMLElement {
  static observedAttributes = ['label', 'value', 'placeholder', 'disabled', 'required', 'name', 'options'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._options = []; this._value = ''; }
  connectedCallback() { this.render(); }
  attributeChangedCallback(name, _old, value) {
    if (name === 'value') this._value = value || '';
    if (name === 'options') this._options = safeItems(value);
    if (this.isConnected) this.render();
  }
  get options() { return this._options; }
  set options(value) { this._options = safeItems(value); if (this.isConnected) this.render(); }
  get value() { return this._value; }
  set value(value) { this._value = String(value ?? ''); if (this.isConnected) this.render(); }
  render() {
    const options = this._options.length ? this._options : [...this.querySelectorAll('option')].map(option => ({ label: option.textContent.trim(), value: option.value }));
    mount(this, `
      :host { display: block; }
      label { display: grid; gap: var(--spacing-2xs); color: var(--color-text-secondary); font-size: var(--font-size-sm); }
      input { width: 100%; min-height: var(--interaction-target-min); padding: var(--spacing-xs) var(--spacing-sm); border: 1px solid var(--color-border-subtle); border-radius: var(--radius-sm); background: var(--color-surface-base); color: var(--color-text-primary); }
      [role="listbox"] { position: fixed; z-index: var(--layer-popover); max-height: var(--component-popup-max-height); overflow: auto; min-width: var(--component-popup-min-width); margin: 0; padding: var(--spacing-2xs); list-style: none; border: 1px solid var(--color-border-subtle); border-radius: var(--radius-sm); background: var(--color-surface-overlay); box-shadow: var(--shadow-md); }
      [role="option"] { min-height: var(--interaction-target-min); padding: var(--spacing-xs); cursor: pointer; }
      [role="option"][aria-selected="true"], [role="option"]:hover { background: var(--color-surface-sunken); }
      [role="option"][data-active="true"] { outline: var(--border-focus-width) solid var(--color-border-focus); outline-offset: 0; }
      [hidden] { display: none; }
    `, `<label>${escapeMarkup(this.getAttribute('label') || '')}<input role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="options" placeholder="${escapeMarkup(this.getAttribute('placeholder') || 'Choose an option')}" ${this.hasAttribute('disabled') ? 'disabled' : ''} ${this.hasAttribute('required') ? 'required' : ''} /><ul id="options" role="listbox" hidden></ul></label>`);
    const input = this.shadowRoot.querySelector('input');
    const list = this.shadowRoot.querySelector('ul');
    input.value = options.find(item => item.value === this._value)?.label || this._value;
    const draw = query => {
      list.replaceChildren();
      options.filter(item => String(item.label).toLowerCase().includes(query.toLowerCase())).forEach((item, index) => {
        const option = document.createElement('li');
        option.setAttribute('role', 'option'); option.id = `option-${index}`; option.tabIndex = -1; option.setAttribute('aria-selected', String(String(item.value) === this._value)); option.dataset.index = String(index); option.textContent = String(item.label);
        option.addEventListener('mousedown', event => event.preventDefault());
        option.addEventListener('click', () => { this._value = String(item.value); input.value = String(item.label); close(); input.removeAttribute('aria-activedescendant'); emit(this, 'ui-select-change', { name: this.getAttribute('name') || '', value: this._value }); });
        list.append(option);
      });
    };
    const open = () => {
      draw(input.value === (options.find(item => item.value === this._value)?.label || '') ? '' : input.value);
      list.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      const bounds = input.getBoundingClientRect();
      const gap = Number.parseFloat(getComputedStyle(this).getPropertyValue('--spacing-2xs')) || 0;
      const roomBelow = innerHeight - bounds.bottom - gap;
      const roomAbove = bounds.top - gap;
      const useAbove = roomBelow < Math.min(list.scrollHeight, 160) && roomAbove > roomBelow;
      const available = Math.max(0, useAbove ? roomAbove : roomBelow);
      list.style.maxHeight = `${available}px`;
      list.style.left = `${Math.max(gap, Math.min(bounds.left, innerWidth - bounds.width - gap))}px`;
      list.style.width = `${bounds.width}px`;
      list.style.top = `${useAbove ? Math.max(gap, bounds.top - Math.min(list.scrollHeight, available) - gap) : bounds.bottom + gap}px`;
    };
    const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); };
    input.addEventListener('focus', open);
    input.addEventListener('input', () => { open(); emit(this, 'ui-select-search', { query: input.value }); });
    input.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        if (list.hidden) open();
        const items = [...list.querySelectorAll('[role="option"]')];
        const current = items.findIndex(option => option.id === input.getAttribute('aria-activedescendant'));
        const next = current < 0 ? (event.key === 'ArrowDown' ? 0 : items.length - 1) : (current + (event.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
        items.forEach((option, index) => { option.dataset.active = String(index === next); });
        if (items[next]) input.setAttribute('aria-activedescendant', items[next].id);
      }
      if (event.key === 'Escape') { close(); input.removeAttribute('aria-activedescendant'); }
      if (event.key === 'Enter' && !list.hidden) { event.preventDefault(); list.querySelector(`#${CSS.escape(input.getAttribute('aria-activedescendant') || '')}`)?.click(); }
    });
    this.shadowRoot.addEventListener('focusout', event => { if (!event.relatedTarget || !this.shadowRoot.contains(event.relatedTarget)) close(); });
    list.addEventListener('focusout', event => { if (event.relatedTarget !== input && !list.contains(event.relatedTarget)) close(); });
  }
}

export class UIDialog extends HTMLElement {
  static observedAttributes = ['open', 'label'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  show() { this.setAttribute('open', ''); }
  close() { const dialog = this.shadowRoot.querySelector('dialog'); if (dialog?.open) dialog.close(); this.removeAttribute('open'); }
  render() {
    mount(this, `
      dialog { width: min(var(--component-dialog-max-width), calc(100vw - var(--spacing-lg))); max-height: calc(100vh - var(--spacing-2xl)); overflow: auto; padding: var(--spacing-lg); border: 1px solid var(--color-border-subtle); border-radius: var(--radius-md); background: var(--color-surface-base); color: var(--color-text-primary); box-shadow: var(--shadow-lg); }
      dialog::backdrop { background: var(--color-overlay-scrim); backdrop-filter: blur(var(--spacing-2xs)); }
      header { display: flex; justify-content: space-between; align-items: start; gap: var(--spacing-md); margin-bottom: var(--spacing-md); }
      h2 { margin: 0; font-size: var(--font-size-lg); }
      button { min-width: var(--interaction-target-min); min-height: var(--interaction-target-min); border: 0; border-radius: var(--radius-sm); background: transparent; cursor: pointer; }
      @media (prefers-reduced-motion: no-preference) { dialog { transition: opacity var(--transition-fast), transform var(--transition-fast); } }
    `, `<dialog aria-labelledby="dialog-title"><header><h2 id="dialog-title"></h2><button type="button" aria-label="Close dialog">×</button></header><section><slot></slot></section></dialog>`);
    const dialog = this.shadowRoot.querySelector('dialog');
    this.shadowRoot.querySelector('h2').textContent = this.getAttribute('label') || '';
    this.shadowRoot.querySelector('button').addEventListener('click', () => this.close());
    dialog.addEventListener('cancel', event => { event.preventDefault(); this.close(); });
    dialog.addEventListener('close', () => emit(this, 'ui-dialog-close'));
    if (this.hasAttribute('open') && !dialog.open) dialog.showModal();
    if (!this.hasAttribute('open') && dialog.open) dialog.close();
  }
}

export class UITooltip extends HTMLElement {
  static observedAttributes = ['text', 'placement'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this.timer = 0; }
  connectedCallback() { this.render(); }
  attributeChangedCallback(_name, oldValue, newValue) { if (this.isConnected && oldValue !== newValue && !this._reflecting) this.render(); }
  disconnectedCallback() { clearTimeout(this.timer); }
  render() {
    mount(this, `
      :host { position: relative; }
      .tip { position: absolute; z-index: var(--layer-tooltip); bottom: calc(100% + var(--spacing-2xs)); left: 50%; transform: translateX(-50%); width: max-content; max-width: var(--component-tooltip-max-width); padding: var(--spacing-2xs) var(--spacing-xs); border-radius: var(--radius-xs); background: var(--color-surface-inverse); color: var(--color-text-inverse); font-size: var(--font-size-xs); pointer-events: none; }
      :host([placement="bottom"]) .tip { top: calc(100% + var(--spacing-2xs)); bottom: auto; }
      .tip[hidden] { display: none; }
    `, `<span id="trigger"><slot></slot></span><span id="tip" class="tip" role="tooltip" hidden></span>`);
    const trigger = this.shadowRoot.querySelector('#trigger'); const slot = this.shadowRoot.querySelector('slot'); const tip = this.shadowRoot.querySelector('#tip');
    tip.textContent = this.getAttribute('text') || '';
    const describedTargets = () => slot.assignedElements({ flatten: true }).flatMap(element => [element, ...element.querySelectorAll('button, a[href], input, select, textarea, [tabindex]')]);
    const show = delay => { clearTimeout(this.timer); this.timer = window.setTimeout(() => { tip.hidden = false; for (const target of describedTargets()) target.setAttribute('aria-describedby', 'tip'); }, delay); };
    const hide = () => { clearTimeout(this.timer); tip.hidden = true; for (const target of describedTargets()) target.removeAttribute('aria-describedby'); };
    trigger.addEventListener('mouseenter', () => show(300)); trigger.addEventListener('mouseleave', hide);
    trigger.addEventListener('focusin', () => show(0)); trigger.addEventListener('focusout', hide);
  }
}

const toastInstances = new Set();
function repositionToasts() {
  const style = getComputedStyle(document.documentElement);
  const offset = Number.parseFloat(style.getPropertyValue('--layout-toast-offset')) || 80;
  let index = 0;
  for (const toast of toastInstances) {
    if (toast.hidden) continue;
    toast.style.bottom = `calc(var(--spacing-md) + ${index * offset}px)`;
    index += 1;
  }
}

export class UIToast extends HTMLElement {
  static observedAttributes = ['message', 'variant', 'duration'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this.timer = 0; }
  connectedCallback() { toastInstances.add(this); this.render(); repositionToasts(); }
  disconnectedCallback() { clearTimeout(this.timer); toastInstances.delete(this); repositionToasts(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  show(message = this.getAttribute('message') || '') { this.setAttribute('message', message); this.hidden = false; repositionToasts(); }
  dismiss() { clearTimeout(this.timer); this.hidden = true; repositionToasts(); emit(this, 'ui-toast-dismiss'); }
  render() {
    const alert = this.getAttribute('variant') === 'danger';
    mount(this, `
      :host { position: fixed; right: var(--spacing-md); bottom: var(--spacing-md); z-index: var(--layer-toast); width: min(var(--component-toast-max-width), calc(100vw - var(--spacing-lg))); }
      .toast { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-md); min-width: min(100%, var(--component-popup-min-width)); padding: var(--spacing-sm) var(--spacing-md); border: 1px solid var(--color-border-subtle); border-radius: var(--radius-md); background: var(--color-surface-base); box-shadow: var(--shadow-md); }
      button { min-width: var(--interaction-target-min); min-height: var(--interaction-target-min); border: 0; background: transparent; cursor: pointer; }
    `, `<div class="toast" role="${alert ? 'alert' : 'status'}" aria-live="${alert ? 'assertive' : 'polite'}"><span></span><button type="button" aria-label="Dismiss notification">×</button></div>`);
    this.shadowRoot.querySelector('span').textContent = this.getAttribute('message') || '';
    this.shadowRoot.querySelector('button').addEventListener('click', () => this.dismiss());
    clearTimeout(this.timer);
    const duration = Number(this.getAttribute('duration') || 5000);
    if (duration > 0) this.timer = window.setTimeout(() => this.dismiss(), duration);
    const pause = () => clearTimeout(this.timer);
    const resume = () => { if (duration > 0) this.timer = window.setTimeout(() => this.dismiss(), duration); };
    this.shadowRoot.querySelector('.toast').addEventListener('mouseenter', pause);
    this.shadowRoot.querySelector('.toast').addEventListener('focusin', pause);
    this.shadowRoot.querySelector('.toast').addEventListener('mouseleave', resume);
    this.shadowRoot.querySelector('.toast').addEventListener('focusout', resume);
  }
}

export class UITabs extends HTMLElement {
  static observedAttributes = ['selected'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._items = []; }
  connectedCallback() { this.render(); }
  attributeChangedCallback(_name, oldValue, newValue) { if (this.isConnected && oldValue !== newValue && !this._reflecting) this.render(); }
  get items() { return this._items; }
  set items(value) { this._items = safeItems(value); if (this.isConnected) this.render(); }
  render() {
    const items = this._items.length ? this._items : [...this.querySelectorAll('[data-tab]')].map((node, index) => ({ label: node.getAttribute('data-tab'), content: node.textContent, id: node.id || String(index) }));
    const selected = Math.max(0, Math.min(items.length - 1, Number(this.getAttribute('selected') || 0)));
    mount(this, `
      :host { display: block; }
      [role="tablist"] { display: flex; gap: var(--spacing-2xs); overflow-x: auto; border-bottom: 1px solid var(--color-border-subtle); }
      [role="tab"] { min-height: var(--interaction-target-min); padding: var(--spacing-xs) var(--spacing-md); border: 0; border-bottom: var(--border-focus-width) solid transparent; background: transparent; color: var(--color-text-secondary); cursor: pointer; white-space: nowrap; }
      :host([variant="segmented"]) [role="tablist"] { padding: var(--spacing-2xs); border: 0; border-radius: var(--radius-md); background: var(--color-surface-sunken); }
      :host([variant="segmented"]) [role="tab"] { border: 0; border-radius: var(--radius-sm); }
      :host([variant="segmented"]) [role="tab"][aria-selected="true"] { background: var(--color-surface-base); box-shadow: var(--shadow-sm); }
      [role="tab"][aria-selected="true"] { border-bottom-color: var(--color-brand-primary); color: var(--color-text-primary); }
      [role="tabpanel"] { padding: var(--spacing-md) 0; }
    `, `<div role="tablist" aria-label="${escapeMarkup(this.getAttribute('label') || 'Tabs')}"></div><section role="tabpanel" tabindex="0"></section>`);
    const tablist = this.shadowRoot.querySelector('[role="tablist"]');
    const panel = this.shadowRoot.querySelector('[role="tabpanel"]');
    const choose = index => {
      if (!items[index]) return;
      [...tablist.children].forEach((tab, tabIndex) => { tab.setAttribute('aria-selected', String(index === tabIndex)); tab.tabIndex = index === tabIndex ? 0 : -1; });
      panel.textContent = String(items[index].content ?? ''); panel.setAttribute('aria-labelledby', `tab-${index}`); this._reflecting = true; this.setAttribute('selected', String(index)); this._reflecting = false;
      emit(this, 'ui-tab-change', { index, id: items[index].id ?? String(index) });
    };
    items.forEach((item, index) => {
      const tab = document.createElement('button'); tab.type = 'button'; tab.id = `tab-${index}`; tab.setAttribute('role', 'tab'); tab.setAttribute('aria-controls', 'panel'); tab.textContent = String(item.label ?? `Tab ${index + 1}`); tab.addEventListener('click', () => choose(index));
      tab.addEventListener('keydown', event => { let next = index; if (event.key === 'ArrowRight') next = (index + 1) % items.length; else if (event.key === 'ArrowLeft') next = (index + items.length - 1) % items.length; else if (event.key === 'Home') next = 0; else if (event.key === 'End') next = items.length - 1; else return; event.preventDefault(); choose(next); tablist.children[next].focus(); });
      tablist.append(tab);
    });
    panel.id = 'panel'; choose(selected);
  }
}

export class UIMenu extends HTMLElement {
  static observedAttributes = ['label', 'items'];
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._items = []; }
  connectedCallback() { this.render(); }
  attributeChangedCallback(name, _old, value) { if (name === 'items') this._items = safeItems(value); if (this.isConnected) this.render(); }
  get items() { return this._items; }
  set items(value) { this._items = safeItems(value); if (this.isConnected) this.render(); }
  render() {
    const items = this._items.length ? this._items : [...this.querySelectorAll('[data-menu-item]')].map(node => ({ label: node.textContent.trim(), value: node.getAttribute('data-menu-item') }));
    mount(this, `
      :host { position: relative; }
      button { min-height: var(--interaction-target-min); padding: var(--spacing-xs) var(--spacing-md); border: 1px solid var(--color-border-default); border-radius: var(--radius-sm); background: var(--color-surface-base); cursor: pointer; }
      [role="menu"] { position: absolute; z-index: var(--layer-popover); top: calc(100% + var(--spacing-2xs)); right: 0; min-width: var(--component-popup-min-width); margin: 0; padding: var(--spacing-2xs); list-style: none; border: 1px solid var(--color-border-subtle); border-radius: var(--radius-sm); background: var(--color-surface-overlay); box-shadow: var(--shadow-md); }
      [role="menu"][hidden] { display: none; }
      [role="menuitem"] { display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: var(--interaction-target-min); padding: var(--spacing-xs); border: 0; text-align: left; background: transparent; cursor: pointer; }
      [role="menuitem"]:hover, [role="menuitem"]:focus-visible { background: var(--color-surface-sunken); }
      kbd { font-family: var(--font-mono); color: var(--color-text-secondary); }
    `, `<button type="button" aria-haspopup="menu" aria-expanded="false">${escapeMarkup(this.getAttribute('label') || 'Menu')}</button><ul role="menu" hidden></ul>`);
    const trigger = this.shadowRoot.querySelector('button'); const menu = this.shadowRoot.querySelector('[role="menu"]');
    const close = () => { menu.hidden = true; trigger.setAttribute('aria-expanded', 'false'); };
    const open = () => { menu.hidden = false; trigger.setAttribute('aria-expanded', 'true'); menu.querySelector('[role="menuitem"]')?.focus(); };
    items.forEach(item => {
      if (item.separator) { const separator = document.createElement('li'); separator.setAttribute('role', 'separator'); menu.append(separator); return; }
      const row = document.createElement('li'); row.setAttribute('role', 'none'); const action = document.createElement('button'); action.type = 'button'; action.setAttribute('role', 'menuitem'); action.textContent = String(item.label ?? '');
      if (item.shortcut) { const key = document.createElement('kbd'); key.textContent = String(item.shortcut); action.append(key); }
      action.addEventListener('click', () => { close(); emit(this, 'ui-menu-select', { value: item.value ?? item.label }); }); row.append(action); menu.append(row);
    });
    trigger.addEventListener('click', () => menu.hidden ? open() : close());
    trigger.addEventListener('keydown', event => { if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
    menu.addEventListener('keydown', event => {
      const actions = [...menu.querySelectorAll('[role="menuitem"]')]; const index = actions.indexOf(event.target);
      if (event.key === 'Escape') { close(); trigger.focus(); }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); actions[(index + (event.key === 'ArrowDown' ? 1 : actions.length - 1)) % actions.length]?.focus(); }
      if (event.key === 'Tab') close();
    });
    this.shadowRoot.addEventListener('focusout', event => { if (!this.shadowRoot.contains(event.relatedTarget)) close(); });
  }
}

const components = [
  ['ui-button', UIButton], ['ui-input', UIInput], ['ui-checkbox', UICheckbox], ['ui-select', UISelect],
  ['ui-dialog', UIDialog], ['ui-tooltip', UITooltip], ['ui-toast', UIToast], ['ui-tabs', UITabs], ['ui-menu', UIMenu],
];
for (const [tag, constructor] of components) if (!customElements.get(tag)) customElements.define(tag, constructor);

export const primitiveTags = components.map(([tag]) => tag);
