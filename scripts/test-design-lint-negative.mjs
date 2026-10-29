#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';

const fixturesDir = 'tools/design-lint/fixtures';
const fixtures = readdirSync(fixturesDir).filter(f => f.endsWith('.css') || f.endsWith('.js') || f.endsWith('.html'));

let passed = 0;
let failed = 0;

for (const fixture of fixtures) {
  const result = spawnSync('node', ['tools/design-lint/index.mjs', '--file', join(fixturesDir, fixture)], { encoding: 'utf-8' });
  if (result.status !== 0) {
    console.log(`✓ ${fixture}: correctly failed with exit code ${result.status}`);
    passed++;
  } else {
    console.log(`✗ ${fixture}: should have failed but passed`);
    failed++;
  }
}

console.log(`\nNegative gate tests: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
