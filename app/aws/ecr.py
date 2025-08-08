from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)
def mk_id(*parts: str) -> str: return ":".join([p for p in parts if p])
def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ecr = session.client('ecr', region_name=region, config=BOTO_CFG)
    try:
        repos = ecr.describe_repositories().get('repositories', []) or []
        for r in repos:
            arn = r['repositoryArn']
            g.add_node(mk_id('ecr', account_id, region, arn), r['repositoryName'], 'ecr_repo', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] ecr describe_repositories: {e.response['Error'].get('Code')}");
