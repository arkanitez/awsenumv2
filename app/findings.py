from __future__ import annotations
from typing import Any, Dict, List

def analyze(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return list of findings with severity and targets."""
    findings: List[Dict[str, Any]] = []
    nodes = [e for e in elements if 'source' not in e['data']]
    edges = [e for e in elements if 'source' in e['data']]
    
    # A more comprehensive list of public CIDR blocks
    public_cidrs = [
        "0.0.0.0/0",
        "::/0", # IPv6 equivalent of 0.0.0.0/0
    ]


    # Public SG ingress
    for e in edges:
        d = e['data']
        if d.get('type') == 'sg-rule' and d.get('label', '').startswith(('tcp', 'udp', 'icmp')):
            src_id = d['source']; tgt_id = d['target']
            if ':cidr:' in src_id and any(public_cidr in src_id for public_cidr in public_cidrs):
                findings.append({
                    'id': f'finding:{d["id"]}',
                    'severity': 'High',
                    'title': 'Public ingress from Internet',
                    'detail': f'{d.get("label")} to {tgt_id}',
                    'edge_id': d['id']
                })

    # Internet-facing LB with wide listeners
    for n in nodes:
        d = n['data']
        if d.get('type') == 'load_balancer' and d['details'].get('scheme') == 'internet-facing':
            # Check listeners via edges to this node
            for e in edges:
                ed = e['data']
                if ed['target'] == d['id'] and ed.get('type') == 'listener':
                    if any(public_cidr in ed['source'] for public_cidr in public_cidrs):
                        findings.append({
                            'id': f'finding:{d["id"]}:lb-listener',
                            'severity': 'Medium',
                            'title': 'Internet-facing LB with public listener',
                            'detail': f'{d["label"]} has listener {ed["label"]}',
                            'node_id': d['id']
                        })

    # RDS publicly accessible
    for n in nodes:
        d = n['data']
        if d.get('type') == 'rds_instance':
            if d['details'].get('PubliclyAccessible'):
                findings.append({
                    'id': f'finding:{d["id"]}:rds-public',
                    'severity': 'High',
                    'title': 'RDS instance is publicly accessible',
                    'detail': d['label'],
                    'node_id': d['id']
                })

    return findings
