from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    # CloudFront is global
    cf = session.client('cloudfront', config=BOTO_CFG)
    try:
        dists = cf.list_distributions().get('DistributionList', {}).get('Items', []) or []
        for d in dists:
            did = d['Id']
            g.add_node(mk_id('cf', account_id, 'global', did), d.get('Comment') or did, 'cloudfront', 'global', account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/global] cloudfront list_distributions: {e.response['Error'].get('Code')}");
    # Route53 hosted zones
    r53 = session.client('route53', config=BOTO_CFG)
    try:
        zones = r53.list_hosted_zones().get('HostedZones', []) or []
        for z in zones:
            zid = z['Id'].split('/')[-1]
            g.add_node(mk_id('r53zone', account_id, 'global', zid), z['Name'], 'route53_zone', 'global', account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/global] route53 list_hosted_zones: {e.response['Error'].get('Code')}");
