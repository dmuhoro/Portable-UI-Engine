#!/usr/bin/env npx tsx
/**
 * i18n coverage linter — run via:
 *   npx tsx scripts/check-i18n.ts
 *
 * Checks:
 * 1. Every key in sw.json exists in en.json (and vice versa)
 * 2. Every key used in t('key') calls exists in both JSON files
 * 3. Reports unused translation keys
 */

import { readFileSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')

const sw: Record<string, string> = JSON.parse(readFileSync(join(root, 'src/i18n/sw.json'), 'utf-8'))
const en: Record<string, string> = JSON.parse(readFileSync(join(root, 'src/i18n/en.json'), 'utf-8'))

const swKeys = new Set(Object.keys(sw))
const enKeys = new Set(Object.keys(en))

let exitCode = 0

function fail(msg: string) {
  console.error(`❌ ${msg}`)
  exitCode = 1
}

// 1. Cross-check SW ↔ EN
for (const k of swKeys) {
  if (!enKeys.has(k)) fail(`Key "${k}" exists in sw.json but NOT in en.json`)
}
for (const k of enKeys) {
  if (!swKeys.has(k)) fail(`Key "${k}" exists in en.json but NOT in sw.json`)
}

// 2. Walk src/ and collect t() calls
const SRC = join(root, 'src')

const tCalls = new Set<string>()

function walk(dir: string) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
      walk(full)
    } else if (entry.isFile() && /\.(ts|tsx)$/.test(entry.name) && !entry.name.includes('.test.')) {
      const content = readFileSync(full, 'utf-8')
      for (const match of content.matchAll(/(?<![$\w])t\(['"]([^'"]+)['"][,)]/g)) {
        tCalls.add(match[1])
      }
    }
  }
}

walk(SRC)

for (const k of tCalls) {
  if (!swKeys.has(k)) fail(`Translation key "${k}" used in source but MISSING from sw.json`)
  if (!enKeys.has(k)) fail(`Translation key "${k}" used in source but MISSING from en.json`)
}

// Keys rendered via t(someKey) where the key is not a literal in the t(...)
// call, so the regex above cannot see them. Sourced from the ACTUAL files that
// reference those keys (per render site), so the list cannot drift from code:
//   - OnboardingScreen option cards: `labelKey: '...'` (pain points, methods)
//   - OnboardingScreen yes-set questions: `{ id: N, key: '...' }`
//   - Receipt: `labelKey = ... ? 'sale_recorded' : 'expense_recorded' : 'withdrawal_recorded'`
//   - UpgradeScreen: `PLAN_KEYS` / `FEATURE_KEYS` maps with `labelKey: '...'`
//   - SettingsScreen: `TIER_KEYS` / `STATUS_KEYS` maps with `labelKey: '...'`
//   - SatisfactionPrompt: `SCORE_KEYS = ['sat_score_1', ...]` rendered as
//     t(SCORE_KEYS[i]) — a bare `_KEYS` literal array
const DYNAMIC_KEY_SITES = ['src/screens/OnboardingScreen.tsx', 'src/components/Receipt.tsx', 'src/screens/UpgradeScreen.tsx', 'src/screens/SettingsScreen.tsx', 'src/components/SatisfactionPrompt.tsx']
const DYNAMIC_KEYS = new Set<string>()
for (const f of DYNAMIC_KEY_SITES) {
  const content = readFileSync(join(root, f), 'utf-8')
  for (const m of content.matchAll(/labelKey:\s*'([^']+)'/g)) DYNAMIC_KEYS.add(m[1])
  for (const m of content.matchAll(/\bid:\s*\d+,?\s*key:\s*'([^']+)'/g)) DYNAMIC_KEYS.add(m[1])
  for (const m of content.matchAll(/'(sale_recorded|expense_recorded|withdrawal_recorded)'/g)) {
    DYNAMIC_KEYS.add(m[1])
  }
  // `const FOO_KEYS = ['k1', 'k2', ...]` literal arrays whose entries are passed
  // to t() indirectly (t(FOO_KEYS[i]), t(FOO_KEYS[score]), ...). Every entry must
  // exist in both locales.
  for (const block of content.matchAll(/(?:const\s+)?[A-Z][A-Z0-9_]*_KEYS\s*=\s*\[([^\]]*)\]/g)) {
    for (const literal of block[1].matchAll(/['"]([^'"]+)['"]/g)) DYNAMIC_KEYS.add(literal[1])
  }
}

// Onboarding receiving-accounts stage renders t(ACCOUNT_NUMBER_KEYS[method]);
// the referenced keys are literals in that map and must exist in both locales.
// Onboarding receiving-accounts stage renders t(ACCOUNT_NUMBER_KEYS[method]) and
// t(accountErrorText(...)); those referenced keys are literals in that file and
// must exist in both locales.
const onboarding = readFileSync(join(root, 'src/screens/OnboardingScreen.tsx'), 'utf-8')
for (const m of onboarding.matchAll(/'(account_number_[a-z_]+|account_name_invalid|account_bank_invalid)'/g)) DYNAMIC_KEYS.add(m[1])

for (const k of DYNAMIC_KEYS) {
  if (swKeys.has(k) && enKeys.has(k)) {
    tCalls.add(k)
  } else {
    fail(`Dynamic key "${k}" referenced in ${DYNAMIC_KEY_SITES.join(', ')} but MISSING from sw.json/en.json`)
  }
}

// 3. Fail on unused keys in either locale. A key nothing renders is dead weight:
//    it drifts from the UI and hides the next set of keys nobody moved.
const unusedSw = [...swKeys].filter(k => !tCalls.has(k))
const unusedEn = [...enKeys].filter(k => !tCalls.has(k))
const unused = [...new Set([...unusedSw, ...unusedEn])]
for (const k of unused) {
  const where = `${swKeys.has(k) ? 'sw' : ''}${swKeys.has(k) && enKeys.has(k) ? '+' : ''}${enKeys.has(k) ? 'en' : ''}`
  fail(`Unused translation key "${k}" in ${where}.json — remove it or wire it up.`)
}

if (exitCode === 0) {
  console.log(`✅ i18n check passed — ${tCalls.size} keys in use, ${swKeys.size} in sw.json, ${enKeys.size} in en.json`)
}

process.exit(exitCode)
