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
        const cssKey = prefix ? `${prefix}-${key}` : key;
        result[cssKey] = val.$value;
      } else {
        Object.assign(result, extractVars(val, prefix ? `${prefix}-${key}` : key));
      }
    }
  }
  return result;
}

const vars = extractVars(tokens);
mkdirSync(join(root, 'css'), { recursive: true });
mkdirSync(join(root, 'ts'), { recursive: true });

let css = ':root {\n';
for (const [k, v] of Object.entries(vars)) {
  // Map to semantic names
  if (k.includes('brand-primary')) css += `  --color-primary: ${v};\n`;
  else if (k.includes('brand-primaryHover')) css += `  --color-primary-hover: ${v};\n`;
  else if (k.includes('surface-background')) css += `  --color-bg: ${v};\n`;
  else if (k.includes('surface-panel')) css += `  --color-panel: ${v};\n`;
  else if (k.includes('text-primary')) css += `  --color-text: ${v};\n`;
  else if (k.includes('text-secondary')) css += `  --color-text-secondary: ${v};\n`;
  else if (k.includes('border')) css += `  --color-border: ${v};\n`;
  else if (k.includes('success')) css += `  --color-success: ${v};\n`;
  else if (k.includes('warning')) css += `  --color-warning: ${v};\n`;
  else if (k.includes('danger')) css += `  --color-danger: ${v};\n`;
  else if (k.includes('spacing-')) {
    const size = k.split('-')[1];
    css += `  --space-${size}: ${v};\n`;
  } else if (k.includes('radius-')) {
    const size = k.split('-')[1];
    css += `  --radius-${size}: ${v};\n`;
  } else if (k.includes('typography-fontSans')) css += `  --font-sans: ${v};\n`;
  else if (k.includes('typography-sizeBase')) css += `  --text-base: ${v};\n`;
  else if (k.includes('typography-sizeSm')) css += `  --text-sm: ${v};\n`;
  else if (k.includes('typography-sizeLg')) css += `  --text-lg: ${v};\n`;
}
css += '}\n';
writeFileSync(join(root, 'css/variables.css'), css);

// Update root theme.css to reference tokens
const themeHeader = `/* Generated from packages/tokens/design-tokens.json */\n`;
writeFileSync(join(root, '..', '..', 'theme.css'), themeHeader + css + '\n' + readFileSync(join(root, '..', '..', 'theme.css'), 'utf8').split('\n').slice(1).join('\n'));

let ts = `export const cssVariables = {\n`;
for (const [k, v] of Object.entries(vars)) {
  ts += `  '${k}': '${v}',\n`;
}
ts += '} as const;\n\nexport const tokens = cssVariables;\nexport type TokenKey = keyof typeof cssVariables;\n';
writeFileSync(join(root, 'ts/tokens.ts'), ts);

console.log('Tokens built successfully');
