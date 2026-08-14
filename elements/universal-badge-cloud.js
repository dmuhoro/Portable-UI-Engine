/**
 * universal-badge-cloud.js
 * Responsive badge/chip grouping with removable tags and click events.
 */

class UniversalBadgeCloud extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._tags = [];
    this._hasParseError = false;
  }

  static get observedAttributes() {
    return ['removable', 'variant'];
  }

  get tags() {
    return this._tags;
  }

  set tags(val) {
    this._parseAndSetTags(val);
  }

  get removable() {
    return this.hasAttribute('removable');
  }

  get variant() {
    const variant = this.getAttribute('variant') || 'default';
    return ['default', 'primary', 'outline'].includes(variant) ? variant : 'default';
  }

  connectedCallback() {
    const tagsAttr = this.getAttribute('tags');
    if (tagsAttr) {
      this._parseAndSetTags(tagsAttr);
    } else {
      this._render();
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    this._render();
  }

  _parseAndSetTags(val) {
    let parsed = val;
    this._hasParseError = false;

    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (err) {
        console.warn('UniversalBadgeCloud: Failed to parse tags JSON string.', err);
        parsed = [];
        this._hasParseError = true;
      }
    }

    if (!Array.isArray(parsed)) {
      parsed = [];
      this._hasParseError = true;
    }

    this._tags = parsed.map((tag, index) => {
      if (typeof tag === 'string') {
        return { id: `tag-${index}`, label: tag, color: null };
      }
      return {
        id: tag.id ?? `tag-${index}`,
        label: tag.label ?? String(tag),
        color: tag.color ?? null,
      };
    });

    this._render();
  }

  _escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  _render() {
    const variant = this.variant;
    const removable = this.removable;

    let content = '';

    if (this._hasParseError) {
      content = `
        <div class="empty-state">
          <strong>Invalid tags format</strong>
          <p>Tags must be a valid JSON array.</p>
        </div>
      `;
    } else if (this._tags.length === 0) {
      content = `<div class="empty-state"><p>No tags to display</p></div>`;
    } else {
      content = this._tags
        .map((tag) => {
          const style = tag.color ? ` style="--badge-custom-color: ${this._escapeHtml(tag.color)};"` : '';
          return `
            <button type="button" class="badge variant-${variant}" data-id="${this._escapeHtml(tag.id)}"${style}>
              <span class="badge-label">${this._escapeHtml(tag.label)}</span>
              ${removable ? '<span class="badge-remove" aria-hidden="true">&times;</span>' : ''}
            </button>
          `;
        })
        .join('');
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-sans, system-ui, -apple-system, sans-serif);
        }

        .badge-cloud {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-2, 8px);
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: var(--spacing-1, 4px);
          padding: var(--spacing-1, 4px) var(--spacing-3, 12px);
          border-radius: var(--radius-full, 9999px);
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-medium, 500);
          cursor: pointer;
          border: 1px solid transparent;
          transition: all var(--transition-fast, 150ms ease);
          background-color: var(--color-primary-light, #eff6ff);
          color: var(--color-primary, #2563eb);
        }

        .badge.variant-primary {
          background-color: var(--color-primary, #2563eb);
          color: var(--color-text-inverse, #ffffff);
        }

        .badge.variant-outline {
          background-color: transparent;
          border-color: var(--color-primary, #2563eb);
          color: var(--color-primary, #2563eb);
        }

        .badge[style*="--badge-custom-color"] {
          background-color: var(--badge-custom-color);
          color: var(--color-text-inverse, #ffffff);
        }

        .badge:hover {
          opacity: 0.85;
        }

        .badge-remove {
          font-size: var(--font-size-sm, 14px);
          line-height: 1;
          margin-left: var(--spacing-1, 4px);
        }

        .empty-state {
          padding: var(--spacing-3, 12px);
          text-align: center;
          color: var(--color-text-muted, #94a3b8);
          font-size: var(--font-size-xs, 12px);
        }

        .empty-state strong {
          display: block;
          color: var(--color-danger, #dc2626);
          margin-bottom: var(--spacing-1, 4px);
        }
      </style>
      <div class="badge-cloud" part="cloud">${content}</div>
    `;

    this.shadowRoot.querySelectorAll('.badge').forEach((badgeEl) => {
      badgeEl.addEventListener('click', (e) => {
        const id = badgeEl.getAttribute('data-id');
        const tag = this._tags.find((t) => t.id === id);
        if (!tag) return;

        if (removable && e.target.classList.contains('badge-remove')) {
          e.stopPropagation();
          this._tags = this._tags.filter((t) => t.id !== id);
          this.dispatchEvent(
            new CustomEvent('tag-remove', {
              detail: { removedTag: tag, remainingTags: [...this._tags] },
              bubbles: true,
              composed: true,
            })
          );
          this._render();
        } else {
          this.dispatchEvent(
            new CustomEvent('tag-click', {
              detail: { tag },
              bubbles: true,
              composed: true,
            })
          );
        }
      });
    });
  }
}

if (!customElements.get('universal-badge-cloud')) {
  customElements.define('universal-badge-cloud', UniversalBadgeCloud);
}
