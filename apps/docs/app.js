const cards = [...document.querySelectorAll('.component-card')];
const searchInput = document.querySelector('#search');
const categoryButtons = [...document.querySelectorAll('[data-filter]')];
const count = document.querySelector('#component-count');
const emptyState = document.querySelector('#empty-state');
let category = 'all';

function filterCards() {
  const query = searchInput.value.trim().toLowerCase();
  let visible = 0;
  for (const card of cards) {
    const matches = (category === 'all' || card.dataset.category === category) && `${card.dataset.search} ${card.textContent}`.toLowerCase().includes(query);
    card.hidden = !matches;
    if (matches) visible += 1;
  }
  count.textContent = `${visible} component${visible === 1 ? '' : 's'}`;
  emptyState.hidden = visible > 0;
}

searchInput.addEventListener('input', filterCards);
for (const button of categoryButtons) button.addEventListener('click', () => {
  category = button.dataset.filter;
  categoryButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  filterCards();
});

document.querySelector('#theme').addEventListener('change', event => window.UniversalUI.setTheme(event.target.value));
const dialog = document.querySelector('#demo-dialog');
document.querySelector('#open-dialog').addEventListener('ui-button-click', () => dialog.show());
document.querySelector('#close-dialog').addEventListener('ui-button-click', () => dialog.close());

const select = document.querySelector('#demo-select');
select.options = [
  { label: 'United States East', value: 'us-east' },
  { label: 'Europe West', value: 'eu-west' },
  { label: 'Asia Pacific', value: 'ap-southeast' },
];
document.querySelector('#demo-tabs').items = [
  { id: 'overview', label: 'Overview', content: 'Review your workspace activity and current status.' },
  { id: 'activity', label: 'Activity', content: 'Recent events are available in the activity stream.' },
  { id: 'settings', label: 'Settings', content: 'Workspace settings are managed by your team.' },
];
document.querySelector('#demo-menu').items = [
  { label: 'Edit workspace', value: 'edit', shortcut: '⌘ E' },
  { label: 'Invite a teammate', value: 'invite', shortcut: '⌘ I' },
  { separator: true },
  { label: 'Archive', value: 'archive' },
];
document.querySelector('#show-toast').addEventListener('ui-button-click', () => document.querySelector('#demo-toast').show('Changes saved'));

const inspector = document.querySelector('#inspector');
const tokenList = document.querySelector('#token-list');
const tokenFilter = document.querySelector('#token-filter');
const copyStatus = document.querySelector('#copy-status');
const tokenNameSet = new Set();
for (const sheet of document.styleSheets) {
  try {
    for (const rule of sheet.cssRules) {
      if (!('style' in rule)) continue;
      for (const name of rule.style) if (name.startsWith('--')) tokenNameSet.add(name);
    }
  } catch { /* Cross-origin stylesheets are not inspectable. */ }
}
const tokenNames = [...tokenNameSet].sort();
const computed = getComputedStyle(document.documentElement);
const tokens = tokenNames.map(name => [name, computed.getPropertyValue(name).trim()]).filter(([, value]) => value);

function renderTokens() {
  const query = tokenFilter.value.toLowerCase();
  const filtered = tokens.filter(([name, value]) => `${name} ${value}`.toLowerCase().includes(query));
  tokenList.replaceChildren(...filtered.map(([name, value]) => {
    const row = document.createElement('li');
    const key = document.createElement('code'); key.textContent = name;
    const val = document.createElement('span'); val.textContent = value;
    row.append(key, val);
    return row;
  }));
}

document.querySelector('#inspector-toggle').addEventListener('click', () => { inspector.hidden = false; renderTokens(); tokenFilter.focus(); });
document.querySelector('#inspector-close').addEventListener('click', () => { inspector.hidden = true; document.querySelector('#inspector-toggle').focus(); });
tokenFilter.addEventListener('input', renderTokens);
document.querySelector('#copy-tokens').addEventListener('click', async () => {
  const text = [...tokenList.querySelectorAll('li')].map(row => `${row.querySelector('code').textContent}: ${row.querySelector('span').textContent}`).join('\n');
  try { await navigator.clipboard.writeText(text); copyStatus.textContent = 'Visible tokens copied.'; }
  catch { copyStatus.textContent = 'Clipboard access is unavailable in this browser context.'; }
});

filterCards();
