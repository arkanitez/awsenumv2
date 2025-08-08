from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)
def mk_id(*parts: str) -> str: return ":".join([p for p in parts if p])
def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    osd = session.client('opensearch', region_name=region, config=BOTO_CFG)
    try:
        d = osd.list_domain_names()
        for item in d.get('DomainNames', []) or []:
            name = item['DomainName']
            g.add_node(mk_id('os', account_id, region, name), name, 'opensearch', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] opensearch list_domain_names: {e.response['Error'].get('Code')}");
