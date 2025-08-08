from __future__ import annotations
from typing import List
from botocore.exceptions import ClientError
from botocore.config import Config as BotoConfig
import boto3
from ..graph import Graph
from ..policy import summarize_policy
from ..utils import safe_call, mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    lam = session.client('lambda', region_name=region, config=BOTO_CFG)
    try:
        paginator = lam.get_paginator('list_functions')
        for page in paginator.paginate():
            for fn in page.get('Functions', []) or []:
                arn = fn['FunctionArn']; name = fn['FunctionName']
                vpcid = fn.get('VpcConfig', {}).get('VpcId')
                parent = mk_id('vpc', account_id, region, vpcid) if vpcid else None
                g.add_node(mk_id('lambda', account_id, region, arn), name, 'lambda', region, details={'runtime': fn.get('Runtime')}, parent=parent, account_id=account_id)
                # VPC
                for sid in fn.get('VpcConfig', {}).get('SubnetIds', []) or []:
                    g.add_edge(mk_id('edge', account_id, region, arn, sid), mk_id('lambda', account_id, region, arn), mk_id('subnet', account_id, region, sid), 'in-subnet', 'attach', 'resource')
                for sgid in fn.get('VpcConfig', {}).get('SecurityGroupIds', []) or []:
                    g.add_edge(mk_id('edge', account_id, region, arn, sgid), mk_id('lambda', account_id, region, arn), mk_id('sg', account_id, region, sgid), 'has-sg', 'attach', 'resource')
                # Destinations (on success/failure)
                ev, err = safe_call(lam.get_function_event_invoke_config, FunctionName=arn)
                if not err and ev:
                    dests = ev.get('DestinationConfig', {})
                    for outcome in ('OnSuccess', 'OnFailure'):
                        arn2 = dests.get(outcome, {}).get('Destination')
                        if arn2:
                            g.add_node(mk_id('dest', account_id, region, arn2), arn2.split(':')[-1], 'destination', region, account_id=account_id)
                            g.add_edge(mk_id('edge', account_id, region, arn, outcome, arn2),
                                       mk_id('lambda', account_id, region, arn),
                                       mk_id('dest', account_id, region, arn2),
                                       f'{outcome.lower()} →', 'invoke', 'data')
                # Resource policy
                pol, err = safe_call(lam.get_policy, FunctionName=arn)
                if not err and pol and pol.get('Policy'):
                    summary = summarize_policy(pol['Policy'])
                    g.add_node(
                        mk_id('lambda', account_id, region, arn),
                        name,
                        'lambda',
                        region,
                        details={'policy': summary}
                    )

    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] lambda list_functions: {e.response['Error'].get('Code')}")
