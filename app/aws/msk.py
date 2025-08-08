from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    msk = session.client('kafka', region_name=region, config=BOTO_CFG)
    try:
        clusters = msk.list_clusters().get('ClusterInfoList', []) or []
        for c in clusters:
            arn = c['ClusterArn']
            g.add_node(mk_id('msk', account_id, region, arn), c.get('ClusterName', arn), 'msk_cluster', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] msk list_clusters: {e.response['Error'].get('Code')}");
