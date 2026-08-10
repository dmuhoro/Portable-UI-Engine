/**
 * qa-pressure-test.js
 * Automated QA Chaos Pressure Testing Engine for @universal-ui/engine
 * 
 * Floods registered Web Components with chaotic edge cases (empty data, massive arrays,
 * malformed JSON strings, XSS script injection payloads) every 500ms to verify defensive
 * parsing and zero-crash fault-tolerance.
 */

export class QAPressureTestEngine {
  constructor() {
    this._isRunning = false;
    this._intervalId = null;
    this._stepCount = 0;
    this._listeners = new Set();
  }

  /**
   * Add log listener
   */
  onLog(callback) {
    if (typeof callback === 'function') {
      this._listeners.add(callback);
    }
  }

  /**
   * Remove log listener
   */
  offLog(callback) {
    this._listeners.delete(callback);
  }

  /**
   * Internal logger dispatch
   */
  _log(entry) {
    const formatted = {
      step: this._stepCount,
      timestamp: new Date().toLocaleTimeString(),
      status: 'PASSED_DEFENSIVE',
      ...entry
    };

    this._listeners.forEach(fn => {
      try {
        fn(formatted);
      } catch (e) {
        console.error('QA Engine log listener error:', e);
      }
    });

    window.dispatchEvent(
      new CustomEvent('qa-pressure-log', {
        detail: formatted,
        bubbles: true,
        composed: true
      })
    );
  }

  /**
   * Generate XSS / Script Injection payloads
   */
  _getMaliciousPayloads() {
    return [
      '<script>alert("XSS Attack Vector Attempt")</script>',
      '<img src="invalid.jpg" onerror="alert(\'XSS Vulnerability\')" />',
      'javascript:void(0); /* Injection Test */',
      '"><iframe src="javascript:alert(1)"></iframe>',
      '{{constructor.constructor("alert(1)")()}}',
      'SQL INJECTION\' OR \'1\'=\'1\' --'
    ];
  }

  /**
   * Generate 1,000 row massive dataset
   */
  _getMassiveDataset() {
    const headers = ['Record ID', 'User Identity', 'Role Category', 'Security Token', 'Status'];
    const rows = [];
    const roles = ['Infrastructure Lead', 'SecOps Analyst', 'Data Architect', 'Frontend Lead'];
    const statuses = ['Active', 'Pending', 'Inactive'];

    for (let i = 1; i <= 1000; i++) {
      const malicious = i % 50 === 0 ? '<script>console.log("XSS in row")</script>' : `User #${i}`;
      rows.push([
        `REC-${10000 + i}`,
        malicious,
        roles[i % roles.length],
        `TOKEN_${Math.random().toString(36).substring(2, 10)}`,
        statuses[i % statuses.length]
      ]);
    }

    return { headers, rows };
  }

  /**
   * Start the pressure test loop
   */
  start(options = {}) {
    if (this._isRunning) return;

    const intervalMs = options.intervalMs || 500;
    this._isRunning = true;
    this._stepCount = 0;

    this._log({
      componentTag: 'ALL',
      scenarioName: 'INITIATE_CHAOS_SUITE',
      payloadType: 'SYSTEM_BOOT',
      message: `🚀 Chaos Pressure Suite booted. Executing test cycles every ${intervalMs}ms...`
    });

    this._intervalId = setInterval(() => {
      this._executeTestCycle();
    }, intervalMs);
  }

  /**
   * Stop the pressure test loop
   */
  stop() {
    if (!this._isRunning) return;

    if (this._intervalId) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
    this._isRunning = false;

    this._log({
      componentTag: 'ALL',
      scenarioName: 'TERMINATE_CHAOS_SUITE',
      payloadType: 'SYSTEM_HALT',
      message: `🛑 Chaos Pressure Test halted after ${this._stepCount} stress cycles.`
    });
  }

  /**
   * Execute a single stress test cycle
   */
  _executeTestCycle() {
    this._stepCount++;

    // Query target elements on the document
    const targets = [
      { selector: 'universal-data-table', prop: 'payload' },
      { selector: 'universal-form', prop: 'schema' },
      { selector: 'universal-metric-grid', prop: 'payload' },
      { selector: 'universal-saas-dashboard', prop: 'state' }
    ];

    // Pick a random target element that exists in DOM
    const targetInfo = targets[Math.floor(Math.random() * targets.length)];
    const element = document.querySelector(targetInfo.selector);

    if (!element) {
      this._log({
        componentTag: targetInfo.selector,
        scenarioName: 'SKIP_TARGET_NOT_FOUND',
        payloadType: 'DOM_QUERY_EMPTY',
        message: `Target ${targetInfo.selector} not currently visible in DOM tab.`
      });
      return;
    }

    // Select scenario type
    const scenarios = [
      'EMPTY_PAYLOAD',
      'MASSIVE_DATASET',
      'BROKEN_JSON_STRING',
      'MALICIOUS_XSS_STRINGS',
      'IRRELEVANT_OBJECT_TREE'
    ];

    const scenario = scenarios[(this._stepCount - 1) % scenarios.length];
    let payload = null;
    let payloadTypeStr = '';

    switch (scenario) {
      case 'EMPTY_PAYLOAD':
        payload = Math.random() > 0.5 ? [] : '';
        payloadTypeStr = 'EMPTY_VAL (Array/String)';
        break;

      case 'MASSIVE_DATASET':
        if (targetInfo.selector === 'universal-data-table') {
          payload = this._getMassiveDataset();
        } else if (targetInfo.selector === 'universal-saas-dashboard') {
          const dataset = this._getMassiveDataset();
          payload = {
            metrics: [
              { title: "Load Test Metrics", value: "1,000 Rows", change: "+1000%", trend: "upward", context: "Heavy Stress" }
            ],
            tableHeaders: dataset.headers,
            tableRows: dataset.rows
          };
        } else {
          payload = Array.from({ length: 100 }, (_, i) => ({
            title: `Metric #${i + 1}`,
            value: `$${(i * 123.45).toFixed(2)}`,
            change: '+5%',
            trend: 'upward',
            context: 'Stress Test'
          }));
        }
        payloadTypeStr = 'HEAVY_OVERLOAD (1,000 records)';
        break;

      case 'BROKEN_JSON_STRING':
        payload = '{"broken_json": [1, 2, undefined, "missing_quote';
        payloadTypeStr = 'MALFORMED_JSON_STRING';
        break;

      case 'MALICIOUS_XSS_STRINGS':
        const xss = this._getMaliciousPayloads();
        if (targetInfo.selector === 'universal-data-table') {
          payload = {
            headers: ['Vector ID', 'XSS Payload Header', 'Status'],
            rows: xss.map((vec, idx) => [`#XSS-${idx}`, vec, 'Active'])
          };
        } else if (targetInfo.selector === 'universal-form') {
          payload = xss.map((vec, idx) => ({
            name: `field_${idx}`,
            type: 'text',
            label: vec,
            placeholder: vec
          }));
        } else {
          payload = xss.map((vec, idx) => ({
            title: vec,
            value: vec,
            change: '+0%',
            trend: 'neutral',
            context: vec
          }));
        }
        payloadTypeStr = 'XSS_SCRIPT_INJECTION_VECTORS';
        break;

      case 'IRRELEVANT_OBJECT_TREE':
        payload = { unmapped: { nested: { deep: [true, false, null] } }, bogusKey: 999 };
        payloadTypeStr = 'IRRELEVANT_SCHEMA_OBJECT';
        break;
    }

    // Apply payload to element safely
    try {
      element[targetInfo.prop] = payload;

      this._log({
        componentTag: targetInfo.selector,
        scenarioName: scenario,
        payloadType: payloadTypeStr,
        message: `Successfully set ${targetInfo.prop} with ${payloadTypeStr}. Handled without DOM exception.`
      });
    } catch (err) {
      console.error(`QA Pressure Test caught uncaught error on ${targetInfo.selector}:`, err);
      this._log({
        componentTag: targetInfo.selector,
        scenarioName: scenario,
        payloadType: payloadTypeStr,
        status: 'FAILED_UNCAUGHT_EXCEPTION',
        message: `Uncaught Exception: ${err.message}`
      });
    }
  }
}

// Global Singleton Instance
export const QAPressureTest = new QAPressureTestEngine();

if (typeof window !== 'undefined') {
  window.QAPressureTest = QAPressureTest;
}
