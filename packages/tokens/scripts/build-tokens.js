import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const tokens = JSON.parse(readFileSync(join(root, 'design-tokens.json'), 'utf8'));

function extractVars(obj, prefix = '') {
  const result = {};
  for (const key in obj) {
    if (key.startsWith('$')) continue;
    const val = obj[key];
    if (val && typeof val === 'object') {
      if ('$value' in val) {
        result[prefix ? prefix + '-' + key : key] = val.$value;
      } else {
        Object.assign(result, extractVars(val, prefix ? prefix + '-' + key : key));
      }
    }
  }
  return result;
}

const vars = extractVars(tokens);
mkdirSync(join(root, 'css'), { recursive: true });
mkdirSync(join(root, 'ts'), { recursive: true });

// Mapping from flattened token keys to CSS custom properties
const cssMap = {
  'color-brand-primary': '--color-primary',
  'color-brand-primaryHover': '--color-primary-hover',
  'color-surface-background': '--color-bg',
  'color-surface-panel': '--color-panel',
  'color-text-primary': '--color-text',
  'color-text-secondary': '--color-text-secondary',
  'color-border': '--color-border',
  'color-success': '--color-success',
  'color-warning': '--color-warning',
  'color-danger': '--color-danger',
};

// Generate CSS
let css = ':root {\n';
for (const [k, v] of Object.entries(vars)) {
  const mapped = cssMap[k] || null;
  if (mapped) {
    css += `  ${mapped}: ${v};\n`;
  } else if (k.startsWith('spacing-')) {
    const size = k.split('-')[1];
    css += `  --space-${size}: ${v};\n`;
  } else if (k.startsWith('radius-')) {
    const size = k.split('-')[1];
    css += `  --radius-${size}: ${v};\n`;
  } else if (k.startsWith('typography-fontSans')) {
    css += `  --font-sans: ${v};\n`;
  } else if (k.startsWith('typography-sizeBase')) {
    css += `  --text-base: ${v};\n`;
  } else if (k.startsWith('typography-sizeSm')) {
    css += `  --text-sm: ${v};\n`;
  } else if (k.startsWith('typography-sizeLg')) {
    css += `  --text-lg: ${v};\n`;
  }
}
css += '}\n';
writeFileSync(join(root, 'css/variables.css'), css);

// Generate TypeScript
let ts = 'export const cssVariables = {\n';
for (const [k, v] of Object.entries(vars)) {
  ts += `  '${k}': '${v}',\n`;
}
ts += '} as const;\n\nexport const tokens = cssVariables;\nexport type TokenKey = keyof typeof cssVariables;\n';
writeFileSync(join(root, 'ts/tokens.ts'), ts);

console.log('Tokens built successfully');
