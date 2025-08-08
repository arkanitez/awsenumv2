from __future__ import annotations
from typing import List
from botocore.config import Config as BotoConfig
import boto3
from ..graph import Graph
from ..utils import safe_call, mk_id

BOTO_CFG = BotoConfig(retries={'max_attempts': 8, 'mode': 'adaptive'}, read_timeout=25, connect_timeout=10)

def enumerate(session: boto3.Session, account_id: str, region: str, g: Graph, warnings: List[str]) -> None:
    # API Gateway v1 (REST)
    apigw = session.client('apigateway', region_name=region, config=BOTO_CFG)
    apis, err = safe_call(apigw.get_rest_apis, limit=500)
    if not err and apis:
        for api in apis.get('items', []):
            api_id = api['id']; name = api.get('name', api_id)
            g.add_node(mk_id('apigw', account_id, region, api_id), f'API {name}', 'api_gw', region, details={'endpoint': api.get('endpointConfiguration', {})}, account_id=account_id)
            # Stages
            stages, err2 = safe_call(apigw.get_stages, restApiId=api_id)
            if not err2 and stages:
                for st in stages.get('item', []):
                    sid = st.get('stageName')
                    g.add_node(mk_id('apigw-stage', account_id, region, api_id, sid), f'Stage {sid}', 'api_gw_stage', region, account_id=account_id, parent=mk_id('apigw', account_id, region, api_id))
            # Policy (resource policy may exist)
            _, err3 = safe_call(apigw.get_rest_api, restApiId=api_id)
            if err3:
                warnings.append(f"[{account_id}/{region}] apigateway get_rest_api: {err3}")

    # API Gateway v2 (HTTP/WebSocket)
    apigwv2 = session.client('apigatewayv2', region_name=region, config=BOTO_CFG)
    apis2, err = safe_call(apigwv2.get_apis)
    if not err and apis2:
        for api in apis2.get('Items', []):
            api_id = api['ApiId']; proto = api.get('ProtocolType')
            g.add_node(mk_id('apigw2', account_id, region, api_id), f'{proto} API {api_id}', 'api_gw_v2', region, details={'endpoint': api.get('ApiEndpoint')}, account_id=account_id)
            # Routes → Integrations
            routes, _ = safe_call(apigwv2.get_routes, ApiId=api_id)
            integrations, _ = safe_call(apigwv2.get_integrations, ApiId=api_id)
            integ_map = {i['IntegrationId']: i for i in (integrations or {}).get('Items', [])}
            for r in (routes or {}).get('Items', []):
                rid = r['RouteId']; key = r.get('RouteKey'); iid = r.get('Target', '').split('/')[-1]
                g.add_node(mk_id('apigw2-route', account_id, region, api_id, rid), key or rid, 'api_gw_v2_route', region, parent=mk_id('apigw2', account_id, region, api_id), account_id=account_id)
                if iid and iid in integ_map:
                    i = integ_map[iid]; uri = i.get('IntegrationUri') or ''
                    g.add_node(mk_id('integration', account_id, region, api_id, iid), 'Integration', 'integration', region, account_id=account_id, parent=mk_id('apigw2', account_id, region, api_id))
                    g.add_edge(mk_id('edge', account_id, region, 'route', rid, iid),
                               mk_id('apigw2-route', account_id, region, api_id, rid),
                               mk_id('integration', account_id, region, api_id, iid),
                               'route→integration', 'bind', 'resource')
                    # Link to Lambda if URI contains lambda arn
                    if ':lambda:' in uri:
                        lam_arn = uri.split('function:')[-1].split(':')[-1] if 'function:' in uri else uri.split(':')[-1]
                        g.add_edge(mk_id('edge', account_id, region, 'integration', iid, 'lambda', lam_arn),
                                   mk_id('integration', account_id, region, api_id, iid),
                                   mk_id('lambda', account_id, region, lam_arn),
                                   'invokes', 'invoke', 'data')
