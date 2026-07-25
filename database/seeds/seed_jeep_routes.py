"""
Tuki Database — Jeepney Routes Seed Script

Seeds jeepney route metadata and stops from reference data.
Idempotent: uses upsert on route_name and stop_name.

Usage:
    python -m database.seeds.seed_jeep_routes

Note:
    Route geometries will be added when GeoJSON route files are available.
    This script seeds metadata extracted from the reference maps.
"""

import asyncio
import logging
import os

import asyncpg

logger = logging.getLogger("tuki.seeds.jeep_routes")

# Angeles City jeepney routes from reference maps
ROUTES = [
    {
        "route_name": "Main Gate – Friendship",
        "route_color": "Sand",
        "description": "Runs along Perimeter Road (Don Juico Avenue) from the Main Gate to Friendship Highway.",
        "operating_direction": "bidirectional",
        "stops": ["Main Gate", "Checkpoint", "Don Juico Avenue", "Friendship Highway"],
    },
    {
        "route_name": "C'Point – Balibago – H'way",
        "route_color": "Grey",
        "description": "Checkpoint through Fields, Balibago to Highway via Arayat Road.",
        "operating_direction": "bidirectional",
        "stops": [
            "Checkpoint",
            "Fields Avenue",
            "Johnnies",
            "Marlim",
            "SR Lim",
            "Robinsons",
            "Crossing",
            "Richtofen Crossing",
            "Pampang Market",
            "San Nicolas",
            "Rizal",
            "Jenra Mall",
            "Plaridel",
        ],
    },
    {
        "route_name": "SM City – Main Gate – Dau",
        "route_color": "Various",
        "description": "Runs from the Main Gate along First Street, MacArthur Highway to Jumbo Jenra, Dau, Mabalacat Bus Terminal.",
        "operating_direction": "bidirectional",
        "stops": [
            "Main Gate",
            "First Street",
            "MacArthur Highway",
            "Jumbo Jenra",
            "Dau",
            "Mabalacat Bus Terminal",
        ],
    },
    {
        "route_name": "Checkpoint – Hensonville – Holy",
        "route_color": "White",
        "description": "Runs from Narciso Street, through Hensonville, to Holy Angel University and vice versa.",
        "operating_direction": "bidirectional",
        "stops": [
            "Narciso Street",
            "21st Street",
            "Hensonville",
            "Arayat Boulevard",
            "Holy Angel University",
        ],
    },
    {
        "route_name": "Sapang Bato – Angeles",
        "route_color": "Maroon",
        "description": "Sapang Bato through Friendship to Pampang Market area.",
        "operating_direction": "bidirectional",
        "stops": [
            "Sapang Bato",
            "Margot",
            "Friendship Highway",
            "Anunas",
            "Timog Park",
            "Carmenville",
            "City College",
            "Kalayaan",
            "Pampang Market",
        ],
    },
    {
        "route_name": "Checkpoint – Holy – Highway",
        "route_color": "Lavender",
        "description": "SM City through Fields, Robinsons, AUF, Holy, to Richtofen Crossing.",
        "operating_direction": "bidirectional",
        "stops": [
            "Main Gate",
            "First Street",
            "Fields Avenue",
            "Johnnies",
            "Marlim",
            "SR Lim",
            "Robinsons",
            "Marisol",
            "AUF",
            "Kuliat",
            "Lakandula",
            "Holy Angel University",
            "Holy",
            "Rizal",
            "Pampang Market",
            "Richtofen Crossing",
        ],
    },
    {
        "route_name": "Marisol – Pampang",
        "route_color": "Green",
        "description": "Marisol through AUF, Holy to Richtofen Crossing.",
        "operating_direction": "bidirectional",
        "stops": [
            "Marisol",
            "Magalang",
            "AUF",
            "Kuliat",
            "Lakandula",
            "Holy Angel University",
            "Holy",
            "Jenra Mall",
            "Plaridel",
            "San Nicolas",
            "Pampang Market",
            "Richtofen Crossing",
        ],
    },
    {
        "route_name": "Pandang – Pampang",
        "route_color": "Blue",
        "description": "City Hall area through MacArthur to Plaridel.",
        "operating_direction": "bidirectional",
        "stops": [
            "City Hall",
            "Mining",
            "MacArthur Highway",
            "Kuliat",
            "Pamintuan Residence",
            "Plaridel",
        ],
    },
    {
        "route_name": "Sunset – Nepo",
        "route_color": "Orange",
        "description": "Sunset area through Carmenville to Nepo Mart.",
        "operating_direction": "bidirectional",
        "stops": ["Sunset", "1976 Initial", "Champaca", "Nepo Mart"],
    },
    {
        "route_name": "Villa – Pampang – SM Telebestagen",
        "route_color": "Yellow",
        "description": "Villa Angela through Holy, Jenra Mall to Lakandula.",
        "operating_direction": "bidirectional",
        "stops": [
            "L&S",
            "Villa Angela",
            "Villa Gloria",
            "Villa Angelina",
            "Bale Herencia",
            "Holy Angel University",
            "Holy",
            "Jenra Mall",
            "Rizal",
            "San Nicolas",
            "Plaridel",
            "Pamintuan Residence",
            "Lakandula",
        ],
    },
    {
        "route_name": "Capaya – Angeles",
        "route_color": "Pink",
        "description": "Capaya through Mining, MacArthur to Plaridel.",
        "operating_direction": "bidirectional",
        "stops": [
            "Citicenter",
            "Mining",
            "MacArthur Highway",
            "Kuliat",
            "Plaridel",
        ],
    },
]


async def seed_jeep_routes(database_url: str) -> int:
    """Seed jeepney routes and stops into the database."""
    conn = await asyncpg.connect(database_url)
    route_count = 0

    try:
        # Clear existing data first to avoid orphaned stops/routes
        logger.info("Clearing existing jeep routes, stops, and associations...")
        await conn.execute(
            "TRUNCATE TABLE jeep_route_stops, jeep_routes, jeep_stops CASCADE"
        )

        for route_data in ROUTES:
            # Create a placeholder geometry (straight line will be replaced with real data)
            # For now, use a minimal valid geometry
            placeholder_geom = "MULTILINESTRING((120.58 15.14, 120.59 15.15))"

            # Upsert route
            route_id = await conn.fetchval(
                """
                INSERT INTO jeep_routes (id, route_name, route_color, description, operating_direction, geometry, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, ST_SetSRID(ST_GeomFromText($5), 4326), NOW(), NOW())
                ON CONFLICT (route_name) DO UPDATE SET
                    route_color = EXCLUDED.route_color,
                    description = EXCLUDED.description,
                    operating_direction = EXCLUDED.operating_direction,
                    updated_at = NOW()
                RETURNING id
                """,
                route_data["route_name"],
                route_data["route_color"],
                route_data["description"],
                route_data["operating_direction"],
                placeholder_geom,
            )

            # Seed stops
            for seq, stop_name in enumerate(route_data["stops"], 1):
                # Upsert stop (shared across routes)
                stop_id = await conn.fetchval(
                    """
                    INSERT INTO jeep_stops (id, stop_name, latitude, longitude, geometry, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, 0, 0, ST_SetSRID(ST_MakePoint(0, 0), 4326), NOW(), NOW())
                    ON CONFLICT (stop_name) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                    """,
                    stop_name,
                )

                # Link route to stop
                await conn.execute(
                    """
                    INSERT INTO jeep_route_stops (id, jeep_route_id, stop_id, sequence)
                    VALUES (gen_random_uuid(), $1, $2, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    route_id,
                    stop_id,
                    seq,
                )

            route_count += 1
            logger.info(
                "Seeded route: %s (%s)",
                route_data["route_name"],
                route_data["route_color"],
            )

        logger.info("Successfully seeded %d jeepney routes", route_count)

    finally:
        await conn.close()

    return route_count


async def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")
    await seed_jeep_routes(database_url)


if __name__ == "__main__":
    asyncio.run(main())
