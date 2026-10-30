#!/usr/bin/env node
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const manifestPath = join(__dirname, '..', 'design', 'contracts', 'components.json');
const outPath = join(__dirname, '..', 'examples', 'nextjs-consumer', 'uie.generated.d.ts');

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const elements = manifest.elements || [];

let lines = `import type { DetailedHTMLProps, HTMLAttributes } from 'react';\n\n`;
lines += `type UieProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & Record<string, any>;\n\n`;
lines += `declare global {\n  namespace JSX {\n    interface IntrinsicElements {\n`;
for (const el of elements) {
  lines += `      '${el.tagName}': UieProps;\n`;
}
lines += `    }\n  }\n}\n\nexport {};\n`;

const current = readFileSync(outPath, 'utf8');
if (current !== lines) {
  console.error('Consumer types stale. Regenerate with: node scripts/generate-consumer-types.mjs');
  process.exit(1);
}
console.log('Consumer types up to date');
