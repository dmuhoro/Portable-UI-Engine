# GitHub Copilot Verification Directive

**Target:** GitHub Copilot (in repo context)  
**Branch:** audit/ui-00-baseline  
**Purpose:** Verify ALL Opencode-scoped work is complete, properly committed, and nothing unfinished

## Mission
Verify every layer (0-6) has been fully executed with evidence. Mark verification results with proof (file paths, git history, checks). Do NOT modify source - only read and report.

## Verification Checklist

### LAYER 0: Ground Truth
- [ ] All core files inventoried (README, package.json, engine.js, theme.css, elements/, universal-*.js)
- [ ] Evidence exists in `docs/evidence/ground-truth/`
- [ ] Git history shows reconnaissance commits

### LAYER 1: Constitution, ADRs, Architecture
- [ ] `docs/CONSTITUTION.md` exists and complete
- [ ] ADRs 0001, 0002, 0003 exist in `docs/adr/`
- [ ] `docs/architecture/OVERVIEW.md` exists
- [ ] AGENTS.md reconciled appropriately
- [ ] Commits present

### LAYER 2: Monorepo Scaffold
- [ ] `packages/engine/` has engine.js, elements/, theme.css, dist/, package.json
- [ ] `packages/tokens/` has package.json, design-tokens.json, scripts/, css/, ts/
- [ ] `apps/` has docs, teardown-lab, run-theater, commit-garden, pattern-foundry
- [ ] `tools/design-lint/` exists
- [ ] `design/briefs/` and `design/directions/` exist
- [ ] `pnpm-workspace.yaml` exists
- [ ] Build still works: `npm run build:engine`

### LAYER 3: Token Pipeline
- [ ] `packages/tokens/design-tokens.json` is valid W3C format
- [ ] Generators exist (build-tokens.js/mjs)
- [ ] `packages/tokens/css/variables.css` generated
- [ ] `packages/tokens/ts/tokens.ts` generated
- [ ] Root `theme.css` updated from tokens
- [ ] Can regenerate tokens successfully

### LAYER 4: Primitives & A11y Groundwork
- [ ] `elements/_shared/a11y-utils.js` exists
- [ ] `packages/engine/elements/_shared/a11y-utils.js` mirrored
- [ ] Utilities functional (trapFocus, prefersReducedMotion, announce)
- [ ] Evidence documented

### LAYER 5: Teardown Lab + Design Gate
- [ ] `apps/teardown-lab/` complete (index.html, rubric-loader.js, rubric-v1.json)
- [ ] `tools/design-lint/index.mjs` enhanced with checks
- [ ] Design gate structure ready
- [ ] Rubric v1 accessible

### LAYER 6: Sprints, Changelog, Evidence, Commits, Push
- [ ] All sprints updated/created
- [ ] `CHANGELOG.md` updated with Unreleased section
- [ ] `docs/ai-studio/DIRECTIVE.md` exists
- [ ] `docs/ai-studio/OPENCODE-COMPLETED.md` exists
- [ ] `tasks/MASTER-TODO.md` exists and accurately reflects state
- [ ] All commits atomic and descriptive
- [ ] Pushed to `origin/audit/ui-00-baseline`
- [ ] Git status clean or only expected untracked

## Verification Commands
```bash
git log --oneline -20
git branch -a
git status
npm run build:engine
node packages/tokens/scripts/build-tokens.js
node tools/design-lint/index.mjs
ls -la packages/ apps/ tools/ design/ docs/adr/ docs/ai-studio/
```

## Output Required
Create `docs/evidence/copilot-verification/VERIFICATION-REPORT.md` with:
- Pass/Fail for each layer
- Evidence (file paths, commit SHAs)
- Any gaps found
- Recommendation: APPROVE or BLOCK
- If BLOCK, list exact fixes needed

**Do NOT fix - only verify and report.**
