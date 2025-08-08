from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ddb = session.client('dynamodb', region_name=region, config=BOTO_CFG)
    try:
        paginator = ddb.get_paginator('list_tables')
        for page in paginator.paginate():
            for t in page.get('TableNames', []) or []:
                g.add_node(mk_id('dynamodb', account_id, region, t), t, 'dynamodb_table', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] dynamodb list_tables: {e.response['Error'].get('Code')}");
