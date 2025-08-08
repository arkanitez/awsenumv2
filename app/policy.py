from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json

def summarize_policy(doc: str | Dict[str, Any]) -> List[str]:
    """Return a brief English list of statements. Accepts JSON string or dict."""
    if isinstance(doc, str):
        try:
            data = json.loads(doc)
        except json.JSONDecodeError:
            return ["<unparseable policy>"]
    else:
        data = doc or {}
    out: List[str] = []
    for st in data.get("Statement", []):
        eff = st.get("Effect")
        act = st.get("Action")
        res = st.get("Resource")
        prn = st.get("Principal") or st.get("NotPrincipal") or "(principal)"
        cond = st.get("Condition")
        out.append(f"{eff} {act} on {res} for {prn}{' with conditions' if cond else ''}")
    return out or ["(empty policy)"]
