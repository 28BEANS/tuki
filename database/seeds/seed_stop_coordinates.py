"""
Tuki Database — Stop Coordinates & Transfer Points Seed Script

Updates the coordinates of jeepney stops to realistic coordinates in Angeles City,
and seeds transfer points between intersecting jeepney routes to enable full multimodal pathfinding.
"""

import asyncio
import logging
import os

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
    "21st Street": (15.165710, 120.578999),
    "AUF": (15.145126, 120.594639),
    "Anunas": (15.156127, 120.542301),
    "Arayat Boulevard": (15.149397, 120.579082),
    "Bale Herencia": (15.133564, 120.591951),
    "Carmenville": (15.142170, 120.570361),
    "Champaca": (15.125720, 120.588278),
    "Checkpoint": (15.166859, 120.582599),
    "Citicenter": (15.151004, 120.612077),
    "City College": (15.149849, 120.577912),
    "City Hall": (15.165494, 120.608261),
    "Crossing": (15.147175, 120.589446),
    "Dau": (15.177386, 120.589221),
    "Don Juico Avenue": (15.166466, 120.562779),
    "Fields Avenue": (15.167229, 120.586376),
    "First Street": (15.1680, 120.5780),
    "Friendship Highway": (15.1500, 120.5600),
    "Hensonville": (15.158876, 120.581788),
    "Holy Angel University": (15.133078, 120.590011),
    "Holy": (15.134258, 120.590159),
    "Jenra Mall": (15.136131, 120.587859),
    "Johnnies": (15.166230, 120.589911),
    "Jumbo Jenra": (15.1780, 120.5800),
    "Kalayaan": (15.142764, 120.582988),
    "Kuliat": (15.140618, 120.591729),
    "L&S": (15.121758, 120.596122),
    "Lakandula": (15.134772, 120.592729),
    "Mabalacat Bus Terminal": (15.177386, 120.589221),
    "MacArthur Highway": (15.147250, 120.594292),
    "Magalang": (15.160564, 120.609918),
    "Main Gate": (15.167119, 120.584410),
    "Margot": (15.170758, 120.534893),
    "Marisol": (15.152434, 120.600490),
    "Marlim": (15.162669, 120.592158),
    "Mining": (15.140641, 120.609038),
    "Narciso Street": (15.164460, 120.583304),
    "Nepo Mart": (15.135000, 120.586792),
    "Pamintuan Residence": (15.135789, 120.591448),
    "Pampang Market": (15.147136, 120.584807),
    "Plaridel": (15.137836, 120.588860),
    "Richtofen Crossing": (15.150660, 120.583970),
    "Rizal": (15.141692, 120.589246),
    "Robinsons": (15.157257, 120.591559),
    "SR Lim": (15.161106, 120.594963),
    "San Nicolas": (15.138509, 120.586187),
    "Sapang Bato": (15.1450, 120.5100),
    "Sunset": (15.141037, 120.569584),
    "Timog Park": (15.145248, 120.561925),
    "Villa Angela": (15.125907, 120.596459),
    "Villa Angelina": (15.131379, 120.592698),
    "Villa Gloria": (15.128135, 120.590754),
}

# Transfers between routes at shared hubs
TRANSFERS = [
    (
        "Main Gate – Friendship",
        "Checkpoint – Hensonville – Holy",
        "Checkpoint",
        "jeep_jeep",
    ),
    (
        "SM City – Main Gate – Dau",
        "Checkpoint – Holy – Highway",
        "Main Gate",
        "jeep_jeep",
    ),
    ("Checkpoint – Holy – Highway", "Sunset – Nepo", "Nepo Mart", "jeep_jeep"),
    (
        "Checkpoint – Hensonville – Holy",
        "Checkpoint – Holy – Highway",
        "Holy Angel University",
        "jeep_jeep",
    ),
    ("Marisol – Pampang", "Checkpoint – Holy – Highway", "AUF", "jeep_jeep"),
    (
        "Villa – Pampang – SM Telebestagen",
        "Checkpoint – Holy – Highway",
        "Holy Angel University",
        "jeep_jeep",
    ),
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
                lat,
                lon,
                stop_name,
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
                    f"Transfer at {stop_name}",
                    stop_geom,
                    from_route_id,
                    to_route_id,
                    transfer_type,
                )
                seeded_count += 1
            else:
                logger.warning(
                    "Skipping transfer %s → %s: one or more entities not found",
                    from_route,
                    to_route,
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
