"""
Tuki Database — Stop Coordinates & Transfer Points Seed Script

Updates the coordinates of jeepney stops to realistic coordinates in Angeles City,
and seeds transfer points between intersecting jeepney routes to enable full multimodal pathfinding.
"""

import asyncio
import logging
import os
import uuid
import asyncpg

logger = logging.getLogger("tuki.seeds.coordinates")

STOP_COORDS = {
    # Main Gate - Friendship (Sand)

    # C'Point - Balibago - H'way (Grey)

    # SM City - Main Gate - Dau (Various)

    # Checkpoint - Hensonville - Holy (White)

    # Sapang Bato - Angeles (Maroon)

    # Checkpoint - Holy - Highway (Lavender)

    # Marisol - Pampang (Green)

    # Pandang - Pampang (Blue)

    # Sunset - Nepo (Orange)

    # Villa - Pampang - SM Telebestagen (Yellow)

    # Capaya - Angeles (Pink)
    "1976 Initial": (15.1260, 120.5700),
    "21st Street": (15.1550, 120.5720),
    "AUF": (15.1380, 120.5910),
    "Anunas": (15.1480, 120.5700),
    "Arayat Boulevard": (15.1380, 120.5850),
    "Carmenville": (15.1350, 120.5680),
    "Champaca": (15.1250, 120.5800),
    "Checkpoint": (15.1640, 120.5680),
    "Citicenter": (15.1380, 120.6050),
    "City College": (15.1390, 120.5760),
    "City Hall": (15.1340, 120.5750),
    "Crossing": (15.1410, 120.5920),
    "Dau": (15.1830, 120.5800),
    "Don Juico Avenue": (15.1580, 120.5650),
    "Fields Avenue": (15.1620, 120.5720),
    "First Street": (15.1680, 120.5780),
    "Friendship Highway": (15.1500, 120.5600),
    "Hensonville": (15.1480, 120.5750),
    "Holy Angel University": (15.1285, 120.5970),
    "Jenra Mall": (15.1370, 120.5915),
    "Johnnies": (15.1600, 120.5750),
    "Jumbo Jenra": (15.1780, 120.5800),
    "Kalayaan": (15.1330, 120.5800),
    "Kuliat": (15.1330, 120.5930),
    "L&S": (15.1350, 120.6050),
    "Lakandula": (15.1310, 120.5940),
    "Mabalacat Bus Terminal": (15.1850, 120.5800),
    "MacArthur Highway": (15.1720, 120.5790),
    "Magalang": (15.1500, 120.6100),
    "Main Gate": (15.1688, 120.5773),
    "Margot": (15.1480, 120.5300),
    "Marisol": (15.1450, 120.5920),
    "Marlim": (15.1550, 120.5800),
    "Mining": (15.1300, 120.5800),
    "Narciso Street": (15.1600, 120.5690),
    "Nepo Mart": (15.1275, 120.5870),
    "Pamintuan Residence": (15.1280, 120.5960),
    "Pampang Market": (15.1400, 120.5920),
    "Plaridel": (15.1270, 120.5980),
    "Richtofen Crossing": (15.1380, 120.5930),
    "Rizal": (15.1300, 120.5950),
    "Robinsons": (15.1435, 120.5900),
    "SR Lim": (15.1500, 120.5850),
    "San Nicolas": (15.1350, 120.5940),
    "Sapang Bato": (15.1450, 120.5100),
    "Sunset": (15.1280, 120.5600),
    "Timog Park": (15.1520, 120.5630),
    "Villa Angela": (15.1320, 120.6020),
    "Villa Angelina": (15.1290, 120.5990),
    "Villa Gloria": (15.1300, 120.6000),
}

# Transfers between routes at shared hubs
TRANSFERS = [
    ("Main Gate – Friendship", "Checkpoint – Hensonville – Holy", "Checkpoint", "jeep_jeep"),
    ("SM City – Main Gate – Dau", "Checkpoint – Holy – Highway", "Main Gate", "jeep_jeep"),
    ("Checkpoint – Holy – Highway", "Sunset – Nepo", "Nepo Mart", "jeep_jeep"),
    ("Checkpoint – Hensonville – Holy", "Checkpoint – Holy – Highway", "Holy Angel University", "jeep_jeep"),
    ("Marisol – Pampang", "Checkpoint – Holy – Highway", "AUF", "jeep_jeep"),
    ("Villa – Pampang – SM Telebestagen", "Checkpoint – Holy – Highway", "Holy Angel University", "jeep_jeep")
]


async def seed_coordinates(database_url: str) -> None:
    conn = await asyncpg.connect(database_url)

    try:
        logger.info("Updating jeep stops with realistic coordinates...")
        updated_count = 0
        for stop_name, (lat, lon) in STOP_COORDS.items():
            result = await conn.execute(
                """
                UPDATE jeep_stops
                SET latitude = $1, longitude = $2,
                    geometry = ST_SetSRID(ST_MakePoint($2, $1), 4326),
                    updated_at = NOW()
                WHERE stop_name = $3
                """,
                lat, lon, stop_name
            )
            if "UPDATE 1" in result:
                updated_count += 1

        logger.info("✓ Updated %d jeepney stops with coordinates", updated_count)

        logger.info("Clearing existing transfer points...")
        await conn.execute("DELETE FROM transfer_points")

        logger.info("Seeding transfer points...")
        seeded_count = 0
        for from_route, to_route, stop_name, transfer_type in TRANSFERS:
            from_route_id = await conn.fetchval(
                "SELECT id FROM jeep_routes WHERE route_name = $1", from_route
            )
            to_route_id = await conn.fetchval(
                "SELECT id FROM jeep_routes WHERE route_name = $1", to_route
            )
            stop_geom = await conn.fetchval(
                "SELECT geometry FROM jeep_stops WHERE stop_name = $1", stop_name
            )

            if from_route_id and to_route_id and stop_geom:
                await conn.execute(
                    """
                    INSERT INTO transfer_points (id, name, geometry, from_route_id, to_route_id, transfer_type, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), NOW())
                    """,
                    f"Transfer at {stop_name}", stop_geom, from_route_id, to_route_id, transfer_type
                )
                seeded_count += 1
            else:
                logger.warning(
                    "Skipping transfer %s → %s: one or more entities not found",
                    from_route, to_route
                )

        logger.info("✓ Seeded %d transfer points", seeded_count)

    finally:
        await conn.close()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")
    await seed_coordinates(database_url)


if __name__ == "__main__":
    asyncio.run(main())