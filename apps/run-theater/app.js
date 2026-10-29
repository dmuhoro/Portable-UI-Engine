window.UniversalUI.setTheme('technical-oceanic');

const stages = [
  { name: 'Ingestion gateway', state: 'complete', elapsed: '1.2s' },
  { name: 'Schema normalization', state: 'complete', elapsed: '0.4s' },
  { name: 'Vector embeddings', state: 'running', elapsed: '8.9s' },
  { name: 'Model inference', state: 'pending', elapsed: '—' },
  { name: 'Response delivery', state: 'pending', elapsed: '—' },
];
const nodes = [
  { id: 'node-us-01', region: 'us-east-1a', protocol: 'gRPC-Web', cpu: 42.1, memory: '2.4 / 8 GB', jobs: 14, status: 'Operational' },
  { id: 'node-us-02', region: 'us-east-1a', protocol: 'HTTP/2', cpu: 38.6, memory: '2.1 / 8 GB', jobs: 11, status: 'Operational' },
  { id: 'node-us-03', region: 'us-east-1b', protocol: 'gRPC-Web', cpu: 78.4, memory: '6.2 / 8 GB', jobs: 39, status: 'Rebalancing' },
  { id: 'node-eu-01', region: 'eu-west-1a', protocol: 'HTTP/2', cpu: 51.8, memory: '4.1 / 8 GB', jobs: 20, status: 'Operational' },
  { id: 'node-ap-01', region: 'ap-southeast-1', protocol: 'gRPC-Web', cpu: 33.7, memory: '2.8 / 8 GB', jobs: 16, status: 'Operational' },
  { id: 'node-ap-02', region: 'ap-southeast-1', protocol: 'HTTP/2', cpu: 45.2, memory: '3.5 / 8 GB', jobs: 22, status: 'Operational' },
];

function renderStages() {
  const root = document.querySelector('#stages');
  root.replaceChildren(...stages.map((stage, index) => {
    const item = document.createElement('li'); item.className = 'stage'; item.dataset.status = stage.state;
    const number = document.createElement('span'); number.className = 'stage-number'; number.textContent = String(index + 1);
    const name = document.createElement('span'); name.className = 'stage-name'; name.textContent = stage.name;
    const state = document.createElement('span'); state.className = 'stage-state'; state.textContent = `${stage.state.toUpperCase()} · ${stage.elapsed}`;
    item.append(number, name, state);
    if (stage.state === 'running') { const track = document.createElement('span'); track.className = 'progress-track'; track.setAttribute('role', 'progressbar'); track.setAttribute('aria-label', `${stage.name} progress`); track.setAttribute('aria-valuemin', '0'); track.setAttribute('aria-valuemax', '100'); track.setAttribute('aria-valuenow', String(progress)); const fill = document.createElement('span'); fill.style.width = `${progress}%`; track.append(fill); item.append(track); }
    return item;
  }));
}

function renderNodes(query = '') {
  const rows = nodes.filter(node => Object.values(node).join(' ').toLowerCase().includes(query.toLowerCase()));
  document.querySelector('#node-rows').replaceChildren(...rows.map(node => {
    const row = document.createElement('tr');
    for (const value of [node.id, node.region, node.protocol, `${node.cpu.toFixed(1)}%`, node.memory, node.jobs]) { const cell = document.createElement('td'); cell.textContent = String(value); row.append(cell); }
    const statusCell = document.createElement('td'); const status = document.createElement('span'); status.className = 'health'; status.dataset.state = node.status; status.textContent = node.status; statusCell.append(status); row.append(statusCell);
    return row;
  }));
}

const logRoot = document.querySelector('#logs');
const messages = [
  ['INFO', 'Ingestion acknowledged with status 200'],
  ['INFO', 'Batch normalized and schema validated'],
  ['INFO', 'Embedding cache hit rate is stable'],
  ['WARN', 'Node node-us-03 is rebalancing workload'],
  ['INFO', 'Inference stream delivered chunk'],
  ['INFO', 'Autoscaler kept desired node count'],
];
let logCount = 0;
let currentStage = 2;
let progress = 64;
let paused = false;
let halted = false;
let timer;

function appendLog(level, message) {
  const row = document.createElement('div'); row.className = 'log-line'; row.dataset.level = level;
  const time = document.createElement('time'); time.dateTime = new Date().toISOString(); time.textContent = new Date().toLocaleTimeString('en-GB', { hour12: false });
  const severity = document.createElement('strong'); severity.textContent = level;
  const text = document.createElement('span'); text.textContent = message;
  row.append(time, severity, text); logRoot.append(row);
  while (logRoot.children.length > 200) logRoot.firstElementChild.remove();
  logRoot.scrollTop = logRoot.scrollHeight;
}

function tick() {
  if (paused || halted) return;
  const latency = 12 + Math.random() * 6;
  const ingestion = 91 + Math.random() * 7;
  const error = Math.random() * 0.008;
  document.querySelector('#latency').textContent = `${latency.toFixed(1)} ms`;
  document.querySelector('#ingestion').textContent = `${ingestion.toFixed(1)}k ops/s`;
  document.querySelector('#error-rate').textContent = `${error.toFixed(3)}%`;
  progress = Math.min(100, progress + 2);
  renderStages();
  document.querySelector('#progress-label').textContent = `Stage ${currentStage + 1} of 5 · ${progress}%`;
  const [level, message] = messages[logCount % messages.length];
  appendLog(level, `#${String(logCount + 43).padStart(2, '0')} ${message}`);
  logCount += 1;
  if (progress >= 100) {
    stages[currentStage].state = 'complete'; stages[currentStage].elapsed = `${(logCount / 10).toFixed(1)}s`;
    currentStage += 1;
    if (currentStage >= stages.length) {
      halted = true; clearInterval(timer); document.querySelector('#run-state').textContent = 'COMPLETE · SIMULATION';
    } else {
      stages[currentStage].state = 'running'; stages[currentStage].elapsed = '0.1s'; progress = 0;
    }
  }
}

function start() { clearInterval(timer); timer = window.setInterval(tick, 1500); }
renderStages(); renderNodes(); appendLog('INFO', 'Demo telemetry stream initialized'); start();

document.querySelector('#node-search').addEventListener('ui-input-change', event => renderNodes(event.detail.value));
document.querySelector('#clear-logs').addEventListener('click', () => logRoot.replaceChildren());
document.querySelector('#pause').addEventListener('click', event => {
  if (halted) return;
  paused = !paused; event.currentTarget.textContent = paused ? 'Resume stream' : 'Pause stream';
  document.querySelector('#run-state').textContent = paused ? 'PAUSED · SIMULATION' : 'RUNNING · SIMULATION';
  if (!paused) start(); else clearInterval(timer);
});

const dialog = document.querySelector('#halt-dialog');
document.querySelector('#halt').addEventListener('ui-button-click', () => dialog.show());
document.querySelector('#cancel-halt').addEventListener('ui-button-click', () => dialog.close());
document.querySelector('#confirm-halt').addEventListener('ui-button-click', () => {
  halted = true; paused = true; clearInterval(timer); dialog.close();
  document.querySelector('#run-state').textContent = 'HALTED · SIMULATION';
  document.querySelector('#pause').disabled = true;
  document.querySelector('#halt').setAttribute('disabled', '');
  stages.forEach(stage => { if (stage.state === 'running') stage.state = 'stopped'; });
  renderStages(); appendLog('WARN', 'Simulation halted by operator');
});
