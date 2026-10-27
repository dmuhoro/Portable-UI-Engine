#!/usr/bin/env node
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, extname } from 'path';

const root = process.cwd();
console.log('[design-lint] Starting design gate checks...\n');

let errors = 0;
let warnings = 0;

// Check 1: Token usage
console.log('1. Checking token usage...');
const elementsDir = join(root, 'elements');
if (existsSync(elementsDir)) {
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    const hardcodedColors = (content.match(/#[0-9a-fA-F]{3,6}/g) || []).length;
    const hardcodedPx = (content.match(/\d+px/g) || []).filter(m => !m.includes('1px') && !m.includes('0px')).length;
    if (hardcodedColors > 0) {
      console.log(`   WARN: ${file} has ${hardcodedColors} hardcoded color(s)`);
      warnings++;
    }
    if (hardcodedPx > 3) {
      console.log(`   WARN: ${file} has ${hardcodedPx} hardcoded pixel values`);
      warnings++;
    }
  }
  console.log(`   Done. Warnings: ${warnings}\n`);
}

// Check 2: Reduced motion
console.log('2. Checking reduced motion support...');
if (existsSync(elementsDir)) {
  let hasReducedMotion = false;
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    if (content.includes('prefers-reduced-motion')) hasReducedMotion = true;
  }
  if (hasReducedMotion) {
    console.log('   PASS: Reduced motion queries found\n');
  } else {
    console.log('   WARN: No reduced-motion support detected\n');
    warnings++;
  }
}

// Check 3: Focus states
console.log('3. Checking focus states...');
console.log('   INFO: Manual review recommended for :focus-visible\n');

// Check 4: A11y basics
console.log('4. Checking accessibility basics...');
console.log('   INFO: Run axe-core for full audit\n');

console.log(`\n[design-lint] Complete: ${errors} errors, ${warnings} warnings`);
process.exit(errors > 0 ? 1 : 0);
