# Master TODO - Portable UI Engine Infrastructure Completion

**Status:** In Progress  
**Branch:** audit/ui-00-baseline  
**Goal:** Complete all Opencode-scoped work to bring repo closer to production-ready design system  
**Last Updated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)

---

## LAYER 0: GROUND TRUTH (Read-Only Recon) ✅
- [x] Read core files (README, package.json, tsconfig, vite.config, build.js, engine.js, theme.css)
- [x] Read components (universal-*.js, elements/, src/)
- [x] Read tests, qa-pressure-test.js, sprints/
- [x] Read existing docs (CONTRIBUTING, ARCHITECTURE, ROADMAP, SECURITY, AGENTS)
- [x] Check git state, branches, remotes, recent commits
- [x] Inventory npm scripts
- [x] Create evidence directory structure

**Evidence:** `docs/evidence/ground-truth/`

---

## LAYER 1: CONSTITUTION, ADRs, ARCHITECTURE ALIGNMENT ✅
- [x] Create `docs/CONSTITUTION.md`
- [x] Create ADR-0001: Monorepo Structure
- [x] Create ADR-0002: Tokens as Source of Truth
- [x] Create ADR-0003: Design Gate via Teardown Lab
- [x] Create `docs/architecture/OVERVIEW.md`
- [x] Reconcile AGENTS.md (keep useful rules)
- [x] Commit individually

**Evidence:** `docs/CONSTITUTION.md`, `docs/adr/`, `docs/architecture/OVERVIEW.md`

---

## LAYER 2: MONOREPO SCAFFOLD (Non-Breaking) ✅
- [x] Create directory structure (`packages/`, `apps/`, `tools/`, `design/`)
- [x] Mirror core to `packages/engine/` (engine.js, elements/, theme.css, dist/)
- [x] Create `packages/engine/package.json`
- [x] Create `packages/tokens/package.json`
- [x] Add `pnpm-workspace.yaml`
- [x] Create `tools/design-lint/` scaffold
- [x] Scaffold all apps (docs, teardown-lab, run-theater, commit-garden, pattern-foundry)
- [x] Create `design/briefs/` and `design/directions/`
- [x] Verify build still works
- [x] Commit individually

**Evidence:** `packages/`, `apps/`, `tools/`, `pnpm-workspace.yaml`

---

## LAYER 3: TOKEN PIPELINE ✅
- [x] Create `packages/tokens/design-tokens.json` (W3C format)
- [x] Create token generator scripts (build-tokens.mjs, build-tokens.js)
- [x] Generate `packages/tokens/css/variables.css`
- [x] Generate `packages/tokens/ts/tokens.ts`
- [x] Update root `theme.css` from tokens
- [x] Sync to `packages/engine/`
- [x] Add packages/tokens/README.md
- [x] Test generation
- [x] Commit individually

**Evidence:** `packages/tokens/design-tokens.json`, generated CSS/TS

---

## LAYER 4: PRIMITIVES & ACCESSIBILITY GROUNDWORK 🔄
- [ ] Audit existing components for a11y gaps
- [ ] Create `elements/_shared/` utilities (focus trap, a11y helpers, reduced-motion)
- [ ] Create `packages/engine/elements/_shared/` mirror
- [ ] Add ElementInternals helpers for form participation
- [ ] Create primitive scaffolds (button, input, select, checkbox) - structure only, minimal implementation
- [ ] Add reduced-motion support utilities
- [ ] Document a11y patterns
- [ ] Commit individually

**Evidence:** `elements/_shared/`, a11y audit notes in `docs/evidence/`

---

## LAYER 5: TEARDOWN LAB (#5) + DESIGN GATE 🔄
- [x] Create `apps/teardown-lab/` scaffold
- [x] Add rubric loader
- [x] Add basic HTML structure
- [ ] Create rubric-v1.json in accessible location or copy from audit
- [ ] Implement scoring logic structure
- [ ] Enhance `tools/design-lint/` with actual checks:
  - [ ] Token usage validation
  - [ ] Hardcoded color detection
  - [ ] Focus state checks
  - [ ] Reduced motion checks
  - [ ] A11y basic checks
- [ ] Create design gate evidence output structure
- [ ] Add CLI usage docs
- [ ] Commit individually

**Evidence:** `apps/teardown-lab/`, `tools/design-lint/`, `docs/evidence/design-gate/`

---

## LAYER 6: SPRINTS, CHANGELOG, EVIDENCE, COMMITS, PUSH 🔄
- [x] Create `sprints/sprint-ui-01-infrastructure-foundation.md`
- [x] Update `CHANGELOG.md` with Unreleased section
- [x] Create `docs/ai-studio/DIRECTIVE.md`
- [x] Commit after each subtask
- [x] Push to `audit/ui-00-baseline`
- [ ] Create comprehensive sprint doc for this directive execution
- [ ] Update all sprint references
- [ ] Generate final evidence report
- [ ] Ensure all tests pass (npm run test/build/lint)
- [ ] Verify no TypeScript errors blocking build
- [ ] Final push to GitHub
- [ ] Stop cleanly

**Evidence:** All commits, push history, evidence reports

---

## ONGOING MAINTENANCE
- [ ] Keep engine distributable paths working (engine.js, theme.css, dist/)
- [ ] Maintain backward compatibility
- [ ] All commits atomic and descriptive
- [ ] Never merge, never use --admin
- [ ] Follow constitution and ADRs

---

## AI STUDIO DIRECTIVE PREPARATION
- [ ] Document what was done in Opencode scope
- [ ] Document what AI Studio should do
- [ ] List briefs needed (design directions, component briefs, app compositions)
- [ ] Specify handoff format and locations
- [ ] Include acceptance criteria for AI Studio work

**Output:** `docs/ai-studio/OPENCODE-COMPLETED.md` + updated `DIRECTIVE.md`
