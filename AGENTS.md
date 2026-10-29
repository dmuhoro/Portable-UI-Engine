# Portable UI Engine — Engineering Conventions

## TypeScript
- `strict: true` in tsconfig
- No `any` — use `unknown` + type guards
- Prefer discriminated unions over enums
- Branded IDs for business keys where needed

## Money Safety (if applicable)
- No raw `+ - * /` on monetary amounts — use `src/lib/money.ts` if present
- All monetary values stored as integer cents (`number`) when dealing with KES

## Repository Pattern
- No direct Dexie imports in feature components
- Table names from `src/lib/constants.ts` only when using Dexie
- Prefer framework-agnostic storage approaches

## State Management
- Zustand store for global state when using React
- React hooks for local state
- No prop drilling beyond 2 levels
- Web Components use attributes/properties for state

## Styling
- TailwindCSS utility classes
- Dark mode via `dark:` prefix
- Mobile-first responsive design
- Design tokens from `packages/tokens` are the source of truth
- Styling stays inside Shadow DOM; use CSS custom properties for theming
- **UI Engine Skill**: See `docs/agent/UI-ENGINE-SKILL.md` for agent guidance on using ui-* primitives and tokens

## Data Flow
- Web Components communicate via CustomEvents (bubbles: true, composed: true)
- Dexie (IndexedDB) for offline-first writes when applicable
- Supabase for remote sync and auth when applicable
- Sync queue mechanism when offline-first needed

## Translation
- All user-facing strings via `t()` from `useTranslation`
- Every key in both `sw.json` and `en.json`
- Default language: Kiswahili when i18n is used

## Testing
- Business logic: unit tests
- Components: integration/behavior tests
- Accessibility: axe-core, reduced-motion tests
- Web Component specific: slot projection, attribute reflection

## Commands
```bash
npm run dev          # Development server
npm run build        # Production build
npm run build:engine # Engine bundle only
npm run preview      # Preview server
npm run test         # Run tests
npm run lint         # ESLint / TypeScript check
```

## CI/CD
- GitHub Actions runs on push/PR to main
- Pipeline: typecheck → lint → test → build → deploy
- All stages must pass before merge
- Branch protection: require PRs, disallow admin bypass

## Release & Tagging (operating procedure)
Every product upgrade ships as its own release. When a new feature/upgrade lands on main:
1. **Cut a release**: bump `APP.VERSION` + `package.json`/`package-lock.json` to the next semantic version, append a CHANGELOG.md section, and add sprint note in docs/changelog/ — in the SAME change as the upgrade
2. **Tag it**: once CI is green, `git tag v<version>` and `git push origin v<version>`
3. Never ship an upgrade without its release + tag; never leave APP.VERSION behind the tag
4. A hotfix that only fixes a bug in a tagged release does NOT need a version bump/tag unless it changes product behavior

## Design Token Discipline
- All visual styling consumes CSS custom properties from `packages/tokens`
- Never hardcode colors, spacing, or radii inside components — use tokens
- Token generator (`packages/tokens/scripts/build-tokens.js`) produces the source of truth
- Generated `theme.css` is derived from tokens, not hand-edited in isolation
