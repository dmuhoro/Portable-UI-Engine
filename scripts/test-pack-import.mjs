#!/usr/bin/env node
/**
 * Packs packages/engine, installs the tarball into a temp project, serves the
 * installed ESM bundle, and asserts ui-* elements register in Chrome.
 */
import { mkdtempSync, writeFileSync, readFileSync, rmSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { chromeLauncher } from '@web/test-runner-chrome';
import { setTimeout as delay } from 'node:timers/promises';

function run(command, args, opts = {}) {
  const result = spawnSync(command, args, { encoding: 'utf8', ...opts });
  if (result.status !== 0) {
    console.error(result.stdout);
    console.error(result.stderr);
    throw new Error(`${command} ${args.join(' ')} failed with ${result.status}`);
  }
  return result;
}

const root = process.cwd();
run(process.execPath, ['build.js'], { cwd: root });

const packDir = mkdtempSync(join(tmpdir(), 'uie-pack-'));
const consumerDir = mkdtempSync(join(tmpdir(), 'uie-consumer-'));
let browser;
let server;

try {
  run('npm', ['pack', '--pack-destination', packDir], { cwd: join(root, 'packages/engine') });
  const tgz = readdirSync(packDir).find(name => name.endsWith('.tgz'));
  if (!tgz) throw new Error('npm pack did not produce a tarball');
  const tarballPath = join(packDir, tgz);

  writeFileSync(join(consumerDir, 'package.json'), JSON.stringify({
    name: 'uie-pack-consumer',
    private: true,
    type: 'module',
  }, null, 2));
  run('npm', ['install', tarballPath], { cwd: consumerDir });

  const installed = join(consumerDir, 'node_modules', '@universal-ui', 'engine');
  const pkg = JSON.parse(readFileSync(join(installed, 'package.json'), 'utf8'));
  if (!pkg.exports?.['.']?.import) throw new Error('Installed package missing exports["."].import');
  if (!existsSync(join(installed, 'dist/engine.js'))) throw new Error('Installed package missing dist/engine.js');
  if (!existsSync(join(installed, 'theme.css'))) throw new Error('Installed package missing theme.css');

  const html = `<!doctype html><html><head>
<link rel="stylesheet" href="/node_modules/@universal-ui/engine/theme.css">
</head><body>
<ui-button>Pack</ui-button>
<ui-input label="Pack"></ui-input>
<ui-dialog></ui-dialog>
<ui-tabs></ui-tabs>
<script type="module">
  import '/node_modules/@universal-ui/engine/dist/engine.js';
  window.__uiePacked = true;
</script>
</body></html>`;
  writeFileSync(join(consumerDir, 'index.html'), html);

  server = createServer((req, res) => {
    const rel = decodeURIComponent((req.url || '/').split('?')[0].replace(/^\//, '')) || 'index.html';
    const path = join(consumerDir, rel);
    if (!path.startsWith(consumerDir) || !existsSync(path)) {
      res.writeHead(404).end('missing');
      return;
    }
    const type = path.endsWith('.js') ? 'text/javascript'
      : path.endsWith('.css') ? 'text/css'
      : path.endsWith('.html') ? 'text/html' : 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type });
    res.end(readFileSync(path));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();

  browser = await chromeLauncher({
    launchOptions: { headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] },
  }).launchBrowser();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'domcontentloaded' });

  const required = ['ui-button', 'ui-input', 'ui-checkbox', 'ui-select', 'ui-dialog', 'ui-tooltip', 'ui-toast', 'ui-tabs', 'ui-menu'];
  const deadline = Date.now() + 20000;
  let result = null;
  while (Date.now() < deadline) {
    result = await page.evaluate(tags => ({
      packed: Boolean(window.__uiePacked),
      missing: tags.filter(tag => !customElements.get(tag)),
      buttonShadow: Boolean(document.querySelector('ui-button')?.shadowRoot),
    }), required);
    if (result.missing.length === 0 && result.buttonShadow) break;
    await delay(200);
  }

  if (!result || result.missing.length) throw new Error(`Packed import missing: ${JSON.stringify({ result, errors })}`);
  if (!result.buttonShadow) throw new Error('Packed ui-button did not attach a shadow root');
  if (errors.length) throw new Error(`Packed import page errors:\n${errors.join('\n')}`);
  console.log(`test-pack: PASS (${tgz})`);
} finally {
  if (browser) {
    try { await browser.close(); } catch { /* ignore */ }
  }
  if (server) server.close();
  rmSync(packDir, { recursive: true, force: true });
  rmSync(consumerDir, { recursive: true, force: true });
}
