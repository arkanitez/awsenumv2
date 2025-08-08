from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph
from ..utils import mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    sns = session.client('sns', region_name=region, config=BOTO_CFG)
    try:
        tps = sns.list_topics().get('Topics', [])
        for t in tps:
            arn = t['TopicArn']
            g.add_node(mk_id('sns', account_id, region, arn), arn.split(':')[-1], 'sns_topic', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] sns list_topics: {e.response['Error'].get('Code')}");
    sqs = session.client('sqs', region_name=region, config=BOTO_CFG)
    try:
        queues = sqs.list_queues().get('QueueUrls', []) or []
        for q in queues:
            g.add_node(mk_id('sqs', account_id, region, q), q.split('/')[-1], 'sqs_queue', region, account_id=account_id)
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] sqs list_queues: {e.response['Error'].get('Code')}");
