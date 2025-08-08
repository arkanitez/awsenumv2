from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import json, re
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    sfn = session.client('stepfunctions', region_name=region, config=BOTO_CFG)
    try:
        paginator = sfn.get_paginator('list_state_machines')
        for page in paginator.paginate():
            for sm in page.get('stateMachines', []) or []:
                arn = sm['stateMachineArn']
                g.add_node(mk_id('sfn', account_id, region, arn), sm['name'], 'step_function', region, account_id=account_id)
                # parse definition for Lambda/SNS/SQS/Kinesis
                try:
                    d = sfn.describe_state_machine(stateMachineArn=arn)
                    definition = d.get('definition')
                    if definition:
                        # crude parse for "arn:aws:lambda:" etc.
                        for service in ('lambda','sqs','sns','kinesis'):
                            for m in re.findall(rf"arn:aws:{service}:[^\"']+", definition):
                                g.add_edge(mk_id('edge', account_id, region, 'sfn', arn, service, m), mk_id('sfn', account_id, region, arn), mk_id(service, account_id, region, m), f'uses {service}', 'invoke', 'data')
                except ClientError as e:
                    warnings.append(f"[{account_id}/{region}] stepfunctions describe_state_machine for {arn}: {e.response['Error'].get('Code')}")
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] stepfunctions list_state_machines: {e.response['Error'].get('Code')}");
