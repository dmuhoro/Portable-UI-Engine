/**
 * universal-billing-funnel.js
 * Portable UI Engine - Advanced Commercial Multi-Step Billing Funnel
 * Custom Element using Shadow DOM, step wizard state management, and custom event emissions.
 * Accepts JSON payload array of plans via 'plans' property/attribute.
 * Emits 'app-checkout-complete' CustomEvent on successful checkout completion.
 */

class UniversalBillingFunnel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    this._plans = [
      {
        id: "tier-basic",
        name: "Basic Core",
        price: "$19/mo",
        features: ["1 User", "Standard Analytics", "Community Support"],
        popular: false
      },
      {
        id: "tier-pro",
        name: "Growth Pro",
        price: "$49/mo",
        features: ["5 Users", "Deep Telemetry", "Priority Email Support", "Custom Dashboard Exports"],
        popular: true
      },
      {
        id: "tier-enterprise",
        name: "Enterprise Scale",
        price: "$199/mo",
        features: ["Unlimited Users", "Dedicated SLA", "Custom Integrations", "24/7 Phone & Slack Support"],
        popular: false
      }
    ];

    this._step = 1; // Step 1: Select Plan, Step 2: Payment Details, Step 3: Confirmation
    this._selectedPlanId = "tier-pro";
    this._completedTransaction = null;
  }

  static get observedAttributes() {
    return ['plans'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'plans' && oldValue !== newValue) {
      this._parseAndSetPlans(newValue);
    }
  }

  get plans() {
    return this._plans;
  }

  set plans(val) {
    this._parseAndSetPlans(val);
  }

  get selectedPlan() {
    return this._plans.find(p => p.id === this._selectedPlanId) || this._plans[0];
  }

  connectedCallback() {
    this.render();
    this._bindEvents();
  }

  _parseAndSetPlans(val) {
    let parsed = val;
    if (typeof val === 'string') {
      try {
        parsed = JSON.parse(val);
      } catch (e) {
        console.warn('UniversalBillingFunnel: Failed to parse plans JSON string.', e);
        parsed = [];
      }
    }
    if (Array.isArray(parsed) && parsed.length > 0) {
      this._plans = parsed;
      if (!this._plans.some(p => p.id === this._selectedPlanId)) {
        this._selectedPlanId = this._plans[0].id;
      }
      this.render();
      this._bindEvents();
    }
  }

  _bindEvents() {
    const shadow = this.shadowRoot;
    if (!shadow) return;

    // Plan Selection Cards
    shadow.querySelectorAll('.plan-card').forEach(card => {
      card.addEventListener('click', () => {
        const planId = card.dataset.planId;
        if (planId) {
          this._selectedPlanId = planId;
          this._updatePlanSelectionUI();
        }
      });
    });

    // Step 1 -> Step 2 Button
    const btnToStep2 = shadow.querySelector('#btn-to-step-2');
    btnToStep2?.addEventListener('click', () => {
      this._step = 2;
      this.render();
      this._bindEvents();
    });

    // Step 2 -> Step 1 Back Button
    const btnBackTo1 = shadow.querySelector('#btn-back-to-step-1');
    btnBackTo1?.addEventListener('click', () => {
      this._step = 1;
      this.render();
      this._bindEvents();
    });

    // Step 2 Form Submit (Checkout)
    const form = shadow.querySelector('#payment-form');
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this._handleCheckoutSubmit(form);
    });

    // Reset Flow Button
    const btnReset = shadow.querySelector('#btn-reset-flow');
    btnReset?.addEventListener('click', () => {
      this._step = 1;
      this._completedTransaction = null;
      this.render();
      this._bindEvents();
    });
  }

  _updatePlanSelectionUI() {
    const shadow = this.shadowRoot;
    shadow.querySelectorAll('.plan-card').forEach(card => {
      if (card.dataset.planId === this._selectedPlanId) {
        card.classList.add('selected');
        const btn = card.querySelector('.select-btn');
        if (btn) btn.textContent = 'Selected';
      } else {
        card.classList.remove('selected');
        const btn = card.querySelector('.select-btn');
        if (btn) btn.textContent = 'Select Plan';
      }
    });
  }

  _handleCheckoutSubmit(form) {
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const formData = new FormData(form);
    const paymentDetails = {
      cardholderName: formData.get('cardholderName') || '',
      cardNumberLast4: (formData.get('cardNumber') || '4242').toString().slice(-4),
      expDate: formData.get('expDate') || '',
      billingEmail: formData.get('billingEmail') || '',
      zipCode: formData.get('zipCode') || ''
    };

    const transactionId = 'TX-' + Math.random().toString(36).substring(2, 9).toUpperCase();
    const timestamp = new Date().toISOString();

    const checkoutPayload = {
      transactionId: transactionId,
      timestamp: timestamp,
      plan: this.selectedPlan,
      payment: paymentDetails
    };

    this._completedTransaction = checkoutPayload;
    this._step = 3;

    // Dispatch Custom Event
    this.dispatchEvent(
      new CustomEvent('app-checkout-complete', {
        detail: checkoutPayload,
        bubbles: true,
        composed: true
      })
    );

    this.render();
    this._bindEvents();
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

        .funnel-container {
          background-color: var(--color-bg-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 12px);
          box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.05));
          padding: var(--spacing-6, 24px);
          max-width: 900px;
          margin: 0 auto;
        }

        /* Wizard Header & Stepper */
        .stepper-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid var(--color-border, #e2e8f0);
          padding-bottom: var(--spacing-4, 16px);
          margin-bottom: var(--spacing-6, 24px);
        }

        .stepper-title {
          font-size: var(--font-size-lg, 18px);
          font-weight: var(--font-weight-bold, 700);
          margin: 0;
          color: var(--color-text-primary, #0f172a);
        }

        .stepper-steps {
          display: flex;
          align-items: center;
          gap: var(--spacing-3, 12px);
        }

        .step-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-bold, 600);
          border-radius: var(--radius-full, 9999px);
          background-color: var(--color-bg-app, #f8fafc);
          color: var(--color-text-muted, #94a3b8);
          border: 1px solid var(--color-border, #e2e8f0);
        }

        .step-pill.active {
          background-color: var(--color-primary-light, #eff6ff);
          color: var(--color-primary, #2563eb);
          border-color: var(--color-primary, #2563eb);
        }

        .step-pill.completed {
          background-color: var(--color-success-bg, #f0fdf4);
          color: var(--color-success, #16a34a);
          border-color: var(--color-success, #16a34a);
        }

        /* Step 1: Plans Grid Layout */
        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: var(--spacing-4, 16px);
          margin-bottom: var(--spacing-6, 24px);
        }

        .plan-card {
          background-color: var(--color-bg-surface, #ffffff);
          border: 2px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          padding: var(--spacing-5, 20px);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
          cursor: pointer;
          transition: all var(--transition-fast, 150ms ease);
        }

        .plan-card:hover {
          border-color: var(--color-primary, #2563eb);
          box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0,0,0,0.1));
        }

        .plan-card.selected {
          border-color: var(--color-primary, #2563eb);
          background-color: var(--color-primary-light, #eff6ff);
        }

        .popular-tag {
          position: absolute;
          top: -12px;
          right: 16px;
          background-color: var(--color-primary, #2563eb);
          color: #ffffff;
          font-size: 10px;
          font-weight: var(--font-weight-bold, 700);
          text-transform: uppercase;
          padding: 2px 8px;
          border-radius: var(--radius-full, 9999px);
          letter-spacing: 0.05em;
        }

        .plan-name {
          font-size: var(--font-size-base, 16px);
          font-weight: var(--font-weight-bold, 700);
          margin: 0 0 var(--spacing-1, 4px) 0;
          color: var(--color-text-primary, #0f172a);
        }

        .plan-price {
          font-size: var(--font-size-2xl, 24px);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-primary, #2563eb);
          margin-bottom: var(--spacing-4, 16px);
        }

        .feature-list {
          list-style: none;
          padding: 0;
          margin: 0 0 var(--spacing-4, 16px) 0;
          display: flex;
          flex-direction: column;
          gap: var(--spacing-2, 8px);
        }

        .feature-item {
          font-size: var(--font-size-xs, 12px);
          color: var(--color-text-secondary, #475569);
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .feature-item::before {
          content: "✓";
          color: var(--color-success, #16a34a);
          font-weight: bold;
        }

        .select-btn {
          width: 100%;
          padding: var(--spacing-2, 8px);
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          border-radius: var(--radius-md, 6px);
          border: 1px solid var(--color-border-strong, #cbd5e1);
          background-color: var(--color-bg-surface, #ffffff);
          color: var(--color-text-primary, #0f172a);
          cursor: pointer;
          transition: all var(--transition-fast, 150ms ease);
          text-align: center;
        }

        .plan-card.selected .select-btn {
          background-color: var(--color-primary, #2563eb);
          color: #ffffff;
          border-color: var(--color-primary, #2563eb);
        }

        /* Step 2: Payment Form & Order Summary Split */
        .checkout-split {
          display: grid;
          grid-template-columns: 1fr 280px;
          gap: var(--spacing-6, 24px);
        }

        @media (max-width: 768px) {
          .checkout-split {
            grid-template-columns: 1fr;
          }
        }

        .form-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--spacing-3, 12px);
        }

        .form-grid-full {
          grid-column: 1 / -1;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .form-label {
          font-size: var(--font-size-xs, 12px);
          font-weight: var(--font-weight-semibold, 600);
          color: var(--color-text-secondary, #475569);
          text-transform: uppercase;
        }

        .form-input {
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
          transition: all var(--transition-fast, 150ms ease);
        }

        .form-input:focus {
          border-color: var(--color-primary, #2563eb);
          background-color: var(--color-bg-surface, #ffffff);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }

        .summary-card {
          background-color: var(--color-bg-app, #f8fafc);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-lg, 8px);
          padding: var(--spacing-4, 16px);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-3, 12px);
        }

        .summary-row {
          display: flex;
          justify-content: space-between;
          font-size: var(--font-size-sm, 14px);
          color: var(--color-text-secondary, #475569);
        }

        .summary-row.total {
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-text-primary, #0f172a);
          border-top: 1px solid var(--color-border, #e2e8f0);
          padding-top: var(--spacing-2, 8px);
          font-size: var(--font-size-base, 16px);
        }

        /* Action Buttons Bar */
        .actions-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: var(--spacing-6, 24px);
          padding-top: var(--spacing-4, 16px);
          border-top: 1px solid var(--color-border, #e2e8f0);
        }

        .btn {
          display: inline-flex;
          align-items: center;
          gap: var(--spacing-2, 8px);
          padding: var(--spacing-2, 8px) var(--spacing-5, 20px);
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-semibold, 600);
          border-radius: var(--radius-md, 6px);
          border: 1px solid var(--color-border-strong, #cbd5e1);
          background-color: var(--color-bg-surface, #ffffff);
          color: var(--color-text-primary, #0f172a);
          cursor: pointer;
          transition: all var(--transition-fast, 150ms ease);
        }

        .btn:hover {
          background-color: var(--color-bg-hover, #f1f5f9);
        }

        .btn-primary {
          background-color: var(--color-primary, #2563eb);
          color: #ffffff;
          border-color: var(--color-primary, #2563eb);
        }

        .btn-primary:hover {
          background-color: var(--color-primary-hover, #1d4ed8);
        }

        /* Step 3: Success Confirmation Screen */
        .success-box {
          text-align: center;
          padding: var(--spacing-8, 32px) var(--spacing-4, 16px);
        }

        .success-icon {
          width: 56px;
          height: 56px;
          background-color: var(--color-success-bg, #f0fdf4);
          color: var(--color-success, #16a34a);
          border-radius: var(--radius-full, 9999px);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
          margin-bottom: var(--spacing-4, 16px);
          border: 2px solid var(--color-success, #16a34a);
        }

        .success-title {
          font-size: var(--font-size-xl, 20px);
          font-weight: var(--font-weight-bold, 700);
          margin: 0 0 var(--spacing-2, 8px) 0;
          color: var(--color-text-primary, #0f172a);
        }

        .success-desc {
          font-size: var(--font-size-sm, 14px);
          color: var(--color-text-secondary, #475569);
          margin: 0 0 var(--spacing-6, 24px) 0;
        }

        .tx-details {
          background-color: var(--color-bg-app, #f8fafc);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: var(--radius-md, 6px);
          padding: var(--spacing-4, 16px);
          text-align: left;
          max-width: 480px;
          margin: 0 auto var(--spacing-6, 24px) auto;
          font-size: var(--font-size-xs, 12px);
          font-family: var(--font-mono, monospace);
        }

        .tx-row {
          display: flex;
          justify-content: space-between;
          padding: 4px 0;
        }
      </style>

      <div class="funnel-container">
        <!-- Stepper Navigation Header -->
        <div class="stepper-header">
          <h2 class="stepper-title">Commercial Billing Setup</h2>
          <div class="stepper-steps">
            <span class="step-pill ${this._step === 1 ? 'active' : this._step > 1 ? 'completed' : ''}">
              1. Select Plan
            </span>
            <span class="step-pill ${this._step === 2 ? 'active' : this._step > 2 ? 'completed' : ''}">
              2. Payment & Checkout
            </span>
            <span class="step-pill ${this._step === 3 ? 'completed' : ''}">
              3. Confirmation
            </span>
          </div>
        </div>

        ${this._renderStepContent()}
      </div>
    `;
  }

  _renderStepContent() {
    if (this._step === 1) {
      return `
        <!-- STEP 1: Select Plan -->
        <div class="plans-grid">
          ${this._plans.map(p => `
            <div class="plan-card ${p.id === this._selectedPlanId ? 'selected' : ''}" data-plan-id="${this._escapeHtml(p.id)}">
              ${p.popular ? '<span class="popular-tag">Most Popular</span>' : ''}
              <div>
                <h3 class="plan-name">${this._escapeHtml(p.name)}</h3>
                <div class="plan-price">${this._escapeHtml(p.price)}</div>
                <ul class="feature-list">
                  ${(p.features || []).map(f => `<li class="feature-item">${this._escapeHtml(f)}</li>`).join('')}
                </ul>
              </div>
              <button type="button" class="select-btn">
                ${p.id === this._selectedPlanId ? 'Selected' : 'Select Plan'}
              </button>
            </div>
          `).join('')}
        </div>

        <div class="actions-bar" style="justify-content: flex-end;">
          <button type="button" class="btn btn-primary" id="btn-to-step-2">
            Continue to Payment &rarr;
          </button>
        </div>
      `;
    }

    if (this._step === 2) {
      const plan = this.selectedPlan;
      return `
        <!-- STEP 2: Payment Details & Order Summary -->
        <form id="payment-form">
          <div class="checkout-split">
            
            <!-- Left: Payment Form Fields -->
            <div class="form-grid">
              <div class="form-group form-grid-full">
                <label class="form-label" for="cardholderName">Cardholder Name *</label>
                <input
                  type="text"
                  id="cardholderName"
                  name="cardholderName"
                  required
                  placeholder="e.g. Alex Morgan"
                  class="form-input"
                  value="Alex Morgan"
                />
              </div>

              <div class="form-group form-grid-full">
                <label class="form-label" for="billingEmail">Billing Email *</label>
                <input
                  type="email"
                  id="billingEmail"
                  name="billingEmail"
                  required
                  placeholder="alex@corp.internal"
                  class="form-input"
                  value="alex@corp.internal"
                />
              </div>

              <div class="form-group form-grid-full">
                <label class="form-label" for="cardNumber">Card Number *</label>
                <input
                  type="text"
                  id="cardNumber"
                  name="cardNumber"
                  required
                  pattern="[0-9\\s]{13,19}"
                  placeholder="4242 4242 4242 4242"
                  class="form-input"
                  value="4242 4242 4242 4242"
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="expDate">Exp. Date *</label>
                <input
                  type="text"
                  id="expDate"
                  name="expDate"
                  required
                  placeholder="MM/YY"
                  class="form-input"
                  value="12/28"
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="cvc">CVC / Zip *</label>
                <input
                  type="text"
                  id="zipCode"
                  name="zipCode"
                  required
                  placeholder="12345"
                  class="form-input"
                  value="90210"
                />
              </div>
            </div>

            <!-- Right: Order Summary Card -->
            <div class="summary-card">
              <h4 style="margin: 0; font-size: var(--font-size-base); font-weight: bold;">Order Summary</h4>
              <div class="summary-row">
                <span>Selected Plan:</span>
                <strong>${this._escapeHtml(plan.name)}</strong>
              </div>
              <div class="summary-row">
                <span>Billing Interval:</span>
                <span>Monthly</span>
              </div>
              <div class="summary-row">
                <span>Subtotal:</span>
                <span>${this._escapeHtml(plan.price)}</span>
              </div>
              <div class="summary-row">
                <span>Tax:</span>
                <span>$0.00</span>
              </div>
              <div class="summary-row total">
                <span>Total Due Now:</span>
                <span>${this._escapeHtml(plan.price)}</span>
              </div>
            </div>

          </div>

          <div class="actions-bar">
            <button type="button" class="btn" id="btn-back-to-step-1">
              &larr; Change Plan
            </button>
            <button type="submit" class="btn btn-primary">
              🔒 Complete Purchase (${this._escapeHtml(plan.price)})
            </button>
          </div>
        </form>
      `;
    }

    if (this._step === 3 && this._completedTransaction) {
      const tx = this._completedTransaction;
      return `
        <!-- STEP 3: Transaction Confirmation -->
        <div class="success-box">
          <div class="success-icon">✓</div>
          <h3 class="success-title">Subscription Activated!</h3>
          <p class="success-desc">
            Your billing details were validated and the subscription was successfully processed.
          </p>

          <div class="tx-details">
            <div class="tx-row">
              <span style="color: var(--color-text-muted);">Transaction ID:</span>
              <strong>${this._escapeHtml(tx.transactionId)}</strong>
            </div>
            <div class="tx-row">
              <span style="color: var(--color-text-muted);">Activated Plan:</span>
              <span>${this._escapeHtml(tx.plan.name)} (${this._escapeHtml(tx.plan.price)})</span>
            </div>
            <div class="tx-row">
              <span style="color: var(--color-text-muted);">Cardholder:</span>
              <span>${this._escapeHtml(tx.payment.cardholderName)} (*${this._escapeHtml(tx.payment.cardNumberLast4)})</span>
            </div>
            <div class="tx-row">
              <span style="color: var(--color-text-muted);">Timestamp:</span>
              <span>${this._escapeHtml(tx.timestamp)}</span>
            </div>
          </div>

          <button type="button" class="btn" id="btn-reset-flow">
            🔄 Restart Billing Wizard
          </button>
        </div>
      `;
    }

    return '';
  }
}

if (!customElements.get('universal-billing-funnel')) {
  customElements.define('universal-billing-funnel', UniversalBillingFunnel);
}
