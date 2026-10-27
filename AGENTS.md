# Daftari — Engineering Conventions

## TypeScript
- `strict: true` in tsconfig
- Branded IDs: `type BusinessId = string & { __brand: 'BusinessId' }`
- No `any` — use `unknown` + type guards
- Prefer discriminated unions over enums

## Money Safety
- No raw `+ - * /` on KES amounts — use `src/lib/money.ts`
- All monetary values stored as integer cents (number)

## Repository Pattern
- No direct Dexie imports in feature components — use `src/lib/repository.ts`
- Table names from `src/lib/constants.ts` only

## State Management
- Zustand store for global state
- React hooks for local state
- No prop drilling beyond 2 levels

## Styling
- TailwindCSS utility classes
- Dark mode via `dark:` prefix
- Mobile-first responsive design

## Data Flow
- Dexie (IndexedDB) for offline-first writes
- Supabase for remote sync and auth
- Sync queue in `src/features/sync/syncQueue.ts`

## Translation
- All user-facing strings via `t()` from `useTranslation`
- Every key in both `sw.json` and `en.json`
- Default language: Kiswahili

## Testing
- `*.test.ts` alongside implementation
- Vitest + React Testing Library
- Business logic: unit tests
- Components: integration/behavior tests

## Commands
```bash
npm run dev          # Development server
npm run build        # Production build
npm run test:run     # Run tests
npm run typecheck    # TypeScript check
npm run lint         # ESLint
npm run check:i18n   # i18n key parity check
```

## CI/CD
- GitHub Actions runs on push/PR to main
- Pipeline: typecheck → lint → test → build → deploy (Vercel)
- All stages must pass before merge

## Release & Tagging (operating procedure)
Every product upgrade ships as its own release. When a new feature/upgrade lands on `main`:
1. **Cut a release**: bump `APP.VERSION` + `package.json`/`package-lock.json` to the next
   semantic version, append a `CHANGELOG.md` section, and add/update the sprint note in
   `docs/changelog/` — in the SAME change as the upgrade, not a follow-up.
2. **Tag it**: once CI is green on that commit, `git tag v<version>` and
   `git push origin v<version>` so every upgrade is attributable and rollback-able.
3. Never ship an upgrade without its release + tag; never leave `APP.VERSION` behind the tag.
4. A hotfix that only fixes a bug in a tagged release does NOT need a version bump/tag unless
   it changes product behavior.
