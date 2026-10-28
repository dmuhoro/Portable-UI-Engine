# Sprint 31 — Self-Serve 14-Day Trial Engines, Interactive Configuration Onboarding Wizard, Subscription Activation Checkouts, and Production Distribution Seals

**Theme:** High-converting self-serve commercial funnel: automated 14-day free trial lifecycle
management with graceful payment overlays, interactive step-by-step clinic configuration
onboarding, multi-provider B2B subscription checkout routing with instant tier activation,
and privacy-focused product milestone telemetry for trial conversion health monitoring.

## Pillars

### 1. 14-Day Free Trial Management & Lifecycle Automations
- `src/lib/trials.server.ts` — Full trial lifecycle engine:
  - `TRIAL_DURATION_DAYS = 14` — Constant for trial window.
  - `getTrialStatus(orgId)` — Evaluates org trial state: active, expiring, expired, or converted. Returns daysRemaining, isTrialActive, isExpired.
  - `startTrial(orgId)` — Applies 14-day window from now, sets subscription_status to 'trialing', records audit + SSE event.
  - `evaluateTrialAccess(orgId)` — Pre-flight check that returns `{ showPaywall, blockAccess, message }`:
    - Active subscription without trial → full access.
    - Active trial with >3 days → full access.
    - Active trial with ≤3 days → access with upgrade nudge message.
    - Expired trial → paywall + block + "trial has ended" message.
    - Converted trial → full access.
    - Suspended → paywall + block + "account suspended" message.
  - `convertTrial(orgId, targetTier)` — Marks trial as converted, sets subscription_status to 'active', records audit + SSE event.
  - `getTrialsExpiringSoon(withinDays)` — Dashboard query for orgs whose trials expire within N days.
- Patient historical records are preserved when a trial lapses — only new access is gated.

### 2. Interactive Clinic Configuration Onboarding Wizard
- `src/components/OnboardingWizard.tsx` — Multi-step configuration wizard:
  - **Step 1 — Clinic Info:** Clinic name (required), base currency selector (KES/USD/GBP/EUR/UGX/TZS/NGN/ZAR), timezone picker, notification email.
  - **Step 2 — WhatsApp Integration:** Toggle enable/disable, Evolution API/Baileys instance ID input.
  - **Step 3 — Practitioner Schedules:** Dynamic add/remove practitioners with name, specialty (12 medical specialties), and schedule presets (Mon-Fri 8am-5pm, Mon-Sat 8am-5pm, etc.).
  - **Step 4 — Review & Confirm:** Full configuration summary before submission.
  - `StepIndicator` — Visual step progress with check marks for completed steps.
  - All configuration data collected in a single `OnboardingConfig` object and applied to tenant config on completion.
  - Exported constants: `CURRENCIES`, `TIMEZONES`, `SPECIALTIES`, `SCHEDULE_PRESETS`, `DEFAULT_CONFIG`.

### 3. Multi-Provider B2B Subscription Checkout Router
- `src/lib/checkout.server.ts` — Subscription checkout lifecycle:
  - `initiateCheckout(orgId, targetTier, provider)` — Creates checkout session with concurrent lock, generates unique `chk_` prefixed session ID and `pay_` payment reference. Prevents duplicate pending sessions for same org + tier. Returns checkout URL + session details.
  - `processWebhookReceipt(receipt)` — Maps external payment provider references to checkout sessions:
    - Success → marks session 'completed', activates tier on org, records audit + SSE event.
    - Failure → marks session 'failed' with raw payload metadata.
    - Already completed → idempotent skip.
    - Unknown ref → logs warning.
  - `activateTier(orgId, targetTier)` — Direct tier activation with `FOR UPDATE` lock, records previous tier for audit trail.
  - `getCheckoutSession(orgId, sessionId)` — Session detail retrieval.
  - `getCheckoutHistory(orgId, limit)` — Paginated checkout history.
- **DB Schema** — `checkout_sessions` table with columns: id (VARCHAR PK), organization_id, target_tier, payment_provider (mpesa/card/bank_transfer), amount_kes, status (pending/processing/completed/failed/expired), external_ref, metadata (JSONB), expires_at, completed_at.

### 4. In-App Operational Metric Event Telemetry
- `src/lib/telemetry.server.ts` — Privacy-focused product adoption tracking:
  - `trackUserMilestone(orgId, milestoneKey, metadata)` — Idempotent milestone recording with ON CONFLICT DO NOTHING. Returns `{ tracked, isNew }`. Fires SSE event on new milestones.
  - `hasMilestone(orgId, milestoneKey)` — Quick boolean check for milestone existence.
  - `getOrgMilestones(orgId)` — Full milestone timeline for an org.
  - `getMilestoneStats()` — Aggregate dashboard: total orgs, orgs with milestones, milestone counts by key, activation rate (onboarding completion %).
  - `listMilestones()` / `getMilestoneDefinition(key)` — Milestone registry introspection.
- **13 Milestone Definitions** across 4 categories:
  - **Activation:** FIRST_LEAD_CREATED, FIRST_CSV_IMPORTED, FIRST_WEBHOOK_CONFIGURED, ONBOARDING_COMPLETED
  - **Engagement:** FIRST_APPOINTMENT_BOOKED, FIRST_WHATSAPP_SENT, LEAD_PIPELINE_ACTIVE, FIRST_EXPORT_GENERATED, MULTI_PROVIDER_SCHEDULED
  - **Revenue:** FIRST_INVOICE_ISSUED, FIRST_PAYMENT_RECEIVED, SUBSCRIPTION_CONVERTED
  - **Retention:** STREAK_7_DAYS
- **DB Schema** — `product_milestones` table with columns: organization_id, user_id, milestone_key (UNIQUE per org), milestone_label, metadata (JSONB).

## Test Coverage

| File | Tests |
|---|---|
| `trials.test.ts` | 16 — Status retrieval (active/expired/converted/not-found), trial start, access evaluation (full access/paywall/expiring warning/suspended), conversion, expiring-soon query, duration constant |
| `checkout.test.ts` | 14 — Session creation, duplicate prevention, tier pricing, invalid tier, webhook success/failure/duplicate/unknown, direct activation, session retrieval, history |
| `telemetry.test.ts` | 19 — First-time tracking, duplicate idempotency, unknown keys, DB unavailable, milestone definitions, hasMilestone, org milestones, stats, category validation |
| `onboarding-wizard.test.ts` | 7 — Default config, currency options, specialties, schedule presets, timezones, config validation |

**Total:** 466 tests across 48 files — all passing.

## Database Changes

```sql
-- Trial columns on organizations
ALTER TABLE organizations ADD COLUMN trial_started_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN trial_ends_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN trial_converted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN onboarding_completed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN onboarding_config JSONB DEFAULT '{}';

-- Product milestones
CREATE TABLE product_milestones (
  id SERIAL PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id),
  milestone_key VARCHAR(60) NOT NULL,
  milestone_label VARCHAR(120) NOT NULL DEFAULT '',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(organization_id, milestone_key)
);

-- Checkout sessions
CREATE TABLE checkout_sessions (
  id VARCHAR(80) PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  target_tier VARCHAR(20) NOT NULL,
  payment_provider VARCHAR(20) NOT NULL CHECK (payment_provider IN ('mpesa', 'card', 'bank_transfer')),
  amount_kes INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  external_ref VARCHAR(100),
  metadata JSONB DEFAULT '{}',
  expires_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Key Architectural Decisions

1. **Graceful trial expiration:** When a trial lapses, patient historical records remain fully accessible. The paywall only gates new feature access — no data loss, no panic.

2. **Idempotent webhook processing:** `processWebhookReceipt` uses external_ref as a natural idempotency key. Completed checkouts are skipped on re-delivery, preventing double-activation from payment provider retries.

3. **Milestone idempotency via UNIQUE constraint:** `trackUserMilestone` uses `ON CONFLICT DO NOTHING` at the database level, making concurrent/duplicate calls safe without application-level locking.

4. **Wizard as pure config collector:** The `OnboardingWizard` component collects all configuration in a single `OnboardingConfig` object and hands it to the parent `onComplete` callback. No network calls during the wizard flow — the parent applies the config in one atomic step.

5. **Checkout session TTL:** Sessions expire after 30 minutes to prevent stale pending sessions from blocking new checkout attempts for the same tier.
