# ADR-009: WhatsApp Sharing via URL Scheme

## Status
Accepted

## Context
Users want to share receipts and daily summaries with customers or for their own records. WhatsApp is the dominant messaging platform in Kenya, with near-universal adoption among Daftari's target users.

## Decision
We will share content via WhatsApp's URL scheme (`https://wa.me/` and `https://api.whatsapp.com/send`) instead of:
- Native share API (requires more permissions, inconsistent UX on mobile browsers)
- Email (less immediate, lower engagement)
- SMS (character limits, no rich formatting)
- In-app PDF generation (heavy, complex)

The URL scheme approach:
- Works entirely within the browser — no native module required
- Pre-fills the message text so the user only needs to tap Send
- Allows optional phone number targeting for customer-specific receipts
- Works on both mobile and desktop WhatsApp Web

## Consequences
### Positive
- Zero additional dependencies
- Works in the PWA shell with no platform-specific code
- Low friction — user taps, WhatsApp opens with pre-filled message
- Formatting uses Markdown-style bold (`*text*`) which WhatsApp renders

### Negative
- Some mobile browsers may show a confirmation dialog before opening WhatsApp
- No delivery tracking or read receipts (not needed for this use case)
- Message length limited by URL length (~2048 chars in most browsers)

## Implementation
- `src/lib/whatsapp.ts` exports `shareViaWhatsApp(text, phone?)` and formatters
- Receipt component and Dashboard both call `shareViaWhatsApp` with formatted text
- Phone number parameter reserved for future customer-targeted sharing

## References
- WhatsApp URL scheme docs: https://faq.whatsapp.com/5913398998672938
