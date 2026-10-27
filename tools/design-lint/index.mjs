#!/usr/bin/env node
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, extname } from 'path';

const root = process.cwd();
console.log('[design-lint] Starting design gate checks...\n');

let errors = 0;
let warnings = 0;

// Check 1: Token usage — hardcoded colors and pixels are ERRORs
console.log('1. Checking token usage...');
const elementsDir = join(root, 'elements');
if (existsSync(elementsDir)) {
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    const hardcodedColors = (content.match(/#[0-9a-fA-F]{3,6}/g) || []).length;
    const hardcodedPx = (content.match(/\d+px/g) || []).filter(m => !m.includes('1px') && !m.includes('0px')).length;
    if (hardcodedColors > 0) {
      console.error(`   ERROR: ${file} has ${hardcodedColors} hardcoded color(s) — use CSS custom properties from packages/tokens`);
      errors++;
    }
    if (hardcodedPx > 0) {
      console.error(`   ERROR: ${file} has ${hardcodedPx} hardcoded pixel value(s) — use design tokens for spacing/radius`);
      errors++;
    }
  }
  console.log(`   Done.\n`);
} else {
  console.log('   INFO: elements/ directory not found, skipping token usage check\n');
}

// Check 2: Reduced motion — required, must be present
console.log('2. Checking reduced motion support...');
if (existsSync(elementsDir)) {
  let hasReducedMotion = false;
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    if (content.includes('prefers-reduced-motion')) hasReducedMotion = true;
  }
  if (hasReducedMotion) {
    console.log('   PASS: Reduced motion queries detected\n');
  } else {
    console.error('   ERROR: No reduced-motion support detected — add prefers-reduced-motion queries to all components');
    errors++;
  }
} else {
  console.log('   INFO: elements/ directory not found\n');
}

// Check 3: Focus states — required structural check
console.log('3. Checking focus states...');
if (existsSync(elementsDir)) {
  let hasFocus = false;
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    if (content.includes(':focus-visible') || content.includes(':focus')) hasFocus = true;
  }
  if (hasFocus) {
    console.log('   PASS: Focus state styles detected\n');
  } else {
    console.warn('   WARN: No :focus-visible/:focus styles detected — consider adding focus styles');
    warnings++;
  }
} else {
  console.log('   INFO: elements/ directory not found\n');
}

// Check 4: A11y basics — role and label presence
console.log('4. Checking accessibility basics...');
if (existsSync(elementsDir)) {
  let hasRole = false;
  let hasAriaLabel = false;
  const files = readdirSync(elementsDir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const content = readFileSync(join(elementsDir, file), 'utf8');
    if (content.includes('role=')) hasRole = true;
    if (content.includes('aria-label') || content.includes('aria-labelledby')) hasAriaLabel = true;
  }
  if (hasRole) {
    console.log('   PASS: Some components have role attributes\n');
  } else {
    console.warn('   WARN: No role attributes detected — consider adding explicit roles');
    warnings++;
  }
  if (hasAriaLabel) {
    console.log('   PASS: Some components have aria-label/aria-labelledby\n');
  } else {
    console.warn('   WARN: No aria-label/aria-labelledby detected — consider adding label associations');
    warnings++;
  }
} else {
  console.log('   INFO: elements/ directory not found\n');
}

console.log(`${errors > 0 ? 'ERRORS' : 'PASS'}: ${errors} error(s), ${warnings} warning(s)\n`);
process.exit(errors > 0 ? 1 : 0);
