let cy;
const LAYOUTS = {
  'vpc': { name: 'cose-bilkent', quality: 'proof', animate: false, nodeRepulsion: 60000, idealEdgeLength: 200, gravity: 0.25, numIter: 1000, tile: true },
  'service': { name: 'dagre', rankDir: 'LR', nodeSep: 50, rankSep: 100, edgeSep: 20, fit: true },
  'account': { name: 'cose-bilkent', quality: 'default', animate: false, nodeRepulsion: 60000, idealEdgeLength: 220, gravity: 0.25, numIter: 1000, tile: true },
};

const NODE_STYLES = [
  // Parent containers (VPC/Account/Region)
  { sel: 'node:parent', style: { 'background-color': '#16a34a', 'background-opacity': 0.08, 'border-color': '#16a34a', 'border-width': 2, 'shape': 'round-rectangle', 'label': 'data(label)', 'text-valign': 'top', 'font-size': 12 } },

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
  { sel: 'edge[category = "resource"]', style: { 'line-color': '#2563eb', 'target-arrow-color': '#2563eb' }
