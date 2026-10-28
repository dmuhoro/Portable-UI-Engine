#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join } from 'node:path';

const bundles = [
  'dist/engine.js',
  'dist/engine.min.js',
  'packages/engine/dist/engine.js',
  'packages/engine/dist/engine.min.js',
];

mkdirSync('docs/evidence/ui-04', { recursive: true });

const results = [];
for (const bundle of bundles) {
  try {
    const content = readFileSync(bundle);
    const raw = content.length;
    const gzip = gzipSync(content).length;
    results.push({ bundle, raw, gzip, rawKB: (raw/1024).toFixed(2), gzipKB: (gzip/1024).toFixed(2) });
    console.log(`${bundle}: ${rawKB}KB raw, ${gzipKB}KB gzip`);
  } catch (e) {
    console.log(`${bundle}: NOT FOUND`);
    results.push({ bundle, error: e.message });
  }
}

const report = `# Bundle Size Measurements

**Date:** ${new Date().toISOString()}  
**Method:** Measured raw bytes and gzip-compressed bytes using Node.js zlib.gzipSync()

## Results

| Bundle | Raw Size | Gzip Size |
| --- | --- | --- |
${results.filter(r => !r.error).map(r => `| ${r.bundle} | ${r.rawKB} KB | ${r.gzipKB} KB |`).join('\n')}

## Notes
- Sizes measured from built artifacts
- Gzip compression level: default (level 6)
- Method is reproducible via \`node scripts/measure-bundles.mjs\`
`;
writeFileSync('docs/evidence/ui-04/bundle-size.md', report);
console.log('\nWrote docs/evidence/ui-04/bundle-size.md');
