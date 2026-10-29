# Security Policy

## Threat Model

### Assets protected
- Transaction records (financial data of informal vendors)
- Business profile (name, location, payment methods)
- Auth credentials (email + password via Supabase)

### Threats mitigated
| Threat | Mitigation |
|---|---|
| Cross-user data access | Supabase RLS on all tables — owner_id = auth.uid() |
| SQL injection | Supabase parameterized queries (no raw SQL from client) |
| XSS via user input | React's JSX auto-escaping; no dangerouslySetInnerHTML |
| Session hijacking | Supabase JWT with short expiry; HTTPS only |
| Offline data exposure | IndexedDB is sandboxed per origin; encrypted on modern Android |
| PII in error logs | Logger never logs names, amounts, phone numbers |

### Out of scope (current version)
- Physical device theft (OS-level encryption responsibility)
- Safaricom M-Pesa security (external dependency)
- Supabase infrastructure security (vendor responsibility)

## Data Classification

| Data | Classification | Storage |
|---|---|---|
| Transaction amounts | Sensitive — financial | Dexie + Supabase (RLS) |
| Business name | Internal | Dexie + Supabase (RLS) |
| M-Pesa sender name | PII | Dexie + Supabase (RLS), never logged |
| M-Pesa transaction code | Internal | Dexie + Supabase |
| Auth email | PII | Supabase Auth only |
| Language preference | Non-sensitive | localStorage |

## Reporting a Vulnerability

Email: security@daftari.co.ke
Response SLA: 48 hours for acknowledgement, 7 days for assessment.

Do not open a public GitHub issue for security vulnerabilities.

## Supported Versions
Only the latest deployed version at daftari-amber.vercel.app is supported.
