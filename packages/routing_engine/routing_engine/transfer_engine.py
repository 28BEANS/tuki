"""
Tuki Routing Engine — Transfer Engine

Identifies valid transfer points between routes.
"""

import logging
import math
from typing import Any

import networkx as nx

from routing_engine.graph_models import TransportMode

logger = logging.getLogger("tuki.routing.transfer")

# Maximum walking distance for a transfer (meters)
MAX_TRANSFER_WALK_M = 300.0


class TransferEngine:
    """
    Identifies and manages transfers between transport routes.

    A transfer is valid when:
    - Two routes have stops within walking distance of each other
    - A jeep stop is near a tricycle terminal
    - A route stop connects to the walking network
    """

    def find_transfers(
        self,
        graph: nx.MultiDiGraph,
        max_walk_m: float = MAX_TRANSFER_WALK_M,
    ) -> list[dict[str, Any]]:
        """
        Find all valid transfer points in the graph.

        Returns a list of transfer dicts with source/target info.
        """
        transfers: list[dict[str, Any]] = []
        nodes = dict(graph.nodes(data=True))

        # Find pairs of jeep stops on different routes within walking distance
        jeep_nodes = [
            (nid, data) for nid, data in nodes.items()
            if data.get("node_type") == TransportMode.JEEP.value
        ]

        for i, (id_a, data_a) in enumerate(jeep_nodes):
            for id_b, data_b in jeep_nodes[i + 1:]:
                # Skip if same route
                if data_a.get("route_id") == data_b.get("route_id"):
                    continue

                distance = _haversine_m(
                    data_a["latitude"], data_a["longitude"],
                    data_b["latitude"], data_b["longitude"],
                )

                if distance <= max_walk_m:
                    transfers.append({
                        "from_node": id_a,
                        "to_node": id_b,
                        "from_name": data_a.get("name"),
                        "to_name": data_b.get("name"),
                        "distance_m": round(distance, 1),
                        "transfer_type": "jeep_jeep",
                    })

        logger.info("Found %d potential transfers", len(transfers))
        return transfers

    def add_transfer_edges(
        self,
        graph: nx.MultiDiGraph,
        transfers: list[dict[str, Any]],
    ) -> int:
        """
        Add transfer edges to the graph.

        Returns the number of edges added.
        """
        count = 0
        for t in transfers:
            walk_time = (t["distance_m"] / 1000) / 4.5 * 60  # Walking speed

            # Bidirectional transfer
            for source, target in [
                (t["from_node"], t["to_node"]),
                (t["to_node"], t["from_node"]),
            ]:
                graph.add_edge(
                    source, target,
                    mode=TransportMode.TRANSFER.value,
                    distance_m=t["distance_m"],
                    fare=0.0,
                    travel_time_min=round(walk_time, 1),
                    weight_time=round(walk_time + 3.0, 1),  # Transfer penalty
                    weight_fare=0.0,
                )
                count += 1

        logger.info("Added %d transfer edges to graph", count)
        return count


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
