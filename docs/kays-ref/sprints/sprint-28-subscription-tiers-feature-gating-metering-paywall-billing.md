# Sprint 28 — Multi-Tier Feature Gating, Usage Metering, Paywall UI, and Billing Dashboard

**Theme:** Monetisation infrastructure: define Starter/Growth/Enterprise subscription tiers with
feature maps and resource limits, add server-side and client-side feature gating, implement
real-time usage metering with quota checks, build paywall modal and quota banner components,
and create a self-serve billing/usage dashboard.

## Pillars

### 1. Subscription Tier Engine
- `src/lib/subscriptions.server.ts` — Defines three tiers with feature maps and resource limits:
  - **Starter** (KES 4,500/mo): 500 leads, 5 GB, 3 users, 5 providers, 1 location
  - **Growth** (KES 12,000/mo): 2,000 leads, 20 GB, 10 users, 20 providers, 1 location
  - **Enterprise** (KES 35,000/mo): 10,000 leads, 100 GB, 50 users, 100 providers, 10 locations
- `getOrgSubscription(orgId)` — Reads tier/status from `organizations` table, falls back to starter.
- `ensureFeatureAccess(featureId)` — Async guard that throws `TenantError` for suspended/past-due
  accounts or tier-restricted features. Structured logging on every denial.
- `checkFeatureAccessSync(tier, status, featureId)` — Synchronous check returning `{ allowed, reason }`.
- `hasFeature(tierId, featureId)` — Checks if a feature is in the tier's feature list.

### 2. Usage Metering & Quota Checking
- `src/lib/metering.server.ts` — Reads cached counters from `organizations` table:
  - `getUsageSnapshot(orgId)` — Returns leads/storage/users usage with percentage against tier limits.
  - `checkQuota(orgId, resource, additionalBytes?)` — Returns `{ withinQuota, used, limit }`.
  - `incrementLeadsUsed`, `decrementLeadsUsed`, `addStorageUsed` — Counter mutations.
  - `refreshUsageCounters(orgId)` — Recounts from source tables, updates cached counters.
  - `formatBytes(bytes)` — Human-readable B/KB/MB/GB formatting.
- `src/lib/db.server.ts` — Schema migration adds columns to `organizations`:
  `subscription_tier`, `subscription_status`, `subscription_expires_at`, `leads_used`,
  `storage_used_bytes`, `usage_refreshed_at`.

### 3. Subscription Route Guard & Paywall UI
- `src/components/SubscriptionGuard.tsx` — Client component that wraps content:
  - Fetches subscription status via `getSubscription()` server function.
  - Shows account-suspended or past-due banners when status is not active.
  - Compares feature against tier level; shows paywall overlay if insufficient.
  - Renders children if access is allowed.
- `src/components/PaywallModal.tsx` — Radix Dialog showing:
  - Current usage meters (leads, storage, users).
  - Three-column tier comparison with features and pricing.
  - "Contact Sales" CTA for upgrade tiers, "Your current plan" badge for current.
- `src/components/QuotaBanner.tsx` — Compact usage overview:
  - Progress bars for leads, storage, and users.
  - Amber warning at 80% threshold, red at 95%.
  - Hidden when all quotas are below threshold (unless `showAlways`).

### 4. Billing & License Audit Dashboard
- `src/routes/admin/settings/billing.tsx` — `/admin/settings/billing` route:
  - Current plan card (tier name, price, status badge, renewal date).
  - Usage meters with progress bars and percentage labels.
  - "Refresh" button to recount from source tables.
  - Tier comparison section (Starter/Growth/Enterprise) with feature lists and upgrade CTAs.
  - Follows existing admin settings page patterns (ErrorBoundary, Suspense, TanStack Query).

### 5. Server API Functions
- `src/lib/api/subscription.server.ts` — `createServerFn` wrappers:
  - `getSubscription()` — Returns tier, status, expiresAt, usage snapshot.
  - `getUsage()` — Returns usage snapshot only.
  - `checkLeadQuota()` / `checkStorageQuota()` — Quota checks for specific resources.
  - `refreshUsage()` — Recounts and returns updated usage.
  - `getAvailableTiers()` — Returns tier list with feature counts and limits.

## File Changes

| File | Change |
|------|--------|
| `src/lib/subscriptions.server.ts` | **New** — Tier definitions, feature maps, limits, `ensureFeatureAccess`, `checkFeatureAccessSync` |
| `src/lib/metering.server.ts` | **New** — Usage snapshot, quota checks, counter mutations, `refreshUsageCounters`, `formatBytes` |
| `src/lib/api/subscription.server.ts` | **New** — Server functions for subscription, usage, quota, tier listing |
| `src/components/SubscriptionGuard.tsx` | **New** — Client guard with paywall overlay |
| `src/components/PaywallModal.tsx` | **New** — Tier comparison modal with usage display |
| `src/components/QuotaBanner.tsx` | **New** — Usage progress bars with threshold warnings |
| `src/routes/admin/settings/billing.tsx` | **New** — License audit dashboard route |
| `src/lib/db.server.ts` | **Updated** — Subscription columns migration on `organizations` table |
| `src/routeTree.gen.ts` | **Updated** — Auto-generated route tree includes billing route |
| `src/__tests__/subscriptions.test.ts` | **New** — 37 tests for tier config, features, limits, `hasFeature`, `checkFeatureAccessSync` |
| `src/__tests__/metering.test.ts` | **New** — 15 tests for `formatBytes`, `formatUsage` |

## Results
- **302 tests** passing (up from 250, +52 new tests)
- **36 test files** passing (up from 34)
- Build: zero errors (only pre-existing `use client` warnings from deps)
