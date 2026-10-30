#!/usr/bin/env node
/**
 * Fails if any registered ui-* element is missing from design/contracts/components.json.
 */
import { readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const REQUIRED = [
  'ui-button', 'ui-input', 'ui-checkbox', 'ui-select',
  'ui-dialog', 'ui-tooltip', 'ui-toast', 'ui-tabs', 'ui-menu',
];

const gen = spawnSync(process.execPath, ['scripts/generate-manifest.mjs'], { encoding: 'utf8' });
if (gen.status !== 0) {
  console.error(gen.stdout);
  console.error(gen.stderr);
  process.exit(gen.status || 1);
}

const manifestPath = 'design/contracts/components.json';
if (!existsSync(manifestPath)) {
  console.error('test-manifest: components.json missing');
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const tags = new Set((manifest.elements || []).map(el => el.tagName));

const source = existsSync('packages/engine/elements/ui-primitives.js')
  ? readFileSync('packages/engine/elements/ui-primitives.js', 'utf8')
  : readFileSync('elements/ui-primitives.js', 'utf8');
const registered = [...source.matchAll(/\['(ui-[a-z0-9-]+)'/g)].map(m => m[1]);
const uniqueRegistered = [...new Set(registered)];

const missingFromManifest = uniqueRegistered.filter(tag => !tags.has(tag));
const missingRequired = REQUIRED.filter(tag => !tags.has(tag));

if (missingFromManifest.length || missingRequired.length) {
  console.error('test-manifest: FAIL');
  if (missingFromManifest.length) console.error('  registered but missing from manifest:', missingFromManifest.join(', '));
  if (missingRequired.length) console.error('  required but missing from manifest:', missingRequired.join(', '));
  process.exit(1);
}

console.log(`test-manifest: PASS (${tags.size} elements; ${REQUIRED.length} required covered)`);
