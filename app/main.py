from __future__ import annotations
import os
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import orjson
import boto3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .graph import Graph
from .reachability import derive_reachability
from .findings import analyze as analyze_findings
from .aws.session import build_root_session, assume_roles, discover_regions
from .aws import ec2, elbv2, lambda_, apigw, s3, sqs_sns, dynamodb, kinesis, stepfunctions, ecs, rds, route53_cf, ecr, opensearch, elasticache, msk, nacl_tgw_vpn_dx

WORKERS = int(os.environ.get('WORKERS', '24'))

def json_response(data: Any) -> JSONResponse:
    return JSONResponse(orjson.loads(orjson.dumps(data)))

app = FastAPI()
app.mount('/ui', StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'ui')), name='ui')

@app.get('/', response_class=HTMLResponse)
async def index():
    with open(os.path.join(os.path.dirname(__file__), 'ui', 'index.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())

@app.post('/enumerate')
async def enumerate_api(req: Request):
    payload = await req.json()
    ak = payload.get('access_key_id'); sk = payload.get('secret_access_key'); st = payload.get('session_token')
    profile = payload.get('profile'); role_arns = payload.get('assume_roles') or []
    regions = payload.get('regions') or []
    services = payload.get('services') or {}  # service toggles

    root = build_root_session(ak, sk, st, profile)
    sessions = assume_roles(root, role_arns)
    all_regions = regions
    if not all_regions or all_regions == ['ALL']:
        all_regions = discover_regions(root)

    g = Graph()
    warnings: List[str] = []
    svc_list = [
        ('ec2', ec2.enumerate),
        ('elbv2', elbv2.enumerate),
        ('lambda', lambda_.enumerate),
        ('apigw', apigw.enumerate),
        ('s3', s3.enumerate),       # global
        ('sqs_sns', sqs_sns.enumerate),
        ('dynamodb', dynamodb.enumerate),
        ('kinesis', kinesis.enumerate),
        ('stepfunctions', stepfunctions.enumerate),
        ('ecs', ecs.enumerate),
        ('rds', rds.enumerate),
        ('route53_cf', route53_cf.enumerate),  # global mostly
        ('ecr', ecr.enumerate),
        ('opensearch', opensearch.enumerate),
        ('elasticache', elasticache.enumerate),
        ('msk', msk.enumerate),
        ('nacl_tgw_vpn_dx', nacl_tgw_vpn_dx.enumerate),
    ]

    # Global services (s3, route53_cf) run once per account
    def run_account(account_arn: str, sess: boto3.Session):
        # identity
        account_id = None
        try:
            sts = sess.client('sts')
            me = sts.get_caller_identity()
            account_id = me.get('Account')
        except Exception as e:
            warnings.append(f"sts failed: {e}")
            account_id = account_arn or 'self'
        # global services
        for name, fn in svc_list:
            if name in ('s3','route53_cf'):
                try:
                    fn(sess, account_id, 'global', g, warnings)
                except Exception as e:
                    warnings.append(f"{name} global error: {e}")
        # regional
        with ThreadPoolExecutor(max_workers=min(WORKERS, max(1, len(all_regions)))) as pool:
            futs = []
            for r in all_regions:
                for name, fn in svc_list:
                    if name in ('s3','route53_cf'): continue
                    if services and services.get(name) is False: continue
                    futs.append(pool.submit(lambda rr=r, f=fn, n=name: _run_fn(f, sess, account_id, rr, g, n)))
            for f in as_completed(futs):
                w = f.result()
                if w: warnings.extend(w)

    def _run_fn(fn, sess, account_id, region, g, name):
        ww = []
        try:
            fn(sess, account_id, region, g, ww)
        except Exception as e:
            ww.append(f"{name} {account_id}/{region}: {e}")
        return ww

    # Run per account
    for arn, sess in sessions.items():
        if sess is None: 
            warnings.append(f"AssumeRole failed: {arn}"); continue
        run_account(arn, sess)

    # Derived reachability
    derived = derive_reachability(g)
    for e in derived:
        g.add_edge(**e)  # e must have keys compatible with Graph.add_edge data

    elements = g.elements()
    findings = analyze_findings(elements)

    return json_response({ 'elements': elements, 'warnings': warnings, 'findings': findings })

@app.get('/_health')
async def health():
    return { 'ok': True }
