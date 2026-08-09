/**
 * universal-form.js
 * Portable UI Engine - Native Data-Driven Form Web Component
 * Accepts a JSON layout schema via 'schema' attribute or JS property.
 * Performs client-side HTML5 validation and dispatches 'app-form-submit' CustomEvent.
 */
class UniversalForm extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._schema = [];
    this._title = 'Submit Data';
    this._submitLabel = 'Save Record';
  }

  static get observedAttributes() {
    return ['schema', 'title', 'submit-label'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    if (name === 'schema') {
      this._parseAndSetSchema(newValue);
    } else if (name === 'title') {
      this._title = newValue || '';
      this._updateFormHeader();
    } else if (name === 'submit-label') {
      this._submitLabel = newValue || 'Save Record';
      this._updateSubmitBtnLabel();
    }
  }

  get schema() {
    return this._schema;
  }

  set schema(val) {
    this._schema = val;
    this._parseAndSetSchema(val);
  }

  get title() {
    return this._title;
  }

  set title(val) {
    this._title = val;
    this.setAttribute('title', val);
  }

  connectedCallback() {
    this.render();
    this._setupFormEvents();
  }

  _parseAndSetSchema(val) {
    let parsed = val;
    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (err) {
        console.warn('UniversalForm: Failed to parse schema JSON string.', err);
        parsed = [];
      }
    }
    this._schema = Array.isArray(parsed) ? parsed : [];
    this._renderFields();
  }

  getFormData() {
    const formEl = this.shadowRoot?.querySelector('form');
    if (!formEl) return {};

    const formData = new FormData(formEl);
    const result = {};

    this._schema.forEach(field => {
      const name = field.name;
      if (!name) return;

      if (field.type === 'checkbox') {
        result[name] = formData.has(name);
      } else if (field.type === 'number') {
        const raw = formData.get(name);
        result[name] = raw !== null && raw !== '' ? Number(raw) : null;
      } else {
        result[name] = formData.get(name) ?? '';
      }
    });

    return result;
  }

  reset() {
    const formEl = this.shadowRoot?.querySelector('form');
    if (formEl) {
      formEl.reset();
      this._clearValidationErrors();
    }
  }

  validate() {
    const formEl = this.shadowRoot?.querySelector('form');
    if (!formEl) return false;

    this._clearValidationErrors();
    let isValid = true;

    this._schema.forEach(field => {
      const inputEl = formEl.elements.namedItem(field.name);
      if (!inputEl) return;

      const groupEl = inputEl.closest('.form-group');
      const errorEl = groupEl?.querySelector('.error-msg');

      if (!inputEl.checkValidity()) {
        isValid = false;
        if (groupEl) groupEl.classList.add('has-error');
        if (errorEl) {
          errorEl.textContent = inputEl.validationMessage || `${field.label || field.name} is invalid.`;
          errorEl.style.display = 'block';
        }
      }
    });

    return isValid;
  }

  _clearValidationErrors() {
    const formEl = this.shadowRoot?.querySelector('form');
    if (!formEl) return;

    const groups = formEl.querySelectorAll('.form-group');
    groups.forEach(group => {
      group.classList.remove('has-error');
      const errorEl = group.querySelector('.error-msg');
      if (errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
      }
    });
  }

  _setupFormEvents() {
    const formEl = this.shadowRoot?.querySelector('form');
    formEl?.addEventListener('submit', (e) => {
      e.preventDefault();

      if (!this.validate()) {
        return;
      }

      const payload = this.getFormData();

      this.dispatchEvent(
        new CustomEvent('app-form-submit', {
          detail: { formData: payload },
          bubbles: true,
          composed: true,
        })
      );
    });

    // Real-time error clearance on input
    formEl?.addEventListener('input', (e) => {
      const target = e.target;
      const group = target.closest('.form-group');
      if (group && group.classList.contains('has-error')) {
        if (target.checkValidity()) {
          group.classList.remove('has-error');
          const err = group.querySelector('.error-msg');
          if (err) err.style.display = 'none';
        }
      }
    });
  }

  _updateFormHeader() {
    const h2 = this.shadowRoot?.querySelector('.form-title');
    if (h2) h2.textContent = this._title;
  }

  _updateSubmitBtnLabel() {
    const btn = this.shadowRoot?.querySelector('.submit-btn-text');
    if (btn) btn.textContent = this._submitLabel;
  }

  _renderFields() {
    const fieldsContainer = this.shadowRoot?.querySelector('.fields-container');
    if (!fieldsContainer) return;

    if (!this._schema || this._schema.length === 0) {
      fieldsContainer.innerHTML = `<p class="empty-schema-msg">No form schema supplied.</p>`;
      return;
    }

    fieldsContainer.innerHTML = this._schema
      .map(field => this._buildFieldHtml(field))
      .join('');
  }

  _buildFieldHtml(field) {
    const name = this._escapeHtml(field.name || '');
    const label = this._escapeHtml(field.label || field.name || '');
    const required = field.required ? 'required' : '';
    const reqMark = field.required ? '<span class="required-star">*</span>' : '';
    const placeholder = field.placeholder ? `placeholder="${this._escapeHtml(field.placeholder)}"` : '';
    const defaultValue = field.defaultValue !== undefined ? field.defaultValue : '';
    const type = field.type || 'text';

    if (type === 'select') {
      const options = Array.isArray(field.options) ? field.options : [];
      const optionsHtml = options
        .map(opt => {
          const val = typeof opt === 'object' ? opt.value : opt;
          const text = typeof opt === 'object' ? opt.label : opt;
          const selected = String(val) === String(defaultValue) ? 'selected' : '';
          return `<option value="${this._escapeHtml(val)}" ${selected}>${this._escapeHtml(text)}</option>`;
        })
        .join('');

      return `
        <div class="form-group">
          <label for="field-${name}">${label} ${reqMark}</label>
          <select id="field-${name}" name="${name}" ${required} class="form-control">
            ${optionsHtml}
          </select>
          <span class="error-msg"></span>
        </div>
      `;
    }

    if (type === 'textarea') {
      return `
        <div class="form-group form-group-full">
          <label for="field-${name}">${label} ${reqMark}</label>
          <textarea
            id="field-${name}"
            name="${name}"
            rows="${field.rows || 3}"
            ${placeholder}
            ${required}
            class="form-control"
          >${this._escapeHtml(defaultValue)}</textarea>
          <span class="error-msg"></span>
        </div>
      `;
    }

    if (type === 'checkbox') {
      const checked = defaultValue ? 'checked' : '';
      return `
        <div class="form-group form-group-checkbox">
          <label class="checkbox-label">
            <input type="checkbox" id="field-${name}" name="${name}" ${checked} />
            <span>${label}</span>
          </label>
          <span class="error-msg"></span>
        </div>
      `;
    }

    return `
      <div class="form-group">
        <label for="field-${name}">${label} ${reqMark}</label>
        <input
          type="${type}"
          id="field-${name}"
          name="${name}"
          value="${this._escapeHtml(defaultValue)}"
          ${placeholder}
          ${required}
          class="form-control"
        />
        <span class="error-msg"></span>
      </div>
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

        .form-card {
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          box-shadow: var(--shadow-sm, 0 1px 2px 0 rgba(0,0,0,0.05));
          padding: var(--spacing-6, 24px);
        }

        .form-header {
          margin-bottom: var(--spacing-5, 20px);
          padding-bottom: var(--spacing-3, 12px);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
        }

        .form-title {
          font-size: var(--font-size-lg, 18px);
          font-weight: var(--font-weight-bold, 700);
          margin: 0;
          color: var(--color-text-primary, #0f172a);
        }

        .fields-container {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: var(--spacing-4, 16px);
        }

        .form-group-full {
          grid-column: 1 / -1;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-1, 4px);
        }

        label {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          color: var(--color-text-secondary, #475569);
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }

        .required-star {
          color: var(--color-danger, #dc2626);
        }

        .form-control {
          width: 100%;
          padding: var(--spacing-2, 8px) var(--spacing-3, 12px);
          font-size: var(--font-size-sm, 14px);
          font-family: inherit;
          color: var(--color-text-primary, #0f172a);
          background-color: var(--color-bg-app, #f8fafc);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          outline: none;
          box-sizing: border-box;
          transition: border-color var(--transition-fast, 150ms ease), box-shadow var(--transition-fast, 150ms ease), background-color var(--transition-fast, 150ms ease);
        }

        .form-control:focus {
          border-color: var(--color-primary, #2563eb);
          background-color: var(--color-bg-surface, #ffffff);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }

        textarea.form-control {
          resize: vertical;
          min-height: 80px;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-medium, 500);
          color: var(--color-text-primary, #0f172a);
          text-transform: none;
          cursor: pointer;
          margin-top: var(--spacing-4, 16px);
        }

        .checkbox-label input[type="checkbox"] {
          width: 16px;
          height: 16px;
          accent-color: var(--color-primary, #2563eb);
          cursor: pointer;
        }

        /* Error States */
        .form-group.has-error .form-control {
          border-color: var(--color-danger, #dc2626);
          background-color: var(--color-danger-bg, #fef2f2);
        }

        .error-msg {
          display: none;
          font-size: var(--font-size-xs, 12px);
          color: var(--color-danger, #dc2626);
          font-weight: var(--font-weight-medium, 500);
          margin-top: 2px;
        }

        /* Form Footer & Actions */
        .form-actions {
          margin-top: var(--spacing-6, 24px);
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-3, 12px);
        }

        .submit-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-2, 8px);
          padding: var(--spacing-2, 8px) var(--spacing-5, 20px);
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-semibold, 600);
          color: var(--color-text-inverse, #ffffff);
          background-color: var(--color-primary, #2563eb);
          border: 1px solid var(--color-primary, #2563eb);
          border-radius: var(--radius-md, 6px);
          cursor: pointer;
          transition: background-color var(--transition-fast, 150ms ease), border-color var(--transition-fast, 150ms ease), transform var(--transition-fast, 150ms ease);
        }

        .submit-btn:hover {
          background-color: var(--color-primary-hover, #1d4ed8);
          border-color: var(--color-primary-hover, #1d4ed8);
        }

        .submit-btn:active {
          transform: translateY(1px);
        }

        .empty-schema-msg {
          color: var(--color-text-muted, #94a3b8);
          font-size: var(--font-size-sm, 14px);
          font-style: italic;
        }
      </style>

      <div class="form-card">
        <div class="form-header">
          <h2 class="form-title">${this._escapeHtml(this._title)}</h2>
        </div>
        <form novalidate>
          <div class="fields-container"></div>
          <div class="form-actions">
            <button type="submit" class="submit-btn">
              <span class="submit-btn-text">${this._escapeHtml(this._submitLabel)}</span>
            </button>
          </div>
        </form>
      </div>
    `;
  }
}

if (!customElements.get('universal-form')) {
  customElements.define('universal-form', UniversalForm);
}
