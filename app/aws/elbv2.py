from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import boto3
from ..graph import Graph

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except ClientError as e:
        return None, e.response['Error'].get('Code')
    except Exception as e:
        return None, str(e)

def mk_id(*parts: str) -> str:
    return ":".join([p for p in parts if p])

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    elb = session.client('elbv2', region_name=region, config=BOTO_CFG)
    lbs, err = safe_call(elb.describe_load_balancers)
    if err: warnings.append(f"[{account_id}/{region}] elbv2 describe_load_balancers: {err}"); return
    for lb in lbs.get('LoadBalancers', []) or []:
        lbarn = lb['LoadBalancerArn']; name = lb['LoadBalancerName']; scheme = lb.get('Scheme'); lbtype = lb.get('Type')
        vpcid = lb.get('VpcId')
        g.add_node(mk_id("lb", account_id, region, lbarn), f"{name} ({lbtype})", "load_balancer", region, details={"scheme": scheme, "dns": lb.get('DNSName')}, parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)
        for az in lb.get('AvailabilityZones', []):
            sid = az.get('SubnetId')
            if sid:
                g.add_edge(mk_id("edge", account_id, region, name, sid), mk_id("lb", account_id, region, lbarn), mk_id("subnet", account_id, region, sid), "in-subnet", "attach", "resource")
        for sgid in lb.get('SecurityGroups', []) or []:
            g.add_edge(mk_id("edge", account_id, region, name, sgid), mk_id("lb", account_id, region, lbarn), mk_id("sg", account_id, region, sgid), "has-sg", "attach", "resource")
        # listeners
        listeners, err = safe_call(elb.describe_listeners, LoadBalancerArn=lbarn)
        if err: warnings.append(f"[{account_id}/{region}] elbv2 describe_listeners: {err}"); listeners = {"Listeners": []}
        for lst in listeners.get('Listeners', []):
            proto = lst.get('Protocol'); port = lst.get('Port')
            ext = mk_id("internet", account_id, region, "0.0.0.0/0") if scheme == "internet-facing" else mk_id("vpc", account_id, region, vpcid)
            g.add_node(ext, "Internet" if scheme == "internet-facing" else f"VPC {vpcid}", "external", region, account_id=account_id)
            g.add_edge(mk_id("edge", account_id, region, lbarn, str(port), str(proto)), ext, mk_id("lb", account_id, region, lbarn), f"{proto}:{port}", "listener", "network")
        # target groups
        tgs, err = safe_call(elb.describe_target_groups, LoadBalancerArn=lbarn)
        if err: warnings.append(f"[{account_id}/{region}] elbv2 describe_target_groups: {err}"); tgs = {"TargetGroups": []}
        for tg in tgs.get('TargetGroups', []) or []:
            tgarn = tg['TargetGroupArn']
            g.add_node(mk_id("tg", account_id, region, tgarn), tg.get('TargetGroupName', 'tg'), "target_group", region, details={"protocol": tg.get('Protocol'), "port": tg.get('Port')}, account_id=account_id)
            g.add_edge(mk_id("edge", account_id, region, lbarn, tgarn), mk_id("lb", account_id, region, lbarn), mk_id("tg", account_id, region, tgarn), "lb→tg", "bind", "resource")
            th, err = safe_call(elb.describe_target_health, TargetGroupArn=tgarn)
            if err: warnings.append(f"[{account_id}/{region}] elbv2 describe_target_health: {err}"); th = {"TargetHealthDescriptions": []}
            for d in th.get('TargetHealthDescriptions', []) or []:
                t = d.get('Target', {}); tid = t.get('Id'); ttype = tg.get('TargetType')  # instance | ip | alb | lambda
                if ttype == 'lambda':
                    nid = mk_id("lambda", account_id, region, tid); g.add_node(nid, tid.split(":")[-1], "lambda", region, account_id=account_id)
                elif ttype == 'instance':
                    nid = mk_id("i", account_id, region, tid); g.add_node(nid, tid, "instance", region, account_id=account_id)
                else:
                    nid = mk_id(ttype or 'target', account_id, region, str(tid)); g.add_node(nid, str(tid), ttype or 'target', region, account_id=account_id)
                g.add_edge(mk_id("edge", account_id, region, tgarn, str(tid)), mk_id("tg", account_id, region, tgarn), nid, f"{tg.get('Protocol')}:{tg.get('Port')}", "tg-target", "network")
