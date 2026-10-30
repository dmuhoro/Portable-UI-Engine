/** Build the root distribution and the standalone packages/engine workspace package. */
import { build } from 'esbuild';
import { mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

const targets = [path.resolve('.'), path.resolve('packages/engine')];

async function buildTarget(directory) {
  const packageJson = JSON.parse(readFileSync(path.join(directory, 'package.json'), 'utf8'));
  const dist = path.join(directory, 'dist');
  mkdirSync(dist, { recursive: true });
  const bannerEsm = `/* @universal-ui/engine v${packageJson.version} | MIT License | ESM */`;
  const bannerIife = `/* @universal-ui/engine v${packageJson.version} | MIT License | IIFE */`;
  await build({
    absWorkingDir: directory,
    entryPoints: ['engine.js'],
    outfile: path.join(dist, 'engine.js'),
    bundle: true,
    minify: false,
    sourcemap: true,
    format: 'esm',
    target: ['es2020', 'chrome80', 'firefox78', 'safari14'],
    banner: { js: bannerEsm },
  });
  await build({
    absWorkingDir: directory,
    entryPoints: ['engine.js'],
    outfile: path.join(dist, 'engine.min.js'),
    bundle: true,
    minify: true,
    sourcemap: true,
    format: 'iife',
    globalName: 'UniversalUIEngine',
    target: ['es2020', 'chrome80', 'firefox78', 'safari14'],
    banner: { js: bannerIife },
  });
}

for (const target of targets) await buildTarget(target);
console.log('Built root and standalone engine distributions.');
