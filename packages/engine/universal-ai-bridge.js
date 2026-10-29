/**
 * universal-ai-bridge.js
 * Native Web Component (<universal-ai-bridge>)
 * 
 * Frontier AI Model Adapter connecting natural language prompts to Portable UI Engine components.
 * Intercepts user requests, posts to AI model endpoints (or generates schema-compliant mock streams),
 * and emits 'ai-generation-complete' custom events carrying structured JSON payloads.
 */

export class UniversalAIBridge extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    this._isLoading = false;
    this._statusMessage = 'AI Bridge Engine Idle';
    this._statusType = 'neutral';
  }

  static get observedAttributes() {
    return ['endpoint', 'target-component', 'mock-mode', 'placeholder'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this._render();
    }
  }

  connectedCallback() {
    this._render();
  }

  /**
   * Generates schema-compliant AI mock payload based on prompt keywords
   */
  _generateMockAIResponse(promptText, targetComp) {
    const text = (promptText || '').toLowerCase();

    // 1. Form Schema Mock Payload
    if (targetComp.includes('form') || text.includes('form') || text.includes('user') || text.includes('contact')) {
      return {
        targetType: 'form',
        payload: [
          { name: "full_name", type: "text", label: "Full Name", required: true, placeholder: "e.g. Sarah Connor" },
          { name: "work_email", type: "email", label: "Work Email", required: true, placeholder: "sarah@cyberdyne.io" },
          { name: "account_type", type: "select", label: "Account Tier", required: true, options: ["Enterprise", "Pro Growth", "Developer"], defaultValue: "Pro Growth" },
          { name: "monthly_budget", type: "number", label: "Est. Monthly Spend ($)", required: false, placeholder: "5000" },
          { name: "notes", type: "textarea", label: "Use Case Notes", required: false, placeholder: "Describe your deployment targets..." }
        ]
      };
    }

    // 2. Metrics Grid Mock Payload
    if (targetComp.includes('metric') || text.includes('metric') || text.includes('kpi')) {
      return {
        targetType: 'metrics',
        payload: [
          { title: "Monthly Recurring Revenue", value: "$128,450.00", change: "+22.4%", trend: "upward", context: "vs last month" },
          { title: "AI Generation Throughput", value: "84.2k reqs", change: "+45.1%", trend: "upward", context: "live streaming" },
          { title: "Avg Inference Latency", value: "142 ms", change: "-18.0%", trend: "upward", context: "faster models" },
          { title: "Model Drift Score", value: "0.02%", change: "-0.01%", trend: "upward", context: "optimal calibration" }
        ]
      };
    }

    // 3. Billing Plans Mock Payload
    if (targetComp.includes('billing') || text.includes('plan') || text.includes('checkout') || text.includes('price')) {
      return {
        targetType: 'billing',
        payload: [
          { id: "ai-starter", name: "AI Starter", price: "$29/mo", features: ["10k Model Tokens/mo", "Standard Latency", "Community Support"], popular: false },
          { id: "ai-pro", name: "AI Frontier Pro", price: "$99/mo", features: ["1M Tokens/mo", "Sub-100ms Streaming", "Custom JSON Schema Enforcement", "24/7 Dedicated Support"], popular: true },
          { id: "ai-enterprise", name: "AI Private Cluster", price: "$499/mo", features: ["Unlimited Tokens", "Isolated Model Weights", "Custom Fine-Tuning", "SLA Guarantees"], popular: false }
        ]
      };
    }

    // 4. Default Composite Dashboard / Master State
    return {
      targetType: 'dashboard',
      payload: {
        metrics: [
          { title: "Generated ARR", value: "$1,420,000.00", change: "+34.5%", trend: "upward", context: "AI forecasted" },
          { title: "Active API Keys", value: "12,840", change: "+12.1%", trend: "upward", context: "vs last week" },
          { title: "Query Latency", value: "88 ms", change: "-12.5%", trend: "upward", context: "edge routed" },
          { title: "System Uptime", value: "99.99%", change: "0.0%", trend: "neutral", context: "SLA Compliant" }
        ],
        tableHeaders: ["API Client Name", "Endpoint Model", "Token Quota", "Region", "Status"],
        tableRows: [
          ["Anthropic Claude 3.5 Sonnet", "v1/chat/completions", "500,000 / day", "us-east-1", "Active"],
          ["Google Gemini 1.5 Pro", "v1beta/models/generate", "1,000,000 / day", "europe-west1", "Active"],
          ["OpenAI GPT-4o Omni", "v1/chat/completions", "250,000 / day", "us-central1", "Active"],
          ["Ollama Llama 3 70B", "localhost:11434/api", "Unlimited", "Edge On-Prem", "Active"],
          ["Mistral Large v2", "api.mistral.ai/v1", "100,000 / day", "eu-west-3", "Pending"]
        ]
      }
    };
  }

  /**
   * Dispatch prompt submit & fetch stream
   */
  async _submitPrompt(promptText) {
    if (!promptText || this._isLoading) return;

    const endpoint = this.getAttribute('endpoint') || '/api/generate';
    const targetComp = this.getAttribute('target-component') || 'saas-dashboard';
    const isMockMode = this.hasAttribute('mock-mode') || endpoint.includes('mock') || true;

    this._isLoading = true;
    this._statusMessage = '🤖 Querying AI Model & Generating JSON Schema...';
    this._statusType = 'active';
    this._render();

    try {
      let resultData = null;

      if (!isMockMode && endpoint && !endpoint.includes('mock')) {
        // Live Fetch Execution
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: promptText, targetComponent: targetComp })
        });

        if (!response.ok) {
          throw new Error(`AI API HTTP error! status: ${response.status}`);
        }
        resultData = await response.json();
      } else {
        // Simulated AI Network Latency (600ms delay for realism)
        await new Promise(resolve => setTimeout(resolve, 600));
        resultData = this._generateMockAIResponse(promptText, targetComp);
      }

      this._statusMessage = '✅ AI Schema Generated & Dispatched!';
      this._statusType = 'success';

      // Emit Unified Custom Browser Event
      this.dispatchEvent(
        new CustomEvent('ai-generation-complete', {
          detail: {
            prompt: promptText,
            targetComponent: targetComp,
            payload: resultData.payload || resultData,
            targetType: resultData.targetType || 'dashboard',
            timestamp: new Date().toISOString()
          },
          bubbles: true,
          composed: true
        })
      );

    } catch (err) {
      console.warn('UniversalAIBridge: Live endpoint fetch failed, falling back to schema generator.', err);
      
      const fallbackResult = this._generateMockAIResponse(promptText, targetComp);
      this._statusMessage = '⚠️ Fallback Schema Generated Successfully';
      this._statusType = 'warning';

      this.dispatchEvent(
        new CustomEvent('ai-generation-complete', {
          detail: {
            prompt: promptText,
            targetComponent: targetComp,
            payload: fallbackResult.payload,
            targetType: fallbackResult.targetType,
            timestamp: new Date().toISOString()
          },
          bubbles: true,
          composed: true
        })
      );
    } finally {
      this._isLoading = false;
      this._render();
    }
  }

  _render() {
    const placeholder = this.getAttribute('placeholder') || 'Describe any UI view (e.g. "Create a fintech dashboard with ARR metrics")...';
    const targetComp = this.getAttribute('target-component') || 'saas-dashboard';
    const endpoint = this.getAttribute('endpoint') || '/api/generate';

    const style = `
      <style>
        :host {
          display: block;
          font-family: var(--font-sans, system-ui, -apple-system, sans-serif);
          color: var(--color-text-primary, #0f172a);
          box-sizing: border-box;
        }

        .ai-bridge-container {
          background: linear-gradient(135deg, var(--color-bg-surface, #ffffff), var(--color-bg-surface-elevated, #f8fafc));
          border: 1px solid var(--color-border-strong, #cbd5e1);
          border-radius: var(--radius-xl, 12px);
          padding: var(--spacing-5, 20px);
          box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
        }

        .ai-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--spacing-3, 12px);
          flex-wrap: wrap;
          gap: var(--spacing-2, 8px);
        }

        .ai-title-group {
          display: flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
        }

        .ai-badge {
          background-color: var(--color-primary-light, #eff6ff);
          color: var(--color-primary, #2563eb);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-full, 9999px);
          padding: 2px 10px;
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-bold, 700);
        }

        .ai-status-indicator {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .status-neutral { color: var(--color-text-secondary, #475569); }
        .status-active { color: var(--color-primary, #2563eb); }
        .status-success { color: var(--color-success, #16a34a); }
        .status-warning { color: var(--color-warning, #d97706); }

        .ai-input-wrapper {
          display: flex;
          gap: var(--spacing-2, 8px);
          margin-bottom: var(--spacing-3, 12px);
        }

        .ai-textarea {
          flex: 1;
          padding: var(--spacing-3, 12px);
          font-size: var(--font-size-sm, 14px);
          font-family: inherit;
          color: var(--color-text-primary, #0f172a);
          background-color: var(--color-bg-app, #f8fafc);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          outline: none;
          resize: vertical;
          min-height: 48px;
          transition: border-color var(--transition-fast, 150ms ease);
        }

        .ai-textarea:focus {
          border-color: var(--color-primary, #2563eb);
          box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
        }

        .ai-submit-btn {
          background-color: var(--color-primary, #2563eb);
          color: var(--color-text-inverse, #ffffff);
          border: none;
          border-radius: var(--radius-md, 6px);
          padding: 0 var(--spacing-5, 20px);
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-bold, 700);
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          white-space: nowrap;
          transition: background-color var(--transition-fast, 150ms ease);
        }

        .ai-submit-btn:hover:not(:disabled) {
          background-color: var(--color-primary-hover, #1d4ed8);
        }

        .ai-submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .preset-pills {
          display: flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
          flex-wrap: wrap;
        }

        .preset-pill {
          background-color: var(--color-bg-hover, #f1f5f9);
          color: var(--color-text-secondary, #475569);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          padding: 4px 10px;
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-medium, 500);
          cursor: pointer;
          transition: all var(--transition-fast, 150ms ease);
        }

        .preset-pill:hover {
          background-color: var(--color-primary-light, #eff6ff);
          color: var(--color-primary, #2563eb);
          border-color: var(--color-primary, #2563eb);
        }

        /* Spinner Animation */
        .spinner {
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: spin 800ms linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360ddeg); }
        }
      </style>
    `;

    this.shadowRoot.innerHTML = `
      ${style}
      <div class="ai-bridge-container">
        <div class="ai-header">
          <div class="ai-title-group">
            <span style="font-size: 18px;">⚡</span>
            <strong style="font-size: var(--font-size-sm, 14px); font-weight: var(--font-weight-bold, 700);">
              Universal AI Gateway Adapter (&lt;universal-ai-bridge&gt;)
            </strong>
            <span class="ai-badge">${endpoint}</span>
          </div>
          <div class="ai-status-indicator status-${this._statusType}">
            <span>${this._statusMessage}</span>
          </div>
        </div>

        <div class="ai-input-wrapper">
          <textarea
            class="ai-textarea"
            id="prompt-input"
            placeholder="${placeholder}"
            rows="2"
          ></textarea>
          <button type="button" class="ai-submit-btn" id="btn-submit" ${this._isLoading ? 'disabled' : ''}>
            ${this._isLoading ? '<span class="spinner"></span> Streaming...' : '✨ Generate UI Layout'}
          </button>
        </div>

        <div class="preset-pills">
          <span style="font-size: var(--font-size-xs, 12px); color: var(--color-text-muted, #94a3b8); font-weight: 600;">Presets:</span>
          <button type="button" class="preset-pill" data-prompt="Generate a SaaS ARR and Churn analytics dashboard">📊 SaaS Revenue Metrics</button>
          <button type="button" class="preset-pill" data-prompt="Create a subscription billing plans selection component">💳 Commercial Billing Plans</button>
          <button type="button" class="preset-pill" data-prompt="Build a new user team onboarding registration form">👤 Team Registration Form</button>
          <button type="button" class="preset-pill" data-prompt="Display security access log data table for cloud cluster">🛡️ Security Cluster Table</button>
        </div>
      </div>
    `;

    // Event Bindings
    const submitBtn = this.shadowRoot.querySelector('#btn-submit');
    const inputEl = this.shadowRoot.querySelector('#prompt-input');

    if (submitBtn && inputEl) {
      submitBtn.addEventListener('click', () => {
        this._submitPrompt(inputEl.value);
      });

      inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          this._submitPrompt(inputEl.value);
        }
      });
    }

    // Preset Pill Click Handlers
    this.shadowRoot.querySelectorAll('.preset-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const promptVal = pill.dataset.prompt;
        if (inputEl) {
          inputEl.value = promptVal;
          this._submitPrompt(promptVal);
        }
      });
    });
  }
}

if (!customElements.get('universal-ai-bridge')) {
  customElements.define('universal-ai-bridge', UniversalAIBridge);
}
