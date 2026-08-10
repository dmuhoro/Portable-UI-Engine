/**
 * universal-data-table.js
 * Portable UI Engine - Native Data-Driven Table Custom Element
 * Observes 'payload' attribute, parses incoming JSON data (headers and rows),
 * and dynamically builds a semantic HTML table with striped rows, hover effects, search, and sorting.
 */
class UniversalDataTable extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._payload = null;
    this._parsedData = { headers: [], rows: [] };
    this._searchTerm = '';
    this._sortColumn = null;
    this._sortAsc = true;
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
    this._setupEvents();
    if ((!this._parsedData.headers.length && !this._parsedData.rows.length) || !this._payload) {
      this._parseLightDomTable();
    }
  }

  _parseLightDomTable() {
    // Skip fallback if payload already supplied valid records
    if (this._payload && (this._parsedData.headers.length > 0 || this._parsedData.rows.length > 0)) {
      return false;
    }

    const lightTable = this.querySelector('table');
    if (!lightTable) {
      return false;
    }

    const headers = [];
    const rows = [];

    // Extract headers from <thead> <th> or <tr> <th>
    const thElements = lightTable.querySelectorAll('thead th, tr:first-child th');
    if (thElements.length > 0) {
      thElements.forEach(th => headers.push(th.textContent.trim()));
    }

    // Extract rows from <tbody> <tr> or direct <tr> elements
    const trElements = lightTable.querySelectorAll('tbody tr, tr');
    trElements.forEach(tr => {
      if (tr.parentElement && tr.parentElement.tagName.toLowerCase() === 'thead') return;
      const tdElements = tr.querySelectorAll('td');
      if (tdElements.length > 0) {
        const row = Array.from(tdElements).map(td => td.textContent.trim());
        rows.push(row);
      }
    });

    if (headers.length > 0 || rows.length > 0) {
      this._hasParseError = false;
      this._parsedData = { headers, rows };
      this._renderHeaders();
      this._renderTableBody();
      return true;
    }

    return false;
  }

  _parseAndSetPayload(val) {
    let data = val;
    let parseError = false;

    if (typeof val === 'string') {
      try {
        data = JSON.parse(val);
      } catch (e) {
        console.warn('UniversalDataTable: Invalid JSON string supplied to payload attribute.', e);
        data = null;
        parseError = true;
      }
    }

    this._hasParseError = parseError;
    this._parsedData = this._normalizePayload(data);

    // HTMX / Light DOM Fallback if payload is missing or empty
    if (!parseError && (!this._parsedData.headers.length && !this._parsedData.rows.length)) {
      if (this._parseLightDomTable()) {
        return;
      }
    }

    this._renderTableBody();
  }

  _normalizePayload(data) {
    if (!data) {
      return { headers: [], rows: [] };
    }

    // Format 1: Object with headers and rows
    if (typeof data === 'object' && !Array.isArray(data)) {
      if (Array.isArray(data.rows)) {
        let headers = [];
        if (Array.isArray(data.headers)) {
          headers = data.headers.map(h => (typeof h === 'object' ? h.label || h.key : String(h)));
        } else if (data.rows.length > 0 && typeof data.rows[0] === 'object' && !Array.isArray(data.rows[0])) {
          headers = Object.keys(data.rows[0]).map(k => this._capitalize(k));
        }

        const rows = data.rows.map(row => {
          if (Array.isArray(row)) return row;
          if (typeof row === 'object' && row !== null) {
            if (Array.isArray(data.headers) && typeof data.headers[0] === 'object' && data.headers[0].key) {
              return data.headers.map(h => row[h.key] ?? '');
            }
            return Object.values(row);
          }
          return [row];
        });

        return { headers, rows };
      }
    }

    // Format 2: Direct Array of Objects or Values
    if (Array.isArray(data)) {
      if (data.length === 0) return { headers: [], rows: [] };

      if (typeof data[0] !== 'object' || data[0] === null) {
        return {
          headers: ['Value'],
          rows: data.map(item => [item]),
        };
      }

      const keySet = new Set();
      data.forEach(item => {
        if (item && typeof item === 'object') {
          Object.keys(item).forEach(k => keySet.add(k));
        }
      });

      const keys = Array.from(keySet);
      const headers = keys.map(k => this._capitalize(k));
      const rows = data.map(item => keys.map(k => item[k] ?? ''));

      return { headers, rows };
    }

    return { headers: [], rows: [] };
  }

  _capitalize(str) {
    return String(str)
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, s => s.toUpperCase())
      .replace(/_/g, ' ')
      .trim();
  }

  _getFilteredAndSortedRows() {
    let rows = [...this._parsedData.rows];

    // Search filter
    if (this._searchTerm.trim() !== '') {
      const query = this._searchTerm.toLowerCase();
      rows = rows.filter(row =>
        row.some(cell => String(cell).toLowerCase().includes(query))
      );
    }

    // Sorting
    if (this._sortColumn !== null && this._sortColumn < this._parsedData.headers.length) {
      const index = this._sortColumn;
      const asc = this._sortAsc;
      rows.sort((a, b) => {
        const valA = a[index] ?? '';
        const valB = b[index] ?? '';

        if (typeof valA === 'number' && typeof valB === 'number') {
          return asc ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return asc ? -1 : 1;
        if (strA > strB) return asc ? 1 : -1;
        return 0;
      });
    }

    return rows;
  }

  _setupEvents() {
    const searchInput = this.shadowRoot.querySelector('.table-search-input');
    searchInput?.addEventListener('input', e => {
      this._searchTerm = e.target.value;
      this._renderTableBody();
    });

    const thead = this.shadowRoot.querySelector('thead');
    const triggerSort = (e) => {
      const th = e.target.closest('th');
      if (th && th.dataset.index !== undefined) {
        const colIndex = parseInt(th.dataset.index, 10);
        if (this._sortColumn === colIndex) {
          this._sortAsc = !this._sortAsc;
        } else {
          this._sortColumn = colIndex;
          this._sortAsc = true;
        }
        this._renderHeaders();
        this._renderTableBody();
      }
    };

    thead?.addEventListener('click', triggerSort);
    thead?.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        triggerSort(e);
      }
    });
  }

  _renderHeaders() {
    const thead = this.shadowRoot.querySelector('thead tr');
    if (!thead) return;

    if (this._parsedData.headers.length === 0) {
      thead.innerHTML = '';
      return;
    }

    thead.innerHTML = this._parsedData.headers
      .map((header, index) => {
        const isSorted = this._sortColumn === index;
        const sortAttr = isSorted ? (this._sortAsc ? 'ascending' : 'descending') : 'none';
        const arrow = isSorted ? (this._sortAsc ? ' ↑' : ' ↓') : '';
        return `
        <th data-index="${index}" class="${isSorted ? 'sorted' : ''}" scope="col" role="columnheader" tabindex="0" aria-sort="${sortAttr}">
          <span>${this._escapeHtml(header)}</span>
          <span class="sort-icon">${arrow}</span>
        </th>
      `;
      })
      .join('');
  }

  _renderTableBody() {
    const tbody = this.shadowRoot.querySelector('tbody');
    const emptyState = this.shadowRoot.querySelector('.empty-state');
    const tableContainer = this.shadowRoot.querySelector('.table-wrapper');
    const countBadge = this.shadowRoot.querySelector('.row-count-badge');

    this._renderHeaders();

    if (!tbody) return;

    if (this._hasParseError) {
      tbody.innerHTML = '';
      if (countBadge) countBadge.textContent = '0 records';
      if (emptyState) {
        emptyState.style.display = 'flex';
        const titleEl = emptyState.querySelector('.empty-title');
        const subEl = emptyState.querySelector('.empty-sub');
        if (titleEl) titleEl.textContent = 'Invalid Data Format Provided';
        if (subEl) subEl.textContent = 'Failed to parse JSON string or malformed table payload provided.';
      }
      if (tableContainer) tableContainer.style.display = 'none';
      return;
    }

    const rows = this._getFilteredAndSortedRows();

    if (countBadge) {
      countBadge.textContent = `${rows.length} ${rows.length === 1 ? 'record' : 'records'}`;
    }

    if (this._parsedData.headers.length === 0 || rows.length === 0) {
      tbody.innerHTML = '';
      if (emptyState) {
        emptyState.style.display = 'flex';
        const titleEl = emptyState.querySelector('.empty-title');
        const subEl = emptyState.querySelector('.empty-sub');
        if (titleEl) titleEl.textContent = 'No Active Records Available';
        if (subEl) subEl.textContent = 'Inject a valid JSON payload to render data rows.';
      }
      if (tableContainer) tableContainer.style.display = 'none';
      return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (tableContainer) tableContainer.style.display = 'block';

    tbody.innerHTML = rows
      .map((row, rowIndex) => {
        const cellsHtml = row
          .map(cell => `<td role="cell">${this._formatCellValue(cell)}</td>`)
          .join('');
        return `<tr data-row-index="${rowIndex}" role="row">${cellsHtml}</tr>`;
      })
      .join('');
  }

  _formatCellValue(val) {
    if (val === null || val === undefined) return '<span class="cell-muted">—</span>';

    const str = String(val);
    const lower = str.toLowerCase();

    if (['active', 'healthy', 'completed', 'success', 'passed'].includes(lower)) {
      return `<span class="badge badge-success">${this._escapeHtml(str)}</span>`;
    }
    if (['pending', 'warning', 'in progress', 'processing'].includes(lower)) {
      return `<span class="badge badge-warning">${this._escapeHtml(str)}</span>`;
    }
    if (['failed', 'error', 'inactive', 'blocked', 'critical'].includes(lower)) {
      return `<span class="badge badge-danger">${this._escapeHtml(str)}</span>`;
    }

    return this._escapeHtml(str);
  }

  _escapeHtml(str) {
    return String(str)
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

        .table-card {
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          box-shadow: var(--shadow-sm, 0 1px 2px 0 rgba(0,0,0,0.05));
          overflow: hidden;
        }

        /* Toolbar Header */
        .table-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--spacing-4, 16px);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
          background-color: var(--color-bg-surface, #ffffff);
          gap: var(--spacing-3, 12px);
          flex-wrap: wrap;
        }

        .toolbar-left {
          display: flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
        }

        .table-title {
          font-size: var(--font-size-md, 16px);
          font-weight: var(--font-weight-semibold, 600);
          margin: 0;
        }

        .row-count-badge {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-medium, 500);
          color: var(--color-text-secondary, #475569);
          background-color: var(--color-bg-hover, #f1f5f9);
          padding: 2px 8px;
          border-radius: var(--radius-full, 9999px);
          border: 1px solid var(--color-border, #e2e8f0);
        }

        .table-search-input {
          padding: var(--spacing-2, 8px) var(--spacing-3, 12px);
          font-size: var(--font-size-sm, 14px);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          background-color: var(--color-bg-app, #f8fafc);
          color: var(--color-text-primary, #0f172a);
          outline: none;
          min-width: 200px;
          transition: border-color var(--transition-fast, 150ms ease), box-shadow var(--transition-fast, 150ms ease);
        }

        .table-search-input:focus {
          border-color: var(--color-primary, #2563eb);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
          background-color: var(--color-bg-surface, #ffffff);
        }

        /* Responsive Scrollable Container */
        .table-wrapper {
          width: 100%;
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
          font-size: var(--font-size-sm, 14px);
        }

        thead {
          background-color: var(--color-bg-hover, #f1f5f9);
          border-bottom: 1px solid var(--color-border, #e2e8f0);
        }

        th {
          padding: var(--spacing-3, 12px) var(--spacing-4, 16px);
          font-weight: var(--font-weight-semibold, 600);
          color: var(--color-text-secondary, #475569);
          user-select: none;
          cursor: pointer;
          white-space: nowrap;
          transition: background-color var(--transition-fast, 150ms ease);
        }

        th:hover {
          background-color: var(--color-bg-active, #e2e8f0);
          color: var(--color-text-primary, #0f172a);
        }

        th.sorted {
          color: var(--color-primary, #2563eb);
        }

        .sort-icon {
          display: inline-block;
          min-width: 12px;
          font-weight: var(--font-weight-bold, 700);
        }

        /* Table Body & Striped Rows */
        tbody tr {
          border-bottom: 1px solid var(--color-border, #e2e8f0);
          transition: background-color var(--transition-fast, 150ms ease);
        }

        tbody tr:last-child {
          border-bottom: none;
        }

        /* Striped rows style requirement */
        tbody tr:nth-child(even) {
          background-color: var(--color-bg-stripe, #f8fafc);
        }

        /* Hover effect requirement */
        tbody tr:hover {
          background-color: var(--color-bg-hover, #f1f5f9);
        }

        td {
          padding: var(--spacing-3, 12px) var(--spacing-4, 16px);
          color: var(--color-text-primary, #0f172a);
          vertical-align: middle;
        }

        .cell-muted {
          color: var(--color-text-muted, #94a3b8);
        }

        /* Status Badges */
        .badge {
          display: inline-flex;
          align-items: center;
          padding: 2px 10px;
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          border-radius: var(--radius-full, 9999px);
          line-height: var(--line-height-tight, 1.25);
          white-space: nowrap;
        }

        .badge-success {
          background-color: var(--color-success-bg, #f0fdf4);
          color: var(--color-success, #16a34a);
          border: 1px solid rgba(22, 163, 74, 0.2);
        }

        .badge-warning {
          background-color: var(--color-warning-bg, #fffbeb);
          color: var(--color-warning, #d97706);
          border: 1px solid rgba(217, 119, 6, 0.2);
        }

        .badge-danger {
          background-color: var(--color-danger-bg, #fef2f2);
          color: var(--color-danger, #dc2626);
          border: 1px solid rgba(220, 38, 38, 0.2);
        }

        /* Empty State */
        .empty-state {
          display: none;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--spacing-12, 48px) var(--spacing-6, 24px);
          text-align: center;
          color: var(--color-text-muted, #94a3b8);
        }

        .empty-icon {
          width: 48px;
          height: 48px;
          margin-bottom: var(--spacing-3, 12px);
          stroke: currentColor;
          fill: none;
          stroke-width: 1.5;
        }

        .empty-title {
          font-size: var(--font-size-base, 16px);
          font-weight: var(--font-weight-medium, 500);
          color: var(--color-text-secondary, #475569);
          margin: 0 0 var(--spacing-1, 4px) 0;
        }

        .empty-sub {
          font-size: var(--font-size-sm, 14px);
          margin: 0;
        }
      </style>

      <div class="table-card">
        <slot style="display:none;"></slot>
        <div class="table-toolbar">
          <div class="toolbar-left">
            <h2 class="table-title">Data Records</h2>
            <span class="row-count-badge">0 records</span>
          </div>
          <input
            type="text"
            class="table-search-input"
            placeholder="Search records..."
            aria-label="Filter data table rows"
          />
        </div>

        <div class="table-wrapper">
          <table role="table">
            <thead role="rowgroup">
              <tr role="row"></tr>
            </thead>
            <tbody role="rowgroup"></tbody>
          </table>
        </div>

        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24">
            <path d="M4 6h16M4 12h16M4 18h7" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="empty-title">No data available</p>
          <p class="empty-sub">Inject a valid JSON payload to render records.</p>
        </div>
      </div>
    `;
  }
}

if (!customElements.get('universal-data-table')) {
  customElements.define('universal-data-table', UniversalDataTable);
}
