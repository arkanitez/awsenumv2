from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ec2 = session.client('ec2', region_name=region, config=BOTO_CFG)
    try:
        nacls = ec2.describe_network_acls().get('NetworkAcls', []) or []
        for a in nacls:
            aid = a['NetworkAclId']; vpcid = a.get('VpcId')
            g.add_node(mk_id('nacl', account_id, region, aid), aid, 'nacl', region, account_id=account_id, parent=mk_id('vpc', account_id, region, vpcid) if vpcid else None)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] ec2 describe_network_acls: {e.response['Error'].get('Code')}");
    # TGW
    try:
        tgws = ec2.describe_transit_gateways().get('TransitGateways', []) or []
        for t in tgws:
            tid = t['TransitGatewayId']
            g.add_node(mk_id('tgw', account_id, region, tid), tid, 'tgw', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] ec2 describe_transit_gateways: {e.response['Error'].get('Code')}");
    # Peering
    try:
        pcx = ec2.describe_vpc_peering_connections().get('VpcPeeringConnections', []) or []
        for p in pcx:
            pid = p['VpcPeeringConnectionId']
            g.add_node(mk_id('pcx', account_id, region, pid), pid, 'pcx', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] ec2 describe_vpc_peering_connections: {e.response['Error'].get('Code')}");
