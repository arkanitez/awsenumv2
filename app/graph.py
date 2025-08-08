from __future__ import annotations
from typing import Any, Dict, List, Optional
import threading

class Graph:
    """Thread-safe graph for Cytoscape elements with optional compound nodes (parent field)."""
    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def add_node(
        self,
        id_: str,
        label: str,
        type_: str,
        region: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        parent: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> None:
        if not id_:
            return
        with self._lock:
            if id_ in self._nodes:
                if details:
                    self._nodes[id_]["data"]["details"].update(details)
                # allow filling parent later
                if parent and not self._nodes[id_]["data"].get("parent"):
                    self._nodes[id_]["data"]["parent"] = parent
                if account_id and not self._nodes[id_]["data"].get("account_id"):
                    self._nodes[id_]["data"]["account_id"] = account_id
                return
            self._nodes[id_] = {
                "data": {
                    "id": id_,
                    "label": label,
                    "type": type_,
                    "region": region or "",
                    "details": details or {},
                    "parent": parent,
                    "account_id": account_id or "",
                }
            }

    def add_edge(
        self,
        id_: str,
        source: str,
        target: str,
        label: str,
        type_: str,
        category: str,
        details: Optional[Dict[str, Any]] = None,
        derived: bool = False,
    ) -> None:
        if not id_ or not source or not target:
            return
        with self._lock:
            if id_ in self._edges:
                return
            self._edges[id_] = {
                "data": {
                    "id": id_,
                    "source": source,
                    "target": target,
                    "label": label,
                    "type": type_,            # attach|assoc|route|sg-rule|listener|bind|invoke|publish|subscribe
                    "category": category,      # resource|network|data
                    "derived": bool(derived),
                    "details": details or {},
                }
            }

    def set_parent(self, child_id: str, parent_id: Optional[str]) -> None:
        with self._lock:
            if child_id in self._nodes:
                self._nodes[child_id]["data"]["parent"] = parent_id

    def elements(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._nodes.values()) + list(self._edges.values())
