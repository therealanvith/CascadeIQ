from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import networkx as nx

NodeType = Literal["Vessel", "Port", "Warehouse", "Truck", "Delivery"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _iso_add_hours(iso: str, hours: float) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    dt2 = dt + timedelta(hours=float(hours))
    return dt2.replace(microsecond=0).isoformat()


def _severity(delay_hours: float) -> Literal["low", "medium", "high", "critical"]:
    if delay_hours >= 12:
        return "critical"
    if delay_hours >= 6:
        return "high"
    if delay_hours >= 2:
        return "medium"
    return "low"


SLA_THRESHOLDS: dict[NodeType, float] = {
    "Vessel": 24.0,
    "Port": 10.0,
    "Warehouse": 8.0,
    "Truck": 6.0,
    "Delivery": 6.0,
}

LOCAL_PROCESSING_DELAY: dict[NodeType, float] = {
    "Vessel": 0.0,
    "Port": 0.75,
    "Warehouse": 3.0,
    "Truck": 2.5,
    "Delivery": 2.5,
}


def build_supply_chain_graph() -> nx.DiGraph:
    """
    A small directed supply chain graph intended for demo + visualization.

    Includes a guaranteed demo chain for MV Endeavour:
    MV_ENDEAVOUR -> NHAVA_SHEVA_PORT -> WAREHOUSE_PUNE -> TRUCK_FLEET_A -> LAST_MILE_MUMBAI
    """
    g = nx.DiGraph()
    base_time = _now_iso()

    def add_node(node_id: str, node_type: NodeType, name: str, sla_hours: float | None = None) -> None:
        g.add_node(
            node_id,
            node_type=node_type,
            name=name,
            sla_hours=float(sla_hours if sla_hours is not None else SLA_THRESHOLDS[node_type]),
        )

    def add_edge(u: str, v: str, buffer_hours: float, expected_arrival_time: str | None = None) -> None:
        g.add_edge(
            u,
            v,
            buffer_hours=float(buffer_hours),
            expected_arrival_time=expected_arrival_time or _iso_add_hours(base_time, 6.0),
        )

    # Demo vessel chain (MV Endeavour)
    add_node("vessel:endeavour", "Vessel", "MV Endeavour")
    add_node("port:nhava_sheva", "Port", "Nhava Sheva Port")
    add_node("wh:pune", "Warehouse", "Warehouse Pune")
    add_node("truck:fleet_a", "Truck", "Truck Fleet A")
    add_node("delivery:last_mile_mumbai", "Delivery", "Last Mile Mumbai")

    # Buffer hours tuned so a 14h vessel delay yields the requested +3/+5/+6/+8 pattern downstream.
    # The engine also adds small per-node processing delays.
    add_edge("vessel:endeavour", "port:nhava_sheva", buffer_hours=11.75)
    add_edge("port:nhava_sheva", "wh:pune", buffer_hours=1.0)
    add_edge("wh:pune", "truck:fleet_a", buffer_hours=1.5)
    add_edge("truck:fleet_a", "delivery:last_mile_mumbai", buffer_hours=0.5)

    # Additional vessels/nodes to make the graph feel real.
    add_node("vessel:atlantic_star", "Vessel", "MV Atlantic Star")
    add_node("vessel:pacific_dawn", "Vessel", "MV Pacific Dawn")

    add_node("port:chennai", "Port", "Chennai Port")
    add_node("port:singapore", "Port", "Port of Singapore")
    add_node("port:dubai", "Port", "Jebel Ali Port (Dubai)")
    add_node("port:rotterdam", "Port", "Port of Rotterdam")

    add_node("wh:chennai", "Warehouse", "Warehouse Chennai")
    add_node("wh:dubai", "Warehouse", "Warehouse Dubai")
    add_node("wh:rotterdam", "Warehouse", "Warehouse Rotterdam")
    add_node("truck:fleet_b", "Truck", "Truck Fleet B")
    add_node("delivery:last_mile_dubai", "Delivery", "Last Mile Dubai")
    add_node("delivery:last_mile_rotterdam", "Delivery", "Last Mile Rotterdam")

    add_edge("vessel:atlantic_star", "port:chennai", buffer_hours=6.0)
    add_edge("port:chennai", "wh:chennai", buffer_hours=2.0)
    add_edge("wh:chennai", "truck:fleet_b", buffer_hours=1.5)
    add_edge("truck:fleet_b", "delivery:last_mile_dubai", buffer_hours=1.0)

    add_edge("vessel:pacific_dawn", "port:rotterdam", buffer_hours=7.0)
    add_edge("port:rotterdam", "wh:rotterdam", buffer_hours=1.5)
    add_edge("wh:rotterdam", "delivery:last_mile_rotterdam", buffer_hours=2.0)

    add_edge("vessel:endeavour", "port:singapore", buffer_hours=5.0)
    add_edge("port:singapore", "wh:dubai", buffer_hours=3.0)
    add_edge("wh:dubai", "delivery:last_mile_dubai", buffer_hours=2.0)

    add_edge("vessel:atlantic_star", "port:dubai", buffer_hours=6.0)
    add_edge("vessel:pacific_dawn", "port:rotterdam", buffer_hours=7.0)

    return g


def run_cascade(g: nx.DiGraph, vessel_id: str, delay_hours: float) -> dict[str, Any]:
    start = vessel_id
    if start not in g.nodes:
        return {"error": "unknown_vessel_id", "vessel_id": vessel_id, "affected": [], "steps": []}

    delay_hours = float(max(0.0, delay_hours))

    affected: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, Any]] = []

    q: deque[tuple[str, float, list[str]]] = deque()
    q.append((start, delay_hours, [start]))

    visited_best: dict[str, float] = {}  # node -> max delay seen (keep highest to be conservative)

    while q:
        node, incoming_delay, path = q.popleft()
        prev_best = visited_best.get(node)
        if prev_best is not None and incoming_delay <= prev_best + 1e-9:
            continue
        visited_best[node] = incoming_delay

        attrs = g.nodes[node]
        node_type: NodeType = attrs.get("node_type", "Vessel")
        sla_hours = float(attrs.get("sla_hours", SLA_THRESHOLDS.get(node_type, 8.0)))
        node_delay = float(incoming_delay + LOCAL_PROCESSING_DELAY.get(node_type, 0.0))
        sev = _severity(node_delay)
        sla_breached = bool(node_delay >= sla_hours)

        affected[node] = {
            "node_id": node,
            "node_type": node_type,
            "name": attrs.get("name", node),
            "delay_hours": round(node_delay, 2),
            "severity": sev,
            "sla_breached": sla_breached,
            "sla_hours": sla_hours,
            "path": path,
        }
        steps.append(
            {
                "node_id": node,
                "delay_hours": round(node_delay, 2),
                "severity": sev,
                "path": path,
            }
        )

        for nxt in g.successors(node):
            e = g.edges[node, nxt]
            buffer_hours = float(e.get("buffer_hours", 0.0))
            downstream = max(0.0, node_delay - buffer_hours)
            q.append((nxt, downstream, [*path, nxt]))

    # Deterministic ordering for UI animations: use BFS step order as collected.
    affected_list = list(affected.values())
    return {
        "vessel_id": vessel_id,
        "input_delay_hours": round(delay_hours, 2),
        "affected": affected_list,
        "steps": steps,
    }

