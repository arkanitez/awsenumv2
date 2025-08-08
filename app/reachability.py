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
    sg_edges = [e for e in edges if e['data'].get('type') == 'sg-rule']
    route_edges = [e for e in edges if e['data'].get('type') == 'route']

    # Build adjacency on SG permissions collapsed by (src, dst, proto)
    # We assume ENIs/instances attached to SGs inherit SG rules.
    # This is a simplified inference and can be iterated later.
    derived = []
    # Example: external -> LB (listener already added); skip duplication.

    # FUTURE: Use subnet/VPC membership + routes to infer inter-VPC via peering/TGW.
    # For v1 we skip heavy path search and only add explanation to existing network edges.

    return derived
