from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    rds = session.client('rds', region_name=region, config=BOTO_CFG)
    try:
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for db in page.get('DBInstances', []) or []:
                arn = db.get('DBInstanceArn') or db['DBInstanceIdentifier']
                name = db['DBInstanceIdentifier']
                vpcid = db.get('DBSubnetGroup', {}).get('VpcId')
                g.add_node(mk_id('rds', account_id, region, arn), name, 'rds_instance', region, details={'engine': db.get('Engine'), 'PubliclyAccessible': db.get('PubliclyAccessible')}, parent=mk_id('vpc', account_id, region, vpcid) if vpcid else None, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] rds describe_db_instances: {e.response['Error'].get('Code')}");
