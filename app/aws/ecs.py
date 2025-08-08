from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)
def mk_id(*parts: str) -> str: return ":".join([p for p in parts if p])
def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ecs = session.client('ecs', region_name=region, config=BOTO_CFG)
    try:
        clusters = ecs.list_clusters().get('clusterArns', []) or []
        for c in clusters:
            g.add_node(mk_id('ecs-cluster', account_id, region, c), c.split('/')[-1], 'ecs_cluster', region, account_id=account_id)
            svcs = ecs.list_services(cluster=c).get('serviceArns', []) or []
            for s in svcs:
                g.add_node(mk_id('ecs-svc', account_id, region, s), s.split('/')[-1], 'ecs_service', region, account_id=account_id, parent=mk_id('ecs-cluster', account_id, region, c))
                g.add_edge(mk_id('edge', account_id, region, c, s), mk_id('ecs-cluster', account_id, region, c), mk_id('ecs-svc', account_id, region, s), 'has-service', 'attach', 'resource')
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] ecs list_clusters/services: {e.response['Error'].get('Code')}");
