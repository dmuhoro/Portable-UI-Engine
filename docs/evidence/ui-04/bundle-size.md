# Bundle Size Measurements

**Date:** 2026-10-28T13:00:35.233Z  
**Method:** Measured raw bytes and gzip-compressed bytes using Node.js zlib.gzipSync()

## Results

| Bundle | Raw Size | Gzip Size |
| --- | --- | --- |
| ./dist/engine.js | 126.61 KB | 23.85 KB |
| ./dist/engine.min.js | 102.71 KB | 20.77 KB |
| ./packages/engine/dist/engine.js | 141.46 KB | 26.17 KB |
| ./packages/engine/dist/engine.min.js | 115.18 KB | 22.94 KB |
| ./packages/engine/engine.js | 3.73 KB | 1.48 KB |

## Notes
- Sizes measured from built artifacts
- Gzip compression level: default (level 6)
- Method is reproducible via `node scripts/measure-bundles.mjs`
