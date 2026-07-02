"""
Tuki Database — OSM Walking Network Download Script

Downloads Angeles City's walking network from OpenStreetMap using OSMnx.
Converts to walking_nodes and walking_edges tables in PostGIS.

Usage:
    python -m database.osm.download_walking_network

Requires:
    - osmnx
    - asyncpg
    - DATABASE_URL environment variable
"""

import asyncio
import logging
import os

logger = logging.getLogger("tuki.osm.walking")

# Angeles City bounding box (approximate)
ANGELES_CITY_PLACE = "Angeles City, Pampanga, Philippines"


async def download_and_import(database_url: str) -> tuple[int, int]:
    """
    Download Angeles City walking network and import to PostGIS.

    Returns (node_count, edge_count).
    """
    try:
        import osmnx as ox
    except ImportError:
        logger.error("osmnx is required. Install with: pip install osmnx")
        return 0, 0

    import asyncpg

    logger.info("Downloading walking network for %s...", ANGELES_CITY_PLACE)

    # Download the walking network
    G = ox.graph_from_place(
        ANGELES_CITY_PLACE,
        network_type="walk",
        simplify=True,
    )

    nodes, edges = ox.graph_to_gdfs(G)
    logger.info(
        "Downloaded: %d nodes, %d edges",
        len(nodes), len(edges),
    )

    # Connect to database
    conn = await asyncpg.connect(database_url)
    node_count = 0
    edge_count = 0

    try:
        # Clear existing walking data
        await conn.execute("DELETE FROM walking_edges")
        await conn.execute("DELETE FROM walking_nodes")

        # Import nodes
        for osm_id, row in nodes.iterrows():
            await conn.execute(
                """
                INSERT INTO walking_nodes (id, osm_id, geometry)
                VALUES (gen_random_uuid(), $1, ST_SetSRID(ST_MakePoint($2, $3), 4326))
                """,
                int(osm_id), float(row.geometry.x), float(row.geometry.y),
            )
            node_count += 1

        logger.info("Imported %d walking nodes", node_count)

        # Build OSM ID → UUID lookup
        rows = await conn.fetch("SELECT id, osm_id FROM walking_nodes")
        osm_to_uuid = {row["osm_id"]: row["id"] for row in rows}

        # Import edges
        for (u, v, _), row in edges.iterrows():
            source_uuid = osm_to_uuid.get(int(u))
            target_uuid = osm_to_uuid.get(int(v))

            if not source_uuid or not target_uuid:
                continue

            length_m = float(row.get("length", 0))
            highway_type = str(row.get("highway", ""))
            if isinstance(highway_type, list):
                highway_type = highway_type[0] if highway_type else ""

            # Create LineString from source/target points
            source_node = nodes.loc[u]
            target_node = nodes.loc[v]

            await conn.execute(
                """
                INSERT INTO walking_edges (id, source_node_id, target_node_id, geometry, length_m, highway_type)
                VALUES (
                    gen_random_uuid(), $1, $2,
                    ST_SetSRID(ST_MakeLine(
                        ST_MakePoint($3, $4),
                        ST_MakePoint($5, $6)
                    ), 4326),
                    $7, $8
                )
                """,
                source_uuid, target_uuid,
                float(source_node.geometry.x), float(source_node.geometry.y),
                float(target_node.geometry.x), float(target_node.geometry.y),
                length_m, highway_type,
            )
            edge_count += 1

        logger.info("Imported %d walking edges", edge_count)

    finally:
        await conn.close()

    return node_count, edge_count


async def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")
    nodes, edges = await download_and_import(database_url)
    print(f"Imported {nodes} nodes and {edges} edges")


if __name__ == "__main__":
    asyncio.run(main())
