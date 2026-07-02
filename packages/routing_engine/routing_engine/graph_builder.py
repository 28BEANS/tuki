"""
Tuki Routing Engine — Graph Builder

Constructs a NetworkX MultiDiGraph from transportation data.
The graph represents Angeles City's complete transportation network.
"""

import logging
from typing import Any

import networkx as nx

from routing_engine.graph_models import TransportEdge, TransportMode, TransportNode

logger = logging.getLogger("tuki.routing.graph_builder")


class TransportGraphBuilder:
    """
    Builds a NetworkX MultiDiGraph representing the transportation network.

    The graph has:
    - Nodes: jeep stops, walking intersections, transfer points, tricycle terminals
    - Edges: jeep rides, walking segments, tricycle rides, transfer connections

    Each edge carries: mode, distance, fare, travel_time
    """

    # Average speeds by mode (km/h)
    SPEEDS: dict[TransportMode, float] = {
        TransportMode.JEEP: 15.0,
        TransportMode.WALK: 4.5,
        TransportMode.TRICYCLE: 20.0,
        TransportMode.TRANSFER: 4.5,  # Walking speed for transfers
    }

    # Transfer penalty in minutes
    TRANSFER_PENALTY_MIN: float = 3.0

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def build(
        self,
        nodes: list[TransportNode],
        edges: list[TransportEdge],
    ) -> nx.MultiDiGraph:
        """
        Build the complete transportation graph.

        Args:
            nodes: All transport nodes (stops, intersections, terminals).
            edges: All transport edges (routes, walks, rides).

        Returns:
            NetworkX MultiDiGraph with node and edge attributes.
        """
        self.graph.clear()

        # Add nodes
        for node in nodes:
            self.graph.add_node(
                node.id,
                name=node.name,
                latitude=node.latitude,
                longitude=node.longitude,
                node_type=node.node_type.value,
                route_id=node.route_id,
            )

        logger.info("Added %d nodes to transport graph", len(nodes))

        # Add edges
        for edge in edges:
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                mode=edge.mode.value,
                distance_m=edge.distance_m,
                fare=edge.fare,
                travel_time_min=edge.travel_time_min,
                route_name=edge.route_name,
                route_color=edge.route_color,
                weight_time=edge.weight_time,
                weight_fare=edge.weight_fare,
            )

        logger.info("Added %d edges to transport graph", len(edges))
        logger.info(
            "Graph summary: %d nodes, %d edges",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

        return self.graph

    def add_walking_network(
        self,
        walking_nodes: list[dict[str, Any]],
        walking_edges: list[dict[str, Any]],
    ) -> None:
        """
        Add OSM walking network to the graph.

        Args:
            walking_nodes: List of dicts with keys: id, latitude, longitude
            walking_edges: List of dicts with keys: source_id, target_id, length_m
        """
        for node in walking_nodes:
            node_id = f"walk_{node['id']}"
            self.graph.add_node(
                node_id,
                name=f"Walking Node {node['id']}",
                latitude=node["latitude"],
                longitude=node["longitude"],
                node_type=TransportMode.WALK.value,
            )

        for edge in walking_edges:
            source = f"walk_{edge['source_id']}"
            target = f"walk_{edge['target_id']}"
            length_m = edge["length_m"]
            time_min = (length_m / 1000) / self.SPEEDS[TransportMode.WALK] * 60

            # Bidirectional walking
            for s, t in [(source, target), (target, source)]:
                self.graph.add_edge(
                    s, t,
                    mode=TransportMode.WALK.value,
                    distance_m=length_m,
                    fare=0.0,
                    travel_time_min=round(time_min, 1),
                    weight_time=round(time_min, 1),
                    weight_fare=0.0,
                )

        logger.info(
            "Added walking network: %d nodes, %d edges",
            len(walking_nodes),
            len(walking_edges) * 2,
        )

    def connect_stops_to_walking_network(
        self,
        stop_to_walking_map: dict[str, str],
        connection_distance_m: float = 50.0,
    ) -> None:
        """
        Connect transport stops to their nearest walking network nodes.

        This enables seamless transitions between riding and walking.
        """
        time_min = (connection_distance_m / 1000) / self.SPEEDS[TransportMode.WALK] * 60

        for stop_id, walk_node_id in stop_to_walking_map.items():
            for s, t in [(stop_id, walk_node_id), (walk_node_id, stop_id)]:
                self.graph.add_edge(
                    s, t,
                    mode=TransportMode.TRANSFER.value,
                    distance_m=connection_distance_m,
                    fare=0.0,
                    travel_time_min=round(time_min, 1),
                    weight_time=round(time_min + self.TRANSFER_PENALTY_MIN, 1),
                    weight_fare=0.0,
                )

        logger.info(
            "Connected %d stops to walking network", len(stop_to_walking_map)
        )
