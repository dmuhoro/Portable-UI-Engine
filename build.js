/**
 * build.js
 * Open-Source Build Script for @universal-ui/engine
 * Bundles engine.js into both ESM (dist/engine.js) and Minified IIFE (dist/engine.min.js) formats.
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
    // 1. Standard ES Module Build for Framework Bundlers
    console.log('📦 Building dist/engine.js (ESM Module)...');
    await build({
      entryPoints: ['engine.js'],
      outfile: 'dist/engine.js',
      bundle: true,
      minify: false,
      sourcemap: true,
      format: 'esm',
      target: ['es2020', 'chrome80', 'firefox78', 'safari14'],
      banner: {
        js: '/* @universal-ui/engine v2.0.0 | ESM Module Build | MIT License */'
      }
    });

    // 2. Minified IIFE Build for CDN Script Tag Injection
    console.log('⚡ Building dist/engine.min.js (Minified IIFE CDN)...');
    await build({
      entryPoints: ['engine.js'],
      outfile: 'dist/engine.min.js',
      bundle: true,
      minify: true,
      sourcemap: true,
      format: 'iife',
      globalName: 'UniversalUIEngine',
      target: ['es2020', 'chrome80', 'firefox78', 'safari14'],
      banner: {
        js: '/* @universal-ui/engine v2.0.0 | Minified IIFE CDN Build | MIT License */'
      }
    });

    console.log('✅ Build completed successfully!');
    console.log('  ➜ dist/engine.js (ESM)');
    console.log('  ➜ dist/engine.min.js (Minified IIFE)');
  } catch (error) {
    console.error('❌ Build failed with error:', error);
    process.exit(1);
  }
}

runBuild();
