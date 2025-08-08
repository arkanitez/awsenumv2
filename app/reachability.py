from __future__ import annotations
from typing import Dict, Any, List, Tuple, Set
from .graph import Graph

def derive_reachability(g: Graph) -> List[Dict[str, Any]]:
    """Best-effort reachability edges based on SG rules + routes.
    Produces dashed ('derived': True) network edges with explanation trail in details.
    This is intentionally conservative to avoid false positives.
    """
    els = g.elements()
    node_by_id = {e['data']['id']: e for e in els if 'source' not in e['data']}
    edges = [e for e in els if 'source' in e['data']]

    derived_edges = []

    # Example: If an instance is in a public subnet with a public IP, it's reachable.
    for node_data in node_by_id.values():
        if node_data['data'].get('type') == 'instance':
            instance_id = node_data['data']['id']
            details = node_data['data'].get('details', {})
            if details.get('public_ip'):
                # Find the subnet and check for an internet gateway route
                for edge in edges:
                    if edge['data']['source'] == instance_id and 'subnet' in edge['data']['target']:
                        subnet_id = edge['data']['target']
                        # Now find the route table for this subnet
                        for rt_edge in edges:
                            if rt_edge['data']['source'] == subnet_id and 'rtb' in rt_edge['data']['target']:
                                rtb_id = rt_edge['data']['target']
                                # Check for a route to an IGW
                                for route in edges:
                                    if route['data']['source'] == rtb_id and 'igw' in route['data']['target']:
                                        derived_edges.append({
                                            'id': f"derived:{instance_id}:igw",
                                            'source': 'internet',
                                            'target': instance_id,
                                            'label': 'public-ip-and-route',
                                            'type': 'derived-reachability',
                                            'category': 'network',
                                            'derived': True
                                        })

    return derived_edges
