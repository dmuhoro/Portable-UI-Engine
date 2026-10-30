#!/usr/bin/env node
/**
 * Design gate for Portable UI Engine.
 * Default mode scans elements/ for token, focus, motion, and a11y signals.
 * `--file <path>` lints a single fixture and fails closed on violations
 * (used by the negative gate test).
 */
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const root = process.cwd();
const fileFlag = process.argv.indexOf('--file');
const singleFile = fileFlag !== -1 ? process.argv[fileFlag + 1] : null;

let errors = 0;
let warnings = 0;

function countHardcodedColors(content) {
  const hex = content.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
  const rgb = content.match(/\brgba?\s*\(/g) || [];
  const hsl = content.match(/\bhsla?\s*\(/g) || [];
  return hex.length + rgb.length + hsl.length;
}

function countHardcodedPx(content) {
  return (content.match(/\d+px/g) || []).filter(m => !m.includes('1px') && !m.includes('0px')).length;
}

function hasFocusStyles(content) {
  return content.includes(':focus-visible') || /:focus(?!-)/.test(content) || content.includes(':focus');
}

function hasReducedMotion(content) {
  return content.includes('prefers-reduced-motion');
}

function hasMotion(content) {
  return /\banimation\b|\btransition\b|@keyframes/.test(content);
}

function lintFixture(filePath) {
  if (!existsSync(filePath)) {
    console.error(`ERROR: file not found: ${filePath}`);
    process.exit(1);
  }
  console.log(`[design-lint] Checking fixture: ${filePath}\n`);
  const content = readFileSync(filePath, 'utf8');

  const colors = countHardcodedColors(content);
  if (colors > 0) {
    console.error(`   ERROR: ${filePath} has ${colors} hardcoded color(s)`);
    errors++;
  }

  if (!hasFocusStyles(content)) {
    console.error(`   ERROR: ${filePath} is missing :focus / :focus-visible styles`);
    errors++;
  }

  if (hasMotion(content) && !hasReducedMotion(content)) {
    console.error(`   ERROR: ${filePath} animates without prefers-reduced-motion`);
    errors++;
  }
}

function lintRepository() {
  console.log('[design-lint] Starting design gate checks...\n');
  const elementsDir = join(root, 'elements');

  console.log('1. Checking token usage...');
  if (existsSync(elementsDir)) {
    for (const file of readdirSync(elementsDir).filter(f => f.endsWith('.js'))) {
      const content = readFileSync(join(elementsDir, file), 'utf8');
      const colors = countHardcodedColors(content);
      if (colors > 0) {
        console.error(`   ERROR: ${file} has ${colors} hardcoded color(s) — use CSS custom properties from packages/tokens`);
        errors++;
      }
      const px = countHardcodedPx(content);
      if (px > 0) {
        console.error(`   ERROR: ${file} has ${px} hardcoded pixel value(s) — use design tokens for spacing/radius`);
        errors++;
      }
    }
    console.log('   Done.\n');
  } else {
    console.log('   INFO: elements/ directory not found, skipping token usage check\n');
  }

  console.log('2. Checking reduced motion support...');
  if (existsSync(elementsDir)) {
    const found = readdirSync(elementsDir).filter(f => f.endsWith('.js'))
      .some(file => hasReducedMotion(readFileSync(join(elementsDir, file), 'utf8')));
    if (found) console.log('   PASS: Reduced motion queries detected\n');
    else {
      console.error('   ERROR: No reduced-motion support detected — add prefers-reduced-motion queries to all components');
      errors++;
    }
  } else {
    console.log('   INFO: elements/ directory not found\n');
  }

  console.log('3. Checking focus states...');
  if (existsSync(elementsDir)) {
    const found = readdirSync(elementsDir).filter(f => f.endsWith('.js'))
      .some(file => hasFocusStyles(readFileSync(join(elementsDir, file), 'utf8')));
    if (found) console.log('   PASS: Focus state styles detected\n');
    else {
      console.warn('   WARN: No :focus-visible/:focus styles detected — consider adding focus styles');
      warnings++;
    }
  } else {
    console.log('   INFO: elements/ directory not found\n');
  }

  console.log('4. Checking accessibility basics...');
  if (existsSync(elementsDir)) {
    let hasRole = false;
    let hasAriaLabel = false;
    for (const file of readdirSync(elementsDir).filter(f => f.endsWith('.js'))) {
      const content = readFileSync(join(elementsDir, file), 'utf8');
      if (content.includes('role=')) hasRole = true;
      if (content.includes('aria-label') || content.includes('aria-labelledby')) hasAriaLabel = true;
    }
    if (hasRole) console.log('   PASS: Some components have role attributes\n');
    else {
      console.warn('   WARN: No role attributes detected — consider adding explicit roles');
      warnings++;
    }
    if (hasAriaLabel) console.log('   PASS: Some components have aria-label/aria-labelledby\n');
    else {
      console.warn('   WARN: No aria-label/aria-labelledby detected — consider adding label associations');
      warnings++;
    }
  } else {
    console.log('   INFO: elements/ directory not found\n');
  }
}

if (singleFile) lintFixture(singleFile);
else lintRepository();

console.log(`${errors > 0 ? 'ERRORS' : 'PASS'}: ${errors} error(s), ${warnings} warning(s)\n`);
process.exit(errors > 0 ? 1 : 0);
