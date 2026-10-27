# Daftari evidence — L10 Second Brain: DataBank vault corridor (2026-09-08)

Second Brain = personal+business knowledge module wired to the tailnet DataBank
vault. This is the Daftari half of L10; the transport half (opt-in CORS) landed
in the DataBank repo as v0.6.2 / commit `deab14d` (154 tests OK, SSH-signed `G`,
pushed). This corpus follows the On-Device Privacy Invariant: no file is sent to
a third-party service; the vault is the Owner's own tailnet host.

## Guardrails (fail-closed, never false confidence)

- **The vault is a raw-HTTP path, the only one in Daftari.** Everything else
  routes through supabase-js. The client is strict: no configured URL+token ⇒
  `Err(VAULT_NOT_CONFIGURED)` **before** any fetch; blank text is refused before
  any fetch; a 401/403 ⇒ `VAULT_AUTH_FAILED`, network failure ⇒
  `VAULT_UNREACHABLE`. Nothing is swallowed into a generic error.
- **Browser mixed-content reality is documented honestly**: a production https
  origin cannot `fetch` a plain-`http://` tailnet host. The working on-device
  corridor is locally-served Daftari (`http://localhost:5173`) → vault with
  `--cors-origin`; the vault stays CORS-closed by default until the Owner opts in.
- **CORS only as broad as needed at the vault**: `Access-Control-Allow-Origin`
  is emitted only when the Owner passes `--cors-origin` (DataBank `deab14d`);
  methods GET/PUT/POST/OPTIONS, headers Authorization/Content-Type.

## Proof — gates run at HEAD after the change

| Gate | Command | Observed |
|---|---|---|
| typecheck | `npm run typecheck` | clean (tsc, tsconfig.app.json) |
| lint | `npm run lint` | clean (eslint .) |
| i18n parity | `npm run check:i18n` | "244 keys in use, 244 in sw.json, 244 in en.json" PASS |
| unit tests | `npm run test:run` | 39 files, **411 tested passed** |
| production build | `npm run build` | vite build success + PWA `generateSW`, 50 precache entries |

## Proof — new tests pin the protection, not the happy path

- `src/lib/dataBankClient.test.ts` (7 tests, mocked `fetch`):
  1. refuses to PUT a blank thought before any `fetch` (`expect(fetch).not.toHaveBeenCalled()`);
  2. refuses an unauthenticated write (blank token ⇒ `VAULT_NOT_CONFIGURED`, no `fetch`);
  3. PUT round-trip: URL `/vault/records`, `PUT`, `Authorization: Bearer tok`, body
     unwraps to `data.record`;
  4. 401 ⇒ `VAULT_AUTH_FAILED` (never masked);
  5. network rejection ⇒ `VAULT_UNREACHABLE`;
  6. `/vault/query` builds `q`, `thread`, `max`;
  7. `/healthz` + `/vault/threads` round-trip.
- `src/screens/SecondBrainScreen.test.tsx` (2 tests):
  1. **fail-closed gate**: empty config renders the "not configured" notice and
     `fetch` is never called (`expect(fetchMock).not.toHaveBeenCalled()`);
  2. configured vault lists an entry fetched from `/vault/entries`.

## Honest status

Implemented and verified in-Daftari; **not yet exercised against a live vault**
— that needs the Owner to (a) run the DataBank vault with `--cors-origin
http://localhost:5173`, (b) open Daftari at `localhost:5173`, (c) set the vault
URL + token in Settings → DataBank Vault, (d) put + list a thought. Until then
the claim is "client + wiring proven under mock"; the real data path is a manual
Owner gate, exactly like the DataBank L7/L8/L9 corridor gates.