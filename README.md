# AWS Topology Enumerator — v1

Cross-account, multi-region AWS topology enumerator with interactive visualization.

## Features (Phase 1)
- Enumerates major AWS services: EC2/VPC (RT/SG/NACL/ENI/IGW/NATGW/Peering/TGW/VPCE), ELBv2, Lambda, API Gateway (v1/v2),
  S3, SQS, SNS, DynamoDB (+ Streams), Kinesis, Step Functions, ECS, ECR, RDS, CloudFront + Route53, OpenSearch, ElastiCache,
  MSK (Kafka), PrivateLink, VPN, Direct Connect.
- Resource edges (attach/belongs/targets) vs Network edges (ports/protocols) vs Data/Invoke edges (invokes/publishes/subscribes).
- Derived reachability (dashed, with explanation trail).
- View modes: VPC view (compound), Service view (lanes), Account/Region view; collapsed by default.
- Search, 1-hop/2-hop spotlight, minimap, exports (PNG/SVG/JSON), AWS Console deep links.
- Findings panel with badges; filters by severity.

> Note: Some services are best-effort and may require additional IAM permissions.

## Quickstart

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000
```

## Credentials
- Uses default env/shared profile, or you can paste keys in the UI.
- Supports multi-account via AssumeRole ARNs (comma-separated).

## Tests
Run unit tests:
```bash
python -m pytest -q
```
