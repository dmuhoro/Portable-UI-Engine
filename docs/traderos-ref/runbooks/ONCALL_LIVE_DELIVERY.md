# On-Call Delivery — Operator Runbook (G-04: live PagerDuty/Slack)

**Purpose:** get a real incident delivered to a **managed on-call platform
account** (PagerDuty events/v2 or Slack incoming webhook) with live keys, so
the G-04 item "on-call providers are wired but no managed on-call platform
account with live keys has yet received a real incident" is closed.

## What is already proven

- `scripts/evidence/run_oncall_drill.py` (in the CI credential-free set) —
  severity routing + fail-closed delivery: INFO/WARNING/ERROR stay local,
  CRITICAL is POSTed on the wire; a non-2xx response raises `OnCallDeliveryError`
  (no silent drop). VERDICT 6/6.
- `tests/test_oncall_providers.py` — `PagerDutyTransport` and `SlackTransport`
  fire the **real** HTTP wire (loopback server) with the correct envelope:
  PagerDuty events/v2 payload (routing_key, event_action, payload severity) and
  Slack webhook payload, both with ack-verified delivery and fail-closed
  construction when keys are absent.
- The live on-call router is wired in `factory.py` from `PAGERDUTY_ROUTING_KEY`
  / `SLACK_WEBHOOK_URL` and refuses to construct without them (fail closed).

The transport mechanism is therefore proven on the wire. The remaining step is
pointing the same code at a **managed account with real keys** and observing a
real delivery.

## Operator steps

1. **Create the on-call accounts:**
   - PagerDuty: create a service + an events/v2 integration to get a
     `routing_key` (a 32-char integration key).
   - Slack: create an incoming-webhook app and copy its `https://hooks.slack.com/
     services/...` webhook URL.
2. **Set env on the deployed TraderOS service (Railway):**
   - `PAGERDUTY_ROUTING_KEY=<integration key>` (and optionally
     `PAGERDUTY_BASE_URL` for a proxy/federated endpoint).
   - `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`
   Either one alone is sufficient — the router is constructed per available
   provider, and both is fine.
3. **Deploy / restart** so the router picks up the keys. Verify via
   `/v1/orchestrator/status` that the on-call router reports the configured
   providers (delivered/failed counters present).
4. **Trigger one real CRITICAL incident** on the live path — the safe,
   repeatable option is a **kill-switch trip** (which is a genuine CRITICAL
   alert and exercises the real path):
   ```bash
   curl -XPOST -H "X-API-Key: $TRADEROS_ADMIN_API_KEY" \
       https://traderos-production.up.railway.app/v1/kill/engage
   # observe the PagerDuty incident + Slack message arrive
   curl -XPOST -H "X-API-Key: $TRADEROS_ADMIN_API_KEY" \
       https://traderos-production.up.railway.app/v1/kill/disengage
   ```
   Alternatively, run the governance/trigger-alerting drill with the real
   keys wired so it POSTs to the managed account.
5. **Confirm delivery + audit + metrics:**
   - The PagerDuty incident appears in the PagerDuty console (events/v2 ack).
   - The message appears in the Slack channel.
   - The audit trail records the alert, and the on-call delivered counter
     increments (`oncall.delivered`); a failed delivery increments
     `oncall.delivery_failed` and raises — never silent.
6. **Record evidence:** save the console/response output to
   `docs/evidence/<date>_oncall_live_delivery.log` and update the G-04 row.

## Acceptance (closes the G-04 open item)

- At least one managed provider (PagerDuty or Slack) received a real CRITICAL
  alert from the live deployment.
- Delivery was ack-verified (HTTP 2xx), audited, and counted.
- The `oncall_transport` CI drill and `test_oncall_providers.py` remain green
  (no regression).

## Fail-closed guarantees (unchanged)

- No `PAGERDUTY_ROUTING_KEY` / `SLACK_WEBHOOK_URL` → transport not constructed;
  on-call routing still works for any configured provider and refuses silently
  for the absent one.
- A non-2xx delivery raises `OnCallDeliveryError` and increments
  `oncall.delivery_failed` — a failed alert is never dropped silently.
- Severity routing: only CRITICAL (and configured escalation levels) fan out to
  the platform; INFO/WARNING/ERROR stay local.
