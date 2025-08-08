let cy;
const LAYOUTS = {
  'vpc': { name: 'cose-bilkent', quality: 'proof', animate: false, nodeRepulsion: 60000, idealEdgeLength: 200, gravity: 0.25, numIter: 1000, tile: true },
  'service': { name: 'dagre', rankDir: 'LR', nodeSep: 50, rankSep: 100, edgeSep: 20, fit: true },
  'account': { name: 'dagre', rankDir: 'TB', nodeSep: 50, rankSep: 100, edgeSep: 20, fit: true },
};

const NODE_STYLES = [
  { sel: 'node', style: { 'label': 'data(label)', 'font-size': 10, 'text-wrap': 'wrap', 'text-max-width': 160, 'background-color': '#9ca3af', 'shape': 'ellipse', 'border-width': 1, 'border-color': '#334155' } },
  { sel: 'node[type = "vpc"]', style: { 'shape': 'round-rectangle', 'background-color': '#16a34a', 'background-opacity': 0.08, 'border-width': 2 } },
  { sel: 'node[type = "subnet"]', style: { 'shape': 'round-rectangle', 'background-color': '#22c55e' } },
  { sel: 'node[type = "instance"]', style: { 'shape': 'round-rectangle', 'background-color': '#10b981' } },
  { sel: 'node[type = "security_group"]', style: { 'shape': 'hexagon', 'background-color': '#a855f7' } },
  { sel: 'node[type = "route_table"]', style: { 'shape': 'round-rectangle', 'background-color': '#15803d' } },
  { sel: 'node[type = "igw"]', style: { 'shape': 'triangle', 'background-color': '#ef4444' } },
  { sel: 'node[type = "nat_gateway"]', style: { 'shape': 'triangle', 'background-color': '#f59e0b' } },
  { sel: 'node[type = "eni"]', style: { 'shape': 'ellipse', 'background-color': '#64748b' } },
  { sel: 'node[type = "load_balancer"]', style: { 'shape': 'round-rectangle', 'background-color': '#0ea5e9' } },
  { sel: 'node[type = "target_group"]', style: { 'shape': 'round-rectangle', 'background-color': '#6366f1' } },
  { sel: 'node[type = "lambda"]', style: { 'shape': 'diamond', 'background-color': '#fb7185' } },
  { sel: 'node[type = "api_gw"], node[type = "api_gw_v2"]', style: { 'shape': 'round-rectangle', 'background-color': '#f97316' } },
  { sel: 'node[type = "rds_instance"]', style: { 'shape': 'round-rectangle', 'background-color': '#1d4ed8' } },
  { sel: 'node[type = "dynamodb_table"]', style: { 'shape': 'round-rectangle', 'background-color': '#6366f1' } },
  { sel: 'node[type = "sqs_queue"]', style: { 'shape': 'round-rectangle', 'background-color': '#06b6d4' } },
  { sel: 'node[type = "sns_topic"]', style: { 'shape': 'round-rectangle', 'background-color': '#14b8a6' } },
  { sel: 'node[type = "kinesis_stream"]', style: { 'shape': 'round-rectangle', 'background-color': '#0ea5e9' } },
  { sel: 'node[type = "ecs_cluster"], node[type = "ecs_service"]', style: { 'shape': 'round-rectangle', 'background-color': '#ef43ba' } },
  { sel: 'node[type = "ecr_repo"]', style: { 'shape': 'round-rectangle', 'background-color': '#ff8fab' } },
  { sel: 'node[type = "cloudfront"]', style: { 'shape': 'round-rectangle', 'background-color': '#94a3b8' } },
  { sel: 'node[type = "route53_zone"]', style: { 'shape': 'round-rectangle', 'background-color': '#94a3b8' } },
  { sel: 'node[type = "opensearch"]', style: { 'shape': 'round-rectangle', 'background-color': '#0ea5e9' } },
  { sel: 'node[type = "elasticache"]', style: { 'shape': 'round-rectangle', 'background-color': '#ef4444' } },
  { sel: 'node[type = "msk_cluster"]', style: { 'shape': 'round-rectangle', 'background-color': '#f59e0b' } },
  { sel: 'node[type = "s3_bucket"]', style: { 'shape': 'round-rectangle', 'background-color': '#84cc16' } },
  { sel: 'node[type = "cidr"], node[type = "prefix_list"], node[type = "external"]', style: { 'shape': 'ellipse', 'background-color': '#e5e7eb' } },
  { sel: 'node:selected', style: { 'border-color': '#111827', 'border-width': 3 } },
];

const EDGE_STYLES = [
  { sel: 'edge', style: { 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'arrow-scale': 0.8, 'width': 2, 'label': 'data(label)', 'font-size': 9 } },
  { sel: 'edge[category = "resource"]', style: { 'line-color': '#2563eb', 'target-arrow-color': '#2563eb' } },
  { sel: 'edge[category = "network"]', style: { 'line-color': '#f97316', 'target-arrow-color': '#f97316' } },
  { sel: 'edge[category = "data"]', style: { 'line-color': '#0ea5e9', 'target-arrow-color': '#0ea5e9', 'line-style': 'dotted' } },
  { sel: 'edge[derived = "true"]', style: { 'line-style': 'dashed' } },
  { sel: 'edge[type = "attach"], edge[type = "assoc"]', style: { 'opacity': 0.45 } },
  { sel: 'edge:selected', style: { 'width': 3 } },
];

function initCy() {
  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [],
    wheelSensitivity: 0.05,
    minZoom: 0.2,
    maxZoom: 3,
    style: [
      ...NODE_STYLES.map(s => ({ selector: s.sel, style: s.style })),
      ...EDGE_STYLES.map(s => ({ selector: s.sel, style: s.style })),
    ],
    layout: LAYOUTS['vpc'],
  });
  cy.minimap({});
  cy.on('select', 'node,edge', (e) => {
    const d = e.target.data();
    document.getElementById('panel').innerHTML = '<pre>' + JSON.stringify(d, null, 2) + '</pre>';
  });
  cy.on('unselect', () => {
    document.getElementById('panel').innerHTML = '<div class="small">Select a node or edge to see details.</div>';
  });
}

function setMeta(text){ document.getElementById('meta').textContent = text; }
function setStatus(text){ document.getElementById('status').textContent = text; }
function addWarnings(ws){
  const el = document.getElementById('warnings'); el.innerHTML = '';
  (ws||[]).forEach(w => { const d = document.createElement('div'); d.className='warn'; d.textContent=w; el.appendChild(d); });
}
function addFindings(fs){
  const el = document.getElementById('findings'); el.innerHTML = '';
  (fs||[]).forEach(f => {
    const d = document.createElement('div'); d.className='finding ' + (f.severity || 'Info').toLowerCase();
    d.textContent = '[' + f.severity + '] ' + f.title + (f.detail ? (': ' + f.detail) : '');
    el.appendChild(d);
  });
}

async function enumerate(){
  setStatus('Enumerating…');
  addWarnings([]); addFindings([]);
  const regionsRaw = document.getElementById('regions').value.trim();
  const payload = {
    profile: document.getElementById('profile').value.trim() || null,
    access_key_id: document.getElementById('ak').value.trim() || null,
    secret_access_key: document.getElementById('sk').value.trim() || null,
    session_token: document.getElementById('st').value.trim() || null,
    assume_roles: (document.getElementById('roles').value.trim() || '').split(',').map(s => s.trim()).filter(Boolean),
    regions: regionsRaw.toUpperCase() === 'ALL' ? ['ALL'] : (regionsRaw ? regionsRaw.split(',').map(s => s.trim()) : []),
    services: {},
  };
  const res = await fetch('/enumerate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await res.json();
  if (!res.ok) { setStatus(data.error || 'Error'); return; }

  setMeta('Elements: ' + (data.elements?.length || 0));
  cy.elements().remove();
  cy.add(data.elements || []);
  applyToggles(); runLayout(); cy.fit(null, 50);
  addWarnings(data.warnings || []);
  addFindings(data.findings || []);
  setStatus('Done');
}

function runLayout(){
  const mode = document.querySelector('input[name="view"]:checked').value;
  cy.layout(LAYOUTS[mode]).run();
}

function applyToggles(){
  const showNetwork = document.getElementById('toggle-network').checked;
  const showResource = document.getElementById('toggle-resource').checked;
  const showData = document.getElementById('toggle-data').checked;
  cy.edges('[category = "network"]').style('display', showNetwork ? 'element' : 'none');
  cy.edges('[category = "resource"]').style('display', showResource ? 'element' : 'none');
  cy.edges('[category = "data"]').style('display', showData ? 'element' : 'none');
}

function bindUI(){
  document.getElementById('run').addEventListener('click', enumerate);
  document.getElementById('fit').addEventListener('click', () => cy.fit(null, 50));
  document.getElementById('layout').addEventListener('click', runLayout);
  document.getElementById('quick-sg').addEventListener('click', () => { document.getElementById('regions').value = 'ap-southeast-1'; });
  document.getElementById('quick-all').addEventListener('click', () => { document.getElementById('regions').value = 'ALL'; });
  ['toggle-network','toggle-resource','toggle-data'].forEach(id => document.getElementById(id).addEventListener('change', applyToggles));

  document.getElementById('export-png').addEventListener('click', () => {
    const png = cy.png({ full: true });
    downloadDataURL(png, 'topology.png');
  });
  document.getElementById('export-svg').addEventListener('click', () => {
    const svg = cy.svg({ full: true });
    downloadText(svg, 'topology.svg');
  });
  document.getElementById('export-json').addEventListener('click', () => {
    const data = { elements: cy.json().elements };
    downloadText(JSON.stringify(data, null, 2), 'topology.json');
  });

  document.getElementById('search').addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    cy.nodes().removeClass('dim');
    if (!q) return;
    const matched = cy.nodes().filter(n => {
      const d = n.data();
      return (d.label || '').toLowerCase().includes(q) || (d.id || '').toLowerCase().includes(q);
    });
    const others = cy.nodes().difference(matched).add(cy.edges());
    others.addClass('dim');
    matched.forEach(n => n.neighborhood().removeClass('dim'));
  });
}

function downloadDataURL(dataUrl, filename){
  const a = document.createElement('a');
  a.href = dataUrl; a.download = filename; a.click();
}
function downloadText(text, filename){
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', () => { initCy(); bindUI(); });
