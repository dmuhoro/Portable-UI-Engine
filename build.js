/**
 * build.js
 * Open-Source Build Script for @universal-ui/engine
 * Bundles and minifies engine.js into dist/engine.min.js using esbuild.
 */

import { build } from 'esbuild';
import { mkdirSync, existsSync } from 'fs';
import path from 'path';

async function runBuild() {
  console.log('🚀 Starting @universal-ui/engine build process...');

  const distDir = path.resolve('dist');
  if (!existsSync(distDir)) {
    mkdirSync(distDir, { recursive: true });
  }

  try {
    const result = await build({
      entryPoints: ['engine.js'],
      outfile: 'dist/engine.min.js',
      bundle: true,
      minify: true,
      sourcemap: true,
      format: 'esm',
      target: ['es2020', 'chrome80', 'firefox78', 'safari14'],
      banner: {
        js: '/* @universal-ui/engine v2.0.0 | MIT License | Portable UI Engine */'
      },
      metafile: true
    });

    console.log('✅ Build completed successfully!');
    console.log('📦 Output file: dist/engine.min.js');
  } catch (error) {
    console.error('❌ Build failed with error:', error);
    process.exit(1);
  }
}

runBuild();
