from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.config import Config as BotoConfig
import boto3

from ..graph import Graph
from ..utils import safe_call, mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def range_to_str(from_port, to_port, proto) -> str:
    if from_port is None and to_port is None: return "all"
    if proto in ("-1", "all"): return "all"
    if from_port == to_port: return str(from_port)
    return f"{from_port}-{to_port}"

def classify_target_type(target: Any) -> str:
    s = str(target)
    if s.startswith("igw-"): return "igw"
    if s.startswith("nat-"): return "natgw"
    if s.startswith("tgw-"): return "tgw"
    if s.startswith("pcx-"): return "pcx"
    if s.startswith("eni-"): return "eni"
    if s.startswith("i-"):   return "i"
    return "target"

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    ec2 = session.client('ec2', region_name=region, config=BOTO_CFG)

    # VPCs
    vpcs, err = safe_call(ec2.describe_vpcs)
    if err: warnings.append(f"[{account_id}/{region}] describe_vpcs: {err}"); return
    for v in vpcs.get('Vpcs', []):
        vid = v['VpcId']
        g.add_node(mk_id("vpc", account_id, region, vid), f"VPC {vid}", "vpc", region, details={"cidr": v.get('CidrBlock')}, account_id=account_id)

    # Subnets
    subnets, err = safe_call(ec2.describe_subnets)
    if err: warnings.append(f"[{account_id}/{region}] describe_subnets: {err}"); subnets = {"Subnets": []}
    for s in subnets.get('Subnets', []):
        sid = s['SubnetId']; vid = s['VpcId']
        g.add_node(mk_id("subnet", account_id, region, sid), f"Subnet {sid}", "subnet", region,
                   details={"cidr": s.get('CidrBlock'), "az": s.get('AvailabilityZone')},
                   parent=mk_id("vpc", account_id, region, vid), account_id=account_id)
        g.add_edge(mk_id("edge", account_id, region, sid, vid),
                   mk_id("subnet", account_id, region, sid),
                   mk_id("vpc", account_id, region, vid),
                   "subnet-of", "attach", "resource")

    # Route tables
    rts, err = safe_call(ec2.describe_route_tables)
    if err: warnings.append(f"[{account_id}/{region}] describe_route_tables: {err}"); rts = {"RouteTables": []}
    for rt in rts.get('RouteTables', []):
        rtid = rt['RouteTableId']; vpcid = rt.get('VpcId')
        g.add_node(mk_id("rtb", account_id, region, rtid), f"RTB {rtid}", "route_table", region,
                   parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)
        if vpcid:
            g.add_edge(mk_id("edge", account_id, region, rtid, vpcid),
                       mk_id("rtb", account_id, region, rtid),
                       mk_id("vpc", account_id, region, vpcid),
                       "rtb-of", "attach", "resource")
        for assoc in rt.get('Associations', []) or []:
            if assoc.get('SubnetId'):
                sid = assoc['SubnetId']
                g.add_edge(mk_id("edge", account_id, region, sid, rtid),
                           mk_id("subnet", account_id, region, sid),
                           mk_id("rtb", account_id, region, rtid),
                           "assoc", "assoc", "resource")
        for r in rt.get('Routes', []) or []:
            dst = r.get('DestinationCidrBlock') or r.get('DestinationIpv6CidrBlock') or r.get('DestinationPrefixListId')
            target = (r.get('GatewayId') or r.get('NatGatewayId') or r.get('TransitGatewayId') or r.get('VpcPeeringConnectionId') or r.get('InstanceId') or r.get('NetworkInterfaceId'))
            if dst and target:
                dstnode = mk_id("cidr", account_id, region, str(dst)) if "pl-" not in str(dst) else mk_id("prefixlist", account_id, region, str(dst))
                g.add_node(dstnode, str(dst), "cidr" if "cidr" in dstnode else "prefix_list", region, account_id=account_id)
                ttype = classify_target_type(target)
                g.add_node(mk_id(ttype, account_id, region, target), target, ttype, region, parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)
                g.add_edge(mk_id("edge", account_id, region, rtid, target, str(dst)),
                           mk_id("rtb", account_id, region, rtid),
                           mk_id(ttype, account_id, region, target),
                           f"route→{dst}", "route", "network", details={"destination": dst})

    # IGW
    igws, err = safe_call(ec2.describe_internet_gateways)
    if err: warnings.append(f"[{account_id}/{region}] describe_internet_gateways: {err}"); igws = {"InternetGateways": []}
    for igw in igws.get('InternetGateways', []):
        igwid = igw['InternetGatewayId']
        g.add_node(mk_id("igw", account_id, region, igwid), igwid, "igw", region, account_id=account_id)
        for att in igw.get('Attachments', []) or []:
            vpcid = att.get('VpcId')
            if vpcid:
                g.add_edge(mk_id("edge", account_id, region, igwid, vpcid),
                           mk_id("igw", account_id, region, igwid),
                           mk_id("vpc", account_id, region, vpcid),
                           "attached", "attach", "resource")

    # NATGW
    ngws, err = safe_call(ec2.describe_nat_gateways)
    if err: warnings.append(f"[{account_id}/{region}] describe_nat_gateways: {err}"); ngws = {"NatGateways": []}
    for nat in ngws.get('NatGateways', []):
        natid = nat['NatGatewayId']; vpcid = nat.get('VpcId')
        g.add_node(mk_id("natgw", account_id, region, natid), natid, "nat_gateway", region,
                   details={"state": nat.get('State')}, parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)
        sn = (nat.get('SubnetId') or (nat.get('SubnetIds') or [None])[0])
        if sn:
            g.add_edge(mk_id("edge", account_id, region, natid, sn),
                       mk_id("natgw", account_id, region, natid),
                       mk_id("subnet", account_id, region, sn),
                       "in-subnet", "attach", "resource")

    # Security groups + rules (collapsed labels per peer)
    sgs, err = safe_call(ec2.describe_security_groups)
    if err: warnings.append(f"[{account_id}/{region}] describe_security_groups: {err}"); sgs = {"SecurityGroups": []}
    for sg in sgs.get('SecurityGroups', []):
        sgid = sg['GroupId']; vpcid = sg.get('VpcId')
        g.add_node(mk_id("sg", account_id, region, sgid), f"{sg.get('GroupName')} ({sgid})", "security_group", region,
                   details={"desc": sg.get('Description'), "vpc": vpcid}, parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)

    def collapse_rules(perms, direction: str, sgid: str):
        agg: Dict[str, Dict[str, set]] = {}
        for perm in perms or []:
            proto = perm.get('IpProtocol', 'all')
            fport = perm.get('FromPort'); tport = perm.get('ToPort')
            prange = range_to_str(fport, tport, proto)
            # CIDRs
            for r in perm.get('IpRanges', []):
                cidr = r.get('CidrIp')
                if not cidr: continue
                key = (proto, prange, cidr)
                agg.setdefault(cidr, {}).setdefault(proto, set()).add(prange)
            # SG refs
            for up in perm.get('UserIdGroupPairs', []):
                other = up.get('GroupId')
                if not other: continue
                key = (proto, prange, other)
                agg.setdefault(other, {}).setdefault(proto, set()).add(prange)
        # Emit collapsed edges
        for peer, protos in agg.items():
            label = "; ".join([f"{p}:{','.join(sorted(r))}" for p, r in protos.items()])
            src, tgt = (peer, sgid) if direction == 'ingress' else (sgid, peer)
            # ensure peer node exists
            if peer.startswith('sg-'):
                g.add_node(mk_id("sg", account_id, region, peer), peer, "security_group", region, account_id=account_id)
                src_id = mk_id("sg", account_id, region, src); tgt_id = mk_id("sg", account_id, region, tgt)
            elif '/' in peer:
                g.add_node(mk_id("cidr", account_id, region, peer), peer, "cidr", region, account_id=account_id)
                src_id = mk_id("cidr", account_id, region, src) if '/' in src else mk_id("sg", account_id, region, src)
                tgt_id = mk_id("cidr", account_id, region, tgt) if '/' in tgt else mk_id("sg", account_id, region, tgt)
            else:
                warnings.append(f"[{account_id}/{region}] Unhandled peer type in SG rule: {peer}")
                continue
            g.add_edge(mk_id("edge", account_id, region, src, tgt, direction),
                       src_id, tgt_id, label, "sg-rule", "network")

    for sg in sgs.get('SecurityGroups', []):
        sgid = sg['GroupId']
        collapse_rules(sg.get('IpPermissions'), 'ingress', sgid)
        collapse_rules(sg.get('IpPermissionsEgress'), 'egress', sgid)

    # ENIs
    enis, err = safe_call(ec2.describe_network_interfaces)
    if err: warnings.append(f"[{account_id}/{region}] describe_network_interfaces: {err}"); enis = {"NetworkInterfaces": []}
    for eni in enis.get('NetworkInterfaces', []):
        enid = eni['NetworkInterfaceId']; vpcid = eni.get('VpcId'); sid = eni.get('SubnetId')
        parent = mk_id("subnet", account_id, region, sid) if sid else (mk_id("vpc", account_id, region, vpcid) if vpcid else None)
        g.add_node(mk_id("eni", account_id, region, enid), enid, "eni", region, details={"private_ip": eni.get('PrivateIpAddress')}, parent=parent, account_id=account_id)
        if sid:
            g.add_edge(mk_id("edge", account_id, region, enid, sid), mk_id("eni", account_id, region, enid), mk_id("subnet", account_id, region, sid), "in-subnet", "attach", "resource")
        for sgid in [x['GroupId'] for x in eni.get('Groups', [])]:
            g.add_edge(mk_id("edge", account_id, region, enid, sgid), mk_id("eni", account_id, region, enid), mk_id("sg", account_id, region, sgid), "has-sg", "attach", "resource")
        if eni.get('Attachment') and eni['Attachment'].get('InstanceId'):
            iid = eni['Attachment']['InstanceId']
            g.add_node(mk_id("i", account_id, region, iid), iid, "instance", region, parent=parent, account_id=account_id)
            g.add_edge(mk_id("edge", account_id, region, iid, enid), mk_id("i", account_id, region, iid), mk_id("eni", account_id, region, enid), "eni", "attach", "resource")

    # Instances
    paginator = ec2.get_paginator('describe_instances')
    try:
        for page in paginator.paginate():
            for res in page.get('Reservations', []):
                for inst in res.get('Instances', []):
                    iid = inst['InstanceId']; name = next((t['Value'] for t in inst.get('Tags', []) if t.get('Key') == 'Name'), iid)
                    sid = inst.get('SubnetId'); vpcid = inst.get('VpcId')
                    parent = mk_id("subnet", account_id, region, sid) if sid else (mk_id("vpc", account_id, region, vpcid) if vpcid else None)
                    g.add_node(mk_id("i", account_id, region, iid), name, "instance", region, details={"state": inst.get('State', {}).get('Name')}, parent=parent, account_id=account_id)
                    if sid:
                        g.add_edge(mk_id("edge", account_id, region, iid, sid), mk_id("i", account_id, region, iid), mk_id("subnet", account_id, region, sid), "in-subnet", "attach", "resource")
                    for sg in inst.get('SecurityGroups', []) or []:
                        g.add_edge(mk_id("edge", account_id, region, iid, sg['GroupId']), mk_id("i", account_id, region, iid), mk_id("sg", account_id, region, sg['GroupId']), "has-sg", "attach", "resource")
    except ClientError as e:
        warnings.append(f"[{account_id}/{region}] describe_instances: {e.response['Error'].get('Code')}")

    # VPC Endpoints
    vpces, err = safe_call(ec2.describe_vpc_endpoints)
    if err: warnings.append(f"[{account_id}/{region}] describe_vpc_endpoints: {err}"); vpces = {"VpcEndpoints": []}
    for vpce in vpces.get('VpcEndpoints', []):
        vid = vpce['VpcEndpointId']; svc = vpce.get('ServiceName'); vpcid = vpce.get('VpcId')
        g.add_node(mk_id("vpce", account_id, region, vid), vid, "vpc_endpoint", region, details={"service": svc, "type": vpce.get('VpcEndpointType')}, parent=mk_id("vpc", account_id, region, vpcid) if vpcid else None, account_id=account_id)
        if svc:
            g.add_node(mk_id("service", account_id, region, svc), svc, "aws_service", region, account_id=account_id)
            g.add_edge(mk_id("edge", account_id, region, vid, svc), mk_id("vpce", account_id, region, vid), mk_id("service", account_id, region, svc), "to-service", "bind", "resource")
        for sid in vpce.get('SubnetIds', []) or []:
            g.add_edge(mk_id("edge", account_id, region, vid, sid), mk_id("vpce", account_id, region, vid), mk_id("subnet", account_id, region, sid), "in-subnet", "attach", "resource")
