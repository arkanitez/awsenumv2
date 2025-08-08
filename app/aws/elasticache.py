from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ec = session.client('elasticache', region_name=region, config=BOTO_CFG)
    try:
        clusters = ec.describe_cache_clusters(ShowCacheNodeInfo=False).get('CacheClusters', []) or []
        for c in clusters:
            gid = c['CacheClusterId']
            g.add_node(mk_id('elasticache', account_id, region, gid), gid, 'elasticache', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] elasticache describe_cache_clusters: {e.response['Error'].get('Code')}");
