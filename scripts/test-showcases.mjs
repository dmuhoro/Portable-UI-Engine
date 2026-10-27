import { spawn } from 'node:child_process';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { puppeteerCore } from '@web/test-runner-chrome';

const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], { stdio: 'ignore' });
let browser;
const failures = [];

try {
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try { await fetch('http://127.0.0.1:4173/'); ready = true; break; }
    catch { await delay(250); }
  }
  if (!ready) throw new Error('Vite showcase server did not start.');
  browser = await puppeteerCore.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });

  async function checkAccessibility(page, route) {
    const violations = await page.evaluate(async () => {
      const result = await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } });
      return result.violations.map(issue => `${issue.id}: ${issue.nodes.map(node => `${node.target.join(' ')} ${node.failureSummary || ''}`).join('\n')}`);
    });
    if (violations.length) throw new Error(`${route} accessibility violations:\n${violations.join('\n')}`);
  }

  async function pageAt(route, check) {
    const page = await browser.newPage();
    page.on('pageerror', error => failures.push(`${route}: ${error.message}`));
    page.on('console', message => { if (message.type() === 'error') failures.push(`${route}: ${message.text()}`); });
    await page.goto(`http://127.0.0.1:4173${route}`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => window.UniversalUI?.getRegisteredComponents().includes('ui-button'));
    await page.addScriptTag({ path: path.resolve('node_modules/axe-core/axe.min.js') });
    await checkAccessibility(page, route);
    await check(page);
    await page.close();
  }

  await pageAt('/apps/docs/', async page => {
    await page.waitForSelector('.component-card');
    if (await page.$eval('.component-card', card => card.hidden)) throw new Error('Component gallery failed to render.');
    await page.type('#search', 'dialog');
    if (await page.$$eval('.component-card:not([hidden])', cards => cards.length) !== 1) throw new Error('Gallery search did not filter results.');
    await page.click('#inspector-toggle');
    if (await page.$eval('#token-list', list => list.children.length) === 0) throw new Error('Token inspector did not load generated tokens.');
    await page.click('#inspector-close');
    await page.select('#theme', 'technical-oceanic');
    if (await page.$eval('html', element => element.dataset.theme) !== 'technical-oceanic') throw new Error('Theme switch did not update the active theme.');
    await new Promise(resolve => setTimeout(resolve, 250));
    await checkAccessibility(page, '/apps/docs/ (Technical Oceanic)');
    await page.select('#theme', 'swiss-minimalist');
    await new Promise(resolve => setTimeout(resolve, 250));
    await checkAccessibility(page, '/apps/docs/ (Swiss Minimalist)');
    await page.select('#theme', 'warm-precision');
    await page.click('#search', { clickCount: 3 });
    await page.keyboard.press('Backspace');
    await page.click('#open-dialog');
    if (!(await page.$eval('#demo-dialog', element => element.shadowRoot.querySelector('dialog').open))) throw new Error('Dialog did not open from its trigger.');
    await page.click('#close-dialog');
    await page.click('#show-toast');
    if (await page.$eval('#demo-toast', element => element.hidden)) throw new Error('Toast did not appear.');
  });

  await pageAt('/apps/teardown-lab/', async page => {
    await page.waitForSelector('.criterion select');
    await page.select('.criterion select', '4');
    if (await page.$eval('#score', node => node.textContent) === '0%') throw new Error('Rubric score did not recalculate.');
    const dimensions = await page.$eval('#candidate ui-button', host => { const button = host.shadowRoot.querySelector('button').getBoundingClientRect(); return { height: button.height, width: button.width }; });
    if (dimensions.height < 44) throw new Error('Candidate button target is below the documented touch target.');
    if ((await page.$eval('#contrast', node => node.textContent)).includes('Measuring')) throw new Error('Contrast sample did not calculate.');
  });

  await pageAt('/apps/run-theater/', async page => {
    await page.waitForSelector('#node-rows tr');
    await page.click('#pause');
    if (!(await page.$eval('#run-state', node => node.textContent.includes('PAUSED')))) throw new Error('Run Theater pause control failed.');
    await page.click('#halt');
    await page.click('#confirm-halt');
    if (!(await page.$eval('#run-state', node => node.textContent.includes('HALTED')))) throw new Error('Run Theater halt action failed.');
    await page.$eval('#node-search', host => host.shadowRoot.querySelector('input').focus());
    await page.keyboard.type('node-eu');
    if (await page.$$eval('#node-rows tr', rows => rows.length) !== 1) throw new Error('Node search did not filter rows.');
  });

  if (failures.length) throw new Error(failures.join('\n'));
  console.log('Showcase browser checks passed: docs gallery, theme/token inspector, teardown rubric, and run theater.');
} finally {
  if (browser) await browser.close();
  server.kill('SIGTERM');
}
