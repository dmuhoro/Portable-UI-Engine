#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const content = readFileSync('packages/engine/elements/ui-primitives.js', 'utf-8');
const tags = [...content.matchAll(/\['([^']+)'/g)].map(m => m[1]).filter(t => t.startsWith('ui-'));

const manifest = {
  schemaVersion: '1.0.0',
  name: '@universal-ui/engine',
  version: '2.1.0',
  generatedAt: new Date().toISOString(),
  elements: tags.map(tagName => ({
    tagName,
    attributes: [],
    events: [`${tagName}-change`, `${tagName}-click`].filter((_, i, arr) => tagName.includes('button') || tagName.includes('input') || tagName.includes('select') || tagName.includes('checkbox')),
    slots: ['default', 'icon-start', 'icon-end', 'label', 'footer'].filter((_, i, arr) => tagName === 'button' || tagName === 'input' || tagName === 'dialog'),
    cssCustomProperties: ['--color-brand-primary', '--color-text-primary', '--spacing-md', '--radius-sm'],
    cssParts: [],
    accessibility: { keyboard: true, focusable: true, ariaSupport: true }
  }))
};

mkdirSync('design/contracts', { recursive: true });
writeFileSync('design/contracts/components.json', JSON.stringify(manifest, null, 2));
console.log('Manifest generated:', manifest.elements.length, 'elements');
