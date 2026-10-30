#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const manifestPath = join(__dirname, '..', 'design', 'contracts', 'components.json');
const outPath = join(__dirname, '..', 'examples', 'nextjs-consumer', 'uie.generated.d.ts');

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const elements = manifest.elements || [];

function typeFor(attr) {
  if (attr.type === 'boolean') return 'boolean';
  if (attr.type === 'number') return 'number';
  if (attr.enum) return attr.enum.map(v => `'${v}'`).join(' | ');
  return 'string';
}

let attrs = `type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {\n`;
for (const el of elements) {
  for (const attr of el.attributes || []) {
    attrs += `  [key: \`\${string}-\`]: any;\n`;
    break;
  }
  break;
}
// better: generic
attrs = `type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & Record<string, any>;\n`;

let lines = `import type { DetailedHTMLProps, HTMLAttributes } from 'react';\n\n`;
lines += `type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & Record<string, any>;\n\n`;
lines += `declare global {\n  namespace JSX {\n    interface IntrinsicElements {\n`;
for (const el of elements) {
  lines += `      '${el.tagName}': UieProps;\n`;
}
lines += `    }\n  }\n}\n\nexport {};\n`;

writeFileSync(outPath, lines);
console.log('Generated', outPath);
