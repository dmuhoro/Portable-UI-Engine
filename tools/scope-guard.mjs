#!/usr/bin/env node
/**
 * Fails when changed files fall outside design/scope-allowlist.json.
 * Usage:
 *   node tools/scope-guard.mjs                 # diff against origin/main
 *   node tools/scope-guard.mjs --base <ref>
 *   SCOPE_GUARD_FILES=$'a\nb' node tools/scope-guard.mjs
 */
import { readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const root = process.cwd();
const allowPath = join(root, 'design/scope-allowlist.json');
if (!existsSync(allowPath)) {
  console.error('scope-guard: missing design/scope-allowlist.json');
  process.exit(1);
}

const config = JSON.parse(readFileSync(allowPath, 'utf8'));
const allow = Array.isArray(config.allow) ? config.allow : [];

const baseFlag = process.argv.indexOf('--base');
const base = baseFlag !== -1 ? process.argv[baseFlag + 1] : 'origin/main';

function listChangedFiles() {
  if (process.env.SCOPE_GUARD_FILES) {
    return process.env.SCOPE_GUARD_FILES.split('\n').map(s => s.trim()).filter(Boolean);
  }
  const result = spawnSync('git', ['diff', '--name-only', `${base}...HEAD`], { encoding: 'utf8' });
  if (result.status !== 0) {
    // Fallback: unstaged + staged against HEAD when base is unavailable
    const local = spawnSync('git', ['diff', '--name-only', 'HEAD'], { encoding: 'utf8' });
    const staged = spawnSync('git', ['diff', '--name-only', '--cached'], { encoding: 'utf8' });
    return `${local.stdout || ''}\n${staged.stdout || ''}`.split('\n').map(s => s.trim()).filter(Boolean);
  }
  return result.stdout.split('\n').map(s => s.trim()).filter(Boolean);
}

function allowed(file) {
  return allow.some(prefix => {
    if (prefix === '*') return true;
    if (prefix.endsWith('/')) return file === prefix.slice(0, -1) || file.startsWith(prefix);
    return file === prefix || file.startsWith(`${prefix}/`);
  });
}

const files = listChangedFiles();
const violations = files.filter(file => !allowed(file));

console.log(`scope-guard: checked ${files.length} file(s) against ${allow.length} allowlist entries`);
if (violations.length) {
  console.error('scope-guard: files outside allowlist:');
  for (const file of violations) console.error(`  - ${file}`);
  console.error('\nTighten or update design/scope-allowlist.json intentionally.');
  process.exit(1);
}
console.log('scope-guard: PASS');
