/**
 * tests/engine.test.js
 * Automated Unit Test Suite for Portable UI Engine (@universal-ui/engine)
 * Verifies element registrations, fault-tolerance fallbacks, and event emissions.
 */

import '../engine.js';

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

describe('Portable UI Engine - Component Suite', () => {

  describe('Custom Element Registrations', () => {
    it('registers all universal components on customElements registry', () => {
      assert(Boolean(customElements.get('universal-app-shell')), '<universal-app-shell> must be registered');
      assert(Boolean(customElements.get('universal-data-table')), '<universal-data-table> must be registered');
      assert(Boolean(customElements.get('universal-form')), '<universal-form> must be registered');
      assert(Boolean(customElements.get('universal-metric-grid')), '<universal-metric-grid> must be registered');
      assert(Boolean(customElements.get('universal-saas-dashboard')), '<universal-saas-dashboard> must be registered');
      assert(Boolean(customElements.get('universal-billing-funnel')), '<universal-billing-funnel> must be registered');
      assert(Boolean(customElements.get('universal-ai-bridge')), '<universal-ai-bridge> must be registered');
    });

    it('instantiates elements and attaches Shadow DOM cleanly', () => {
      const table = document.createElement('universal-data-table');
      const form = document.createElement('universal-form');
      const shell = document.createElement('universal-app-shell');
      const metrics = document.createElement('universal-metric-grid');

      document.body.appendChild(table);
      document.body.appendChild(form);
      document.body.appendChild(shell);
      document.body.appendChild(metrics);

      assert(table.shadowRoot !== null, 'Table must attach Shadow DOM');
      assert(form.shadowRoot !== null, 'Form must attach Shadow DOM');
      assert(shell.shadowRoot !== null, 'Shell must attach Shadow DOM');
      assert(metrics.shadowRoot !== null, 'Metrics must attach Shadow DOM');

      document.body.removeChild(table);
      document.body.removeChild(form);
      document.body.removeChild(shell);
      document.body.removeChild(metrics);
    });
  });

  describe('Fault-Tolerance & Malformed Data Fallbacks', () => {
    it('gracefully renders tokenized error fallback on invalid JSON payload in data-table', () => {
      const table = document.createElement('universal-data-table');
      document.body.appendChild(table);

      // Apply malformed JSON string attribute
      table.setAttribute('payload', '{ invalid: json string }}}');

      const emptyState = table.shadowRoot.querySelector('.empty-state');
      assert(emptyState !== null, 'Empty state element should exist in shadow DOM');
      assert(emptyState.style.display !== 'none', 'Empty state should be displayed on malformed data');

      const title = emptyState.querySelector('.empty-title');
      assert(title.textContent.includes('Invalid Data Format Provided'), 'Should display tokenized error fallback title');

      document.body.removeChild(table);
    });

    it('gracefully renders error fallback on invalid schema in form', () => {
      const form = document.createElement('universal-form');
      document.body.appendChild(form);

      form.schema = '{ malformed: schema }';

      const fieldsContainer = form.shadowRoot.querySelector('.fields-container');
      assert(fieldsContainer.textContent.includes('Invalid Data Format'), 'Form displays tokenized error fallback');

      document.body.removeChild(form);
    });
  });

  describe('Theme Controller & Persistence Layer', () => {
    it('persists active theme preference to localStorage and sets data-theme attribute', () => {
      window.UniversalUI.setTheme('cyberpunk');
      assert(document.documentElement.getAttribute('data-theme') === 'cyberpunk', 'data-theme attribute must be cyberpunk');
      assert(localStorage.getItem('universal-ui-theme') === 'cyberpunk', 'localStorage must contain universal-ui-theme preference');
      
      // Reset back to light
      window.UniversalUI.setTheme('light');
      assert(document.documentElement.getAttribute('data-theme') === 'light', 'data-theme attribute must reset to light');
    });
  });

  describe('Declarative HTML Table Ingestion (HTMX Bridge)', () => {
    it('parses semantic light DOM <table> element when payload property is omitted', () => {
      const tableComponent = document.createElement('universal-data-table');
      tableComponent.innerHTML = `
        <table>
          <thead>
            <tr><th>Endpoint</th><th>Latency</th></tr>
          </thead>
          <tbody>
            <tr><td>/api/v1/auth</td><td>12ms</td></tr>
            <tr><td>/api/v1/data</td><td>25ms</td></tr>
          </tbody>
        </table>
      `;

      document.body.appendChild(tableComponent);

      const headers = tableComponent.shadowRoot.querySelectorAll('th');
      assert(headers.length === 2, 'Should parse 2 th headers from light DOM table');
      assert(headers[0].textContent.includes('Endpoint'), 'First header text must match light DOM table');

      const rows = tableComponent.shadowRoot.querySelectorAll('tbody tr');
      assert(rows.length === 2, 'Should parse 2 tbody rows from light DOM table');

      document.body.removeChild(tableComponent);
    });
  });

  describe('Form Submissions & Custom Events', () => {
    it('blocks native submit and dispatches app-form-submit event with sanitized formData', (done) => {
      const form = document.createElement('universal-form');
      document.body.appendChild(form);

      form.schema = [
        { name: 'username', type: 'text', label: 'Username', required: true, defaultValue: 'alex_m' },
        { name: 'email', type: 'email', label: 'Email', required: true, defaultValue: 'alex@corp.internal' }
      ];

      form.addEventListener('app-form-submit', (e) => {
        try {
          assert(e.detail !== undefined, 'Event detail should exist');
          assert(e.detail.formData !== undefined, 'formData map should exist in event detail');
          assert(e.detail.formData.username === 'alex_m', 'formData username should match input');
          assert(e.detail.formData.email === 'alex@corp.internal', 'formData email should match input');
          document.body.removeChild(form);
          done();
        } catch (err) {
          document.body.removeChild(form);
          done(err);
        }
      });

      const nativeForm = form.shadowRoot.querySelector('form');
      assert(nativeForm !== null, 'Form shadow DOM must contain <form>');

      const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
      nativeForm.dispatchEvent(submitEvent);

      assert(submitEvent.defaultPrevented, 'Standard form submit must be defaultPrevented');
    });
  });

});
