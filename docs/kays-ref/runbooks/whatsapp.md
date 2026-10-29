# Runbook: WhatsApp Delivery

> How to verify and operate WhatsApp Cloud API outbound messaging.

## Env Required

| Variable | Purpose | Where to get it |
|----------|---------|-----------------|
| `WHATSAPP_TOKEN` | Cloud API **access token** (system-user token) | Meta Developer Portal → WhatsApp app → API Setup → "Access Token" (or create a System User → WhatsApp Connection → generate token) |
| `WHATSAPP_PHONE_NUMBER_ID` | Business phone number ID | Meta Developer Portal → WhatsApp app → API Setup → "Phone number ID" for +254703939236 |
| `WHATSAPP_VERIFY_TOKEN` | webhook verify token (default `kwc_webhook_2026`) | self-chosen string |
| `WHATSAPP_APP_SECRET` | webhook signature secret (HMAC `x-hub-signature-256`) | Meta app → App Settings → Basic → App Secret |
| `WHATSAPP_ACCESS_TOKEN` | used for media download (inbound) | same as `WHATSAPP_TOKEN` (long-lived) |

> **Which token to provide:** The two required values to unblock live delivery are
> **`WHATSAPP_TOKEN`** (the long-lived access token for the WhatsApp Business app) and
> **`WHATSAPP_PHONE_NUMBER_ID`** (the numeric ID of the +254703939236 business number).
> These are found in the Meta Developer Portal (developers.facebook.com) under the WhatsApp
> app → WhatsApp → API Setup. The app currently logs messages with `provider: "log"` when the
> token is unset — so the pilot can proceed without WhatsApp, but live delivery needs the token.

## Send Path

`dispatch.server.ts:sendWhatsApp` → Graph API `POST https://graph.facebook.com/v18.0/{id}/messages`.
If `WHATSAPP_TOKEN` unset → message logged (`provider: "log"`), not dropped.

## Verify Live (test target +254703939236)

1. Submit a lead with the test phone from the admin UI (or public contact form).
2. Select preferred language EN or SW.
3. Confirm the confirmation message arrives on the phone.
4. Book an appointment → confirm reminder arrives.
5. Record result in `docs/evidence/`.

## Notes

- Bilingual templates live in `dispatch.server.ts:MESSAGE_TEMPLATES` (EN/SW).
- Swahili copy was LLM-authored — have a native speaker review before broad use (HEADSUP in file).
- Rate limit: 20 dispatches/org/60s.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Message never arrives | token/phone-id wrong | verify env + number active in WhatsApp Business |
| API returns error | number not opted-in / sandbox | use a number that has messaged the business |
| Logs show provider "log" | token missing | set `WHATSAPP_TOKEN` + phone id |