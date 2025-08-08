from __future__ import annotations
from typing import Dict, Any, List, Optional
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def build_root_session(ak: Optional[str], sk: Optional[str], st: Optional[str], profile: Optional[str]) -> boto3.Session:
    if profile:
        return boto3.Session(profile_name=profile)
    if ak and sk:
        return boto3.Session(aws_access_key_id=ak, aws_secret_access_key=sk, aws_session_token=st)
    return boto3.Session()

def assume_roles(root: boto3.Session, role_arns: List[str]) -> Dict[str, boto3.Session]:
    out = { 'self': root }
    if not role_arns:
        return out
    sts = root.client('sts', config=BOTO_CFG)
    for i, arn in enumerate(role_arns, start=1):
        try:
            resp = sts.assume_role(RoleArn=arn, RoleSessionName=f'topology-session-{i}')
            creds = resp['Credentials']
            out[arn] = boto3.Session(
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
            )
        except ClientError as e:
            # Skip but record as None
            out[arn] = None
    return out

def discover_regions(sess: boto3.Session) -> List[str]:
    try:
        ec2 = sess.client('ec2', region_name='us-east-1', config=BOTO_CFG)
        data = ec2.describe_regions(AllRegions=False)
        return [r['RegionName'] for r in data.get('Regions', [])]
    except Exception:
        # Reasonable subset
        return [
            'us-east-1','us-east-2','us-west-1','us-west-2','eu-west-1','eu-west-2','eu-central-1',
            'ap-southeast-1','ap-southeast-2','ap-northeast-1','ap-south-1'
        ]
