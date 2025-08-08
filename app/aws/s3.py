from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    s3 = session.client('s3', config=BOTO_CFG)
    try:
        res = s3.list_buckets()
    except ClientError as e:
        warnings.append(f"[{account_id}/global] s3 list_buckets: {e.response['Error'].get('Code')}"); return
    for b in res.get('Buckets', []) or []:
        name = b['Name']
        loc = 'us-east-1'
        try:
            lr = s3.get_bucket_location(Bucket=name)
            loc = lr.get('LocationConstraint') or 'us-east-1'
        except ClientError as e:
            warnings.append(f"[{account_id}/global] s3 get_bucket_location for bucket {name}: {e.response['Error'].get('Code')}")
        g.add_node(mk_id('s3', account_id, loc, name), name, 's3_bucket', loc, account_id=account_id)
