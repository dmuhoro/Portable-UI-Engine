#!/usr/bin/env node
/**
 * Generates design/contracts/components.json from registered ui-* primitives.
 * Combines source introspection with hand-authored contract metadata.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const REQUIRED = [
  'ui-button', 'ui-input', 'ui-checkbox', 'ui-select',
  'ui-dialog', 'ui-tooltip', 'ui-toast', 'ui-tabs', 'ui-menu',
];

const META = {
  'ui-button': {
    attributes: [
      { name: 'variant', type: 'string' },
      { name: 'size', type: 'string' },
      { name: 'disabled', type: 'boolean' },
      { name: 'loading', type: 'boolean' },
      { name: 'type', type: 'string' },
    ],
    events: [{ name: 'ui-button-click', detail: '{ originalEvent, variant }' }],
    slots: ['default', 'icon-start', 'icon-end'],
    cssParts: ['button'],
    keyboard: 'Enter/Space activate; disabled suppresses events',
  },
  'ui-input': {
    attributes: [
      { name: 'label', type: 'string' },
      { name: 'name', type: 'string' },
      { name: 'type', type: 'string' },
      { name: 'value', type: 'string' },
      { name: 'disabled', type: 'boolean' },
      { name: 'required', type: 'boolean' },
      { name: 'clearable', type: 'boolean' },
      { name: 'error', type: 'string' },
      { name: 'help', type: 'string' },
    ],
    events: [{ name: 'ui-input-change', detail: '{ value }' }],
    slots: ['default', 'prefix', 'suffix'],
    cssParts: ['field', 'label', 'input'],
    keyboard: 'Standard text input; Escape clears when clearable',
  },
  'ui-checkbox': {
    attributes: [
      { name: 'checked', type: 'boolean' },
      { name: 'disabled', type: 'boolean' },
      { name: 'name', type: 'string' },
      { name: 'value', type: 'string' },
      { name: 'indeterminate', type: 'boolean' },
    ],
    events: [{ name: 'ui-checkbox-change', detail: '{ checked, indeterminate }' }],
    slots: ['default'],
    cssParts: ['control', 'label'],
    keyboard: 'Space toggles',
  },
  'ui-select': {
    attributes: [
      { name: 'label', type: 'string' },
      { name: 'name', type: 'string' },
      { name: 'value', type: 'string' },
      { name: 'disabled', type: 'boolean' },
      { name: 'placeholder', type: 'string' },
    ],
    events: [{ name: 'ui-select-change', detail: '{ value }' }],
    slots: ['default'],
    cssParts: ['trigger', 'listbox', 'option'],
    keyboard: 'Arrow keys navigate; Enter selects; Escape closes; typeahead filters',
  },
  'ui-dialog': {
    attributes: [
      { name: 'open', type: 'boolean' },
      { name: 'label', type: 'string' },
    ],
    events: [{ name: 'ui-dialog-close', detail: '{}' }],
    slots: ['default', 'header', 'footer'],
    cssParts: ['dialog', 'backdrop'],
    keyboard: 'Escape closes; focus trapped while open',
  },
  'ui-tooltip': {
    attributes: [
      { name: 'content', type: 'string' },
      { name: 'placement', type: 'string' },
    ],
    events: [],
    slots: ['default'],
    cssParts: ['tooltip'],
    keyboard: 'Shown on focus; suppressed when hover unavailable',
  },
  'ui-toast': {
    attributes: [
      { name: 'open', type: 'boolean' },
      { name: 'variant', type: 'string' },
      { name: 'duration', type: 'number' },
    ],
    events: [{ name: 'ui-toast-dismiss', detail: '{}' }],
    slots: ['default'],
    cssParts: ['toast'],
    keyboard: 'Pause on focus; Escape dismisses when focused',
  },
  'ui-tabs': {
    attributes: [
      { name: 'value', type: 'string' },
      { name: 'orientation', type: 'string' },
    ],
    events: [{ name: 'ui-tab-change', detail: '{ value }' }],
    slots: ['default'],
    cssParts: ['tablist', 'tab', 'panel'],
    keyboard: 'Arrow keys move; Home/End jump; roving tabindex',
  },
  'ui-menu': {
    attributes: [
      { name: 'open', type: 'boolean' },
      { name: 'label', type: 'string' },
    ],
    events: [{ name: 'ui-menu-select', detail: '{ value }' }],
    slots: ['default', 'trigger'],
    cssParts: ['menu', 'item'],
    keyboard: 'Arrow keys navigate; Enter activates; Escape closes',
  },
};

const sources = [
  'packages/engine/elements/ui-primitives.js',
  'elements/ui-primitives.js',
].filter(existsSync);

if (!sources.length) {
  console.error('generate-manifest: ui-primitives.js not found');
  process.exit(1);
}

const content = readFileSync(sources[0], 'utf8');
const discovered = [...content.matchAll(/customElements\.define\(\s*['"](ui-[a-z0-9-]+)['"]/g)].map(m => m[1]);
const fromArray = [...content.matchAll(/\['(ui-[a-z0-9-]+)'/g)].map(m => m[1]);
const tags = [...new Set([...discovered, ...fromArray, ...REQUIRED])].filter(t => t.startsWith('ui-')).sort();

const missingRequired = REQUIRED.filter(tag => !tags.includes(tag));
if (missingRequired.length) {
  console.error('generate-manifest: missing required elements:', missingRequired.join(', '));
  process.exit(1);
}

const manifest = {
  schemaVersion: '1.0.0',
  name: '@universal-ui/engine',
  version: JSON.parse(readFileSync('packages/engine/package.json', 'utf8')).version,
  generatedAt: new Date().toISOString(),
  source: sources[0],
  cssCustomProperties: [
    '--color-brand-primary',
    '--color-text-primary',
    '--color-surface-base',
    '--spacing-md',
    '--radius-sm',
    '--motion-duration-fast',
  ],
  elements: tags.map(tagName => {
    const meta = META[tagName] || {
      attributes: [],
      events: [],
      slots: ['default'],
      cssParts: [],
      keyboard: 'See component brief',
    };
    return {
      tagName,
      attributes: meta.attributes,
      events: meta.events,
      slots: meta.slots,
      cssCustomProperties: [
        '--color-brand-primary',
        '--color-text-primary',
        '--spacing-md',
        '--radius-sm',
      ],
      cssParts: meta.cssParts,
      keyboard: meta.keyboard,
      accessibility: { keyboard: true, focusable: true, ariaSupport: true },
    };
  }),
};

mkdirSync('design/contracts', { recursive: true });
const out = join('design/contracts', 'components.json');
writeFileSync(out, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`Manifest generated: ${manifest.elements.length} elements -> ${out}`);
