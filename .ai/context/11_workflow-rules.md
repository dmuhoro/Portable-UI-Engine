# Workflow Rules Brief

> The rules governing agent execution. Canonical: `docs/engineering/CONSTITUTION.md` + root `AGENTS.md`.

## Hard Rules

1. **Never weaken a test to pass a build.** Fix the code (AGENTS.md rule 4).
2. **Never modify `src/routeTree.gen.ts` directly** — edit `src/routes/`, let the generator rebuild (rule 1).
3. **Tenant-scoping changes in `*.server.ts` require a `docs/db-contracts.md` update** in the same commit (rule 2).
4. **New server functions touching leads/scheduling/notifications need tests in `src/__tests__/`** (rule 3).
5. **No new dependency without justification** against existing packages (rule 5).
6. **Read `docs/architecture.md` (+ `docs/current-state.md` when present) before starting.** If a task
   assumes an **ASPIRATIONAL** capability, stop and say so (rule 6).
7. **Explicit commit messages** — state what changed + which doc needs updating (rule 7).
8. **Feature freeze on open P0s** — no new subsystem while P0s are open in db-contracts/release-readiness (rule 8).
9. **Diagnostic tests must be marked** `xfail`/`skip` with a linked issue (rule 9).
10. **All commits SSH-signed** — `commit.gpgsign=true`, `gpg.format ssh`, key `~/.ssh/id_ed25519.pub` (rule 10).

## Execution-Safety Rules (from Constitution Article I)

- Fail closed. Enforcement at the real boundary. Proof exercises the real path. No silent drops.
- Say no early, loudly, if a plan is flawed — propose the corrected version before executing.

## Operating Rhythm

- Work sequentially in layers; finish one layer before the next.
- Commit each piece individually with an explicit message.
- Everything green before push. Loop until no tasks remain pending.
- Update `docs/sprints/` and `CHANGELOG.md` with what was built.