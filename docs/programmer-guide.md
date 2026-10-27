# Daftari — Programmer Guide

This guide is for the **programmer** extending Daftari. Read this before touching code. If you
operate the deployed instance, read `docs/operator-guide.md`; if you are a shop owner using the
app, read `docs/user-guide.md`.

These constraints come from the repo's own conventions and from build orders —
**the pipeline (typecheck → lint → i18n → test → build) is the law; a PR that is not green
everywhere does not merge.**

---

## 1. Architecture map

```
src/
├── App.tsx              Root: auth + onboarding + screen routing
├── main.tsx             Entry: Sentry init, React root, PWA
├── screens/             One file per full-page screen; tests sit beside them
├── components/          Reusable UI (AppShell, Receipt, banners, …)
├── features/            Feature modules — sms, sync, transactions, close, academy, marketing
│   └── sync/            syncQueue.ts (offline-first upload ledger)
├── lib/                 Core layer — store, db, repository, money, analytics, tsp
│   ├── db.ts            Dexie schema (single source of truth for tables)
│   ├── repository.ts    The ONLY data-access surface components may call
│   ├── store.ts         Zustand global store (persisted to localStorage)
│   ├── money.ts         All KES arithmetic goes through this module
│   └── constants.ts     Table names, storage keys, categories — no magic strings
├── i18n/                sw.json + en.json (must stay in key parity)
├── hooks/               useTranslation, useSync, …
└── test/                Test setup + global mocks
```

**Data flow:** UI → `src/lib/repository.ts` → Dexie (IndexedDB) → sync queue → Supabase.
Always offline-first: writes succeed locally; the queue reconciles to the cloud.

## 2. Non-negotiable conventions

| Rule | How |
|------|-----|
| `strict: true` | No `any`; use `unknown` + type guards |
| Branded IDs | `type BusinessId = string & { __brand: 'BusinessId' }` |
| Discriminated unions | Over `enum` |
| Money is integer cents | No raw `+ - * /` on KES — only `kesAdd`, `kesSubtract`, `kesSum`, `parseKESInput` from `src/lib/money.ts` |
| Repository pattern | Components never import Dexie directly; never use a table name outside `src/lib/constants.ts` |
| Global state | Zustand `useStore`; local state via React hooks; no prop drilling past 2 levels |
| Styling | Tailwind utility classes, `dark:` prefix, mobile-first |
| i18n | Every user-facing string via `useTranslation`; every key in **both** `sw.json` and `en.json` (default language Kiswahili) |
| No secrets | Real env values live in Vercel/Supabase only |

## 3. How to add a new screen (the standard step)

1. Create `src/screens/YourScreen.tsx`. Use the existing bilingual pattern
   (`language === 'sw' ? … : …`) or `t('key')` — never raw English-only strings.
2. For i18n keys: add the key to `src/i18n/en.json` **and** `src/i18n/sw.json`, then run
   `npx tsx scripts/check-i18n.ts`.
3. If the screen needs global navigation, register it as a `View` in
   `src/components/AppShell.tsx` (union type + `viewTitle` case) and wire its entry point in
   Settings or the shell.
4. Data access must go through `src/lib/repository.ts` (e.g. `getBusiness`, `saveTransaction`).
   Ignore any temptation to touch `db.ts` directly from a screen.
5. If you call the store, read via `useStore(selector)` for re-render correctness.
6. Add a behavior test in `src/screens/YourScreen.test.tsx` (Vitest + React Testing Library).
   Prefer asserting on user-visible outcomes, not internal state.

## 4. Changing the database schema (rare — do it right)

1. Update the Dexie schema in `src/lib/db.ts` **and** bump `DB.VERSION` in
   `src/lib/constants.ts`.
2. All existing rows must migrate — write the `upgrade()` path and test it with an old-version
   database instance.
3. `src/lib/repository.ts` is the only layer that should reference the schema — screens fetch
   via its typed helpers.

**Historical lesson (v6.7.0):** a prior WIP commit dropped `products?: string` from the
`Business` schema and replaced it with `categories`, breaking every `updateBusiness(…,
{ products: … })` call site and failing typecheck across screens. The correct fix was to
restore the original column. Revert column deletions; never "fix" callers by weakening types.

## 5. Money safety — the rules that protect real cash

- Amounts are stored as integer cents (`number`), computed only through `src/lib/money.ts`.
- Never introduce a raw arithmetic expression on `KES`; if a helper is missing, add it to
  `money.ts` with tests in `money.test.ts`.
- Profit/fuliza calculations live in `repository.ts` (`calculateProfit`, `calculateFulizaDebt`)
  and are unit-tested. Do not re-derive them ad hoc.

## 6. Security posture

- **Fail closed.** Defaults refuse. Example: the store's `role: 'user' | 'admin'` defaults to
  `'user'` and is **not** persisted — the Admin screen's guard
  (`role !== 'admin'` → "Not authorized") holds by default on every boot.
- **Proof must exercise the real path.** A test of a helper does not prove wiring. Security
  tests must assert the protected UI never renders for a non-admin (see
  `src/screens/AdminScreen.test.tsx`).
- Rejections are explicit: caller gets a reason (`Result<…, AppError>`), an audit row, and a
  metric — no silent drops.

## 7. Testing expectations

```bash
npm run test:run      # the gate runner (non-watch)
npx vitest run <file> # a single file, fast
```

- Business logic → unit tests; components → behavior/integration tests.
- Real-time/`requestAnimationFrame` charts (recharts) must be **mocked** in tests so CI is
  deterministic (see `AdminScreen.test.tsx`'s `vi.mock('recharts')`).
- New functionality is not "done" until its test sits beside it and the full suite is green.

## 8. Release protocol (for the programmer)

1. Bump `package.json` and `APP.VERSION` in `src/lib/constants.ts` in the same commit that
   updates `CHANGELOG.md` and the sprints/ + docs/changelog/ notes → tag that commit.
2. All five gates green locally **before** pushing the tag: typecheck, lint, check-i18n,
   test:run, build.
3. Tag only green commits; if the tag already exists on an earlier/un-green commit, re-point it
   at the final green commit (tag moves are operator-authority, announce them).
4. The `deploy` job later fires the Vercel hook. Operator confirms the version footer and sync
   status in production.

## 9. Commit hygiene

- One logical change per commit; commit each layer separately.
- Match the existing style (see `git log`): typed e.g.
  `fix(db):`, `fix(store):`, `feat(landing):`, `docs:`.
- Never commit secrets; the repo's `.env`/key files are ignored — do not force-add them.