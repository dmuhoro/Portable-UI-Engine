import { readFileSync } from 'node:fs';

const readJson = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const appSource = readFileSync(new URL('../src/lib/constants.ts', import.meta.url), 'utf8');
const engineSource = readFileSync(new URL('../engine.js', import.meta.url), 'utf8');
const packageEngineSource = readFileSync(new URL('../packages/engine/engine.js', import.meta.url), 'utf8');
const appVersion = appSource.match(/VERSION:\s*'([^']+)'/)?.[1];
const engineVersion = engineSource.match(/version:\s*'([^']+)'/)?.[1];
const packageEngineVersion = packageEngineSource.match(/version:\s*'([^']+)'/)?.[1];
const rootPackage = readJson('../package.json');
const lockfile = readJson('../package-lock.json');
const enginePackage = readJson('../packages/engine/package.json');
const versions = {
  'APP.VERSION': appVersion,
  'UniversalUI.version': engineVersion,
  'packages/engine/engine.js': packageEngineVersion,
  'package.json': rootPackage.version,
  'package-lock.json': lockfile.version,
  'package-lock packages[""]': lockfile.packages?.['']?.version,
  'packages/engine/package.json': enginePackage.version,
};
const distinct = new Set(Object.values(versions));
if (distinct.size !== 1 || distinct.has(undefined)) {
  throw new Error(`Release version mismatch: ${JSON.stringify(versions)}`);
}
console.log(`Version metadata consistent: ${appVersion}`);
