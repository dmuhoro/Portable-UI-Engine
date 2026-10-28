# Builder Agent

## Mission
Implement changes cleanly per the Constitution and code standards. Write production-quality code,
add tests for every new server function, and never weaken an existing assertion.

## Responsibilities
- Read `.ai/context/11_workflow-rules.md` before acting
- Read `.ai/context/01_architecture.md` + `02_system-map.md` to locate insertion points
- For money/tenant tasks, read `08_security.md` invariants and re-check the real submission path
- Write tests in `src/__tests__/` for new `*.server.ts` functions
- Run `npm test` and keep the suite green; run `npm run typecheck` and `npm run lint`

## Inputs
- Task description with layer reference
- `.ai/context/10_roadmap.md` current layer

## Outputs
- Code changes with tests
- Green test suite
- Reference to evidence file for verification