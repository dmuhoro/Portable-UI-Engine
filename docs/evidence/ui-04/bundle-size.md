# Bundle Size Measurements

**Date:** 2026-10-28T12:59:40.000Z  
**Method:** Measured raw bytes and gzip-compressed bytes using Node.js zlib.gzipSync() with default compression level

## Results

| Bundle | Raw Size | Gzip Size |
| --- | --- | --- |
| dist/engine.js | 126.61 KB | 23.85 KB |
| dist/engine.min.js | 102.71 KB | 20.77 KB |
| packages/engine/dist/engine.js | 141.46 KB | 26.17 KB |
| packages/engine/dist/engine.min.js | 115.18 KB | 22.94 KB |

## Notes
- Sizes measured from built artifacts (after `npm run build` and `npm run build:engine`)
- Method is reproducible via `node scripts/measure-bundles.mjs`
- Root dist bundles are smaller due to different build configuration
