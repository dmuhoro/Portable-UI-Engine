#!/usr/bin/env node
/**
 * Proves the README quick-start snippet: theme.css + engine bundle register ui-* elements.
 */
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { extname, join } from 'node:path';
import { chromeLauncher } from '@web/test-runner-chrome';
import { setTimeout as delay } from 'node:timers/promises';

const root = process.cwd();
const distEngine = existsSync(join(root, 'dist/engine.js')) ? 'dist/engine.js' : null;
if (!distEngine) {
  console.error('test-quick-start: dist/engine.js missing — run npm run build:engine first');
  process.exit(1);
}
const theme = existsSync(join(root, 'theme.css')) ? 'theme.css' : 'packages/engine/theme.css';

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Quick-start proof</title>
  <link rel="stylesheet" href="/${theme}">
</head>
<body>
  <ui-button variant="primary">Save changes</ui-button>
  <ui-input label="Workspace name" name="workspace"></ui-input>
  <script type="module">
    import '/${distEngine}';
    window.__uieReady = true;
  </script>
</body>
</html>`;

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.map': 'application/json',
};

const server = createServer((req, res) => {
  if (req.url === '/' || req.url === '/index.html') {
    res.writeHead(200, { 'Content-Type': mime['.html'] });
    res.end(html);
    return;
  }
  const rel = decodeURIComponent((req.url || '').replace(/^\//, '').split('?')[0]);
  const path = join(root, rel);
  if (!path.startsWith(root) || !existsSync(path)) {
    res.writeHead(404).end('not found');
    return;
  }
  res.writeHead(200, { 'Content-Type': mime[extname(path)] || 'application/octet-stream' });
  res.end(readFileSync(path));
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const { port } = server.address();
let browser;

try {
  browser = await chromeLauncher({
    launchOptions: { headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] },
  }).launchBrowser();
  const page = await browser.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'domcontentloaded' });

  const deadline = Date.now() + 15000;
  let registered = null;
  while (Date.now() < deadline) {
    registered = await page.evaluate(() => ({
      ready: Boolean(window.__uieReady),
      buttonDefined: Boolean(customElements.get('ui-button')),
      inputDefined: Boolean(customElements.get('ui-input')),
      buttonShadow: Boolean(document.querySelector('ui-button')?.shadowRoot),
      inputShadow: Boolean(document.querySelector('ui-input')?.shadowRoot),
    }));
    if (registered.buttonDefined && registered.inputDefined && registered.buttonShadow && registered.inputShadow) break;
    await delay(200);
  }

  if (!registered?.buttonDefined || !registered?.inputDefined) {
    throw new Error(`Quick-start elements not registered: ${JSON.stringify({ registered, pageErrors })}`);
  }
  if (!registered.buttonShadow || !registered.inputShadow) {
    throw new Error(`Quick-start elements did not render shadow roots: ${JSON.stringify(registered)}`);
  }
  if (pageErrors.length) throw new Error(`Quick-start page errors:\n${pageErrors.join('\n')}`);
  console.log('Quick-start proof passed: README snippet registers and renders ui-button and ui-input.');
} finally {
  if (browser) {
    try { await browser.close(); } catch { /* ignore */ }
  }
  server.close();
}
