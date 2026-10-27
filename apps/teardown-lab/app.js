import loadRubric from './rubric-loader.js';

const criteriaRoot = document.querySelector('#criteria');
const form = document.querySelector('#rubric-form');
const savedKey = 'portable-ui-teardown-v1';
let rubric;

function readSaved() {
  try { return JSON.parse(localStorage.getItem(savedKey) || '{}'); }
  catch { return {}; }
}

function renderCriteria(saved) {
  criteriaRoot.replaceChildren();
  for (const criterion of rubric.criteria) {
    const row = document.createElement('div'); row.className = 'criterion';
    const label = document.createElement('label'); label.htmlFor = `score-${criterion.id}`; label.textContent = criterion.name;
    const description = document.createElement('p'); description.textContent = criterion.description || `Rate ${criterion.name.toLowerCase()} based on observed evidence.`;
    const select = document.createElement('select'); select.id = `score-${criterion.id}`; select.name = criterion.id; select.dataset.weight = String(criterion.weight || 1); select.setAttribute('aria-label', `Score ${criterion.name}`);
    for (let value = 0; value <= 4; value += 1) { const option = document.createElement('option'); option.value = String(value); option.textContent = `${value} — ${['Not assessed', 'Needs work', 'Partial', 'Meets', 'Exceeds'][value]}`; select.append(option); }
    select.value = String(saved.scores?.[criterion.id] ?? 0);
    row.append(label, description, select); criteriaRoot.append(row);
  }
  document.querySelector('#evidence').value = saved.evidence || '';
  document.querySelector('#reviewer').value = saved.reviewer || '';
}

function calculate() {
  const selects = [...criteriaRoot.querySelectorAll('select')];
  const scored = selects.filter(input => input.value !== '0').length;
  const totalWeight = selects.reduce((sum, input) => sum + Number(input.dataset.weight), 0);
  const points = selects.reduce((sum, input) => sum + Number(input.value) * Number(input.dataset.weight), 0);
  const percent = totalWeight ? Math.round((points / (totalWeight * 4)) * 100) : 0;
  document.querySelector('#score').textContent = `${percent}%`;
  document.querySelector('#scored-count').textContent = `${scored} / ${selects.length}`;
  document.querySelector('#grade').textContent = scored === 0 ? 'Not yet assessed' : percent >= 90 ? 'Strong evidence' : percent >= 70 ? 'Developing' : 'Needs attention';
  try {
    const scores = Object.fromEntries(selects.map(input => [input.name, input.value]));
    localStorage.setItem(savedKey, JSON.stringify({ scores, evidence: document.querySelector('#evidence').value, reviewer: document.querySelector('#reviewer').value }));
    document.querySelector('#save-status').textContent = 'Saved on this device';
  } catch { document.querySelector('#save-status').textContent = 'Local storage unavailable'; }
}

function toRgb(value) {
  const hex = value.trim().match(/^#([\da-f]{3}|[\da-f]{6})$/i);
  if (hex) {
    const expanded = hex[1].length === 3 ? [...hex[1]].map(part => part + part).join('') : hex[1];
    return [0, 2, 4].map(index => Number.parseInt(expanded.slice(index, index + 2), 16) / 255);
  }
  const parts = value.match(/[\d.]+/g)?.map(Number);
  return parts?.length >= 3 ? parts.slice(0, 3).map(channel => channel / 255) : null;
}

function luminance(rgb) {
  const linear = rgb.map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
}

function updateMeasurements() {
  const root = getComputedStyle(document.documentElement);
  const foreground = toRgb(root.getPropertyValue('--color-text-primary'));
  const background = toRgb(root.getPropertyValue('--color-canvas-default'));
  if (foreground && background) {
    const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
    document.querySelector('#contrast').textContent = `${((values[0] + 0.05) / (values[1] + 0.05)).toFixed(2)}:1`;
  } else document.querySelector('#contrast').textContent = 'Not available';
  const button = document.querySelector('#candidate').querySelector('ui-button').shadowRoot.querySelector('button');
  const bounds = button.getBoundingClientRect();
  document.querySelector('#target-size').textContent = `${Math.round(bounds.width)} × ${Math.round(bounds.height)} px`;
}

rubric = await loadRubric();
const saved = readSaved();
renderCriteria(saved);
calculate();
updateMeasurements();
form.addEventListener('input', calculate);
document.querySelector('#reset').addEventListener('ui-button-click', () => { try { localStorage.removeItem(savedKey); } catch { /* Keep the in-memory reset working. */ } renderCriteria({}); calculate(); });
document.querySelector('#export').addEventListener('click', () => window.print());
document.querySelector('#candidate').addEventListener('ui-button-click', () => { document.querySelector('#candidate-status').textContent = 'Candidate action completed.'; });
document.querySelector('#baseline-button').addEventListener('click', () => { document.querySelector('#baseline-status').textContent = 'Baseline action completed.'; });
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
  document.querySelectorAll('[data-view]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.querySelector('.compare-grid').dataset.view = button.dataset.view;
});
