from __future__ import annotations
from typing import List, Dict
from botocore.exceptions import ClientError
import boto3

def list_accounts(sess: boto3.Session, warnings: List[str]) -> List[Dict]:
    org = sess.client('organizations')
    out: List[Dict] = []
    try:
        paginator = org.get_paginator('list_accounts')
        for page in paginator.paginate():
            out.extend(page.get('Accounts', []) or [])
    except ClientError as e:
        warnings.append(f"[global] organizations list_accounts: {e.response['Error'].get('Code')}")
    return out
