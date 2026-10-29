import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const tokens = JSON.parse(readFileSync(join(root, 'design-tokens.json'), 'utf8'));

function flatten(obj, prefix = '') {
  let result = {};
  for (const key in obj) {
    if (key === '$value' || key === '$type' || key === '$schema') continue;
    const value = obj[key];
    const newKey = prefix ? `${prefix}-${key}` : key;
    if (value && typeof value === 'object') {
      if ('$value' in value) {
        result[newKey] = value.$value;
      } else {
        Object.assign(result, flatten(value, newKey));
      }
    }
  }
  return result;
}

const flat = flatten(tokens);
mkdirSync(join(root, 'css'), { recursive: true });
mkdirSync(join(root, 'ts'), { recursive: true });

let css = ':root {\n';
for (const [k, v] of Object.entries(flat)) {
  css += `  --color-${k.replace('color-', '')}: ${v};\n`.replace('color-color-', 'color-');
  // Better mapping
}
css = ':root {\n';
for (const [k, v] of Object.entries(flat)) {
  if (k.startsWith('color-')) {
    css += `  --${k.replace('color-', 'color-')}: ${v};\n`;
  } else if (k.startsWith('spacing-')) {
    css += `  --space-${k.split('-')[1]}: ${v};\n`;
  } else if (k.startsWith('radius-')) {
    css += `  --radius-${k.split('-')[1]}: ${v};\n`;
  } else if (k.startsWith('typography-')) {
    if (k.includes('font')) css += `  --font-sans: ${v};\n`;
    else if (k.includes('size')) css += `  --text-${k.split('size')[1].toLowerCase() || 'base'}: ${v};\n`;
  }
}
css += '}\n';
writeFileSync(join(root, 'css/variables.css'), css);

let ts = 'export const tokens = {\n';
for (const [k, v] of Object.entries(flat)) {
  ts += `  '${k}': '${v}',\n`;
}
ts += '} as const;\n\nexport type TokenKey = keyof typeof tokens;\n';
writeFileSync(join(root, 'ts/tokens.ts'), ts);

console.log('Tokens built');
