"""
Tuki Database — Landmark Seed Script

Seeds common Angeles City landmarks for search and navigation.
Idempotent: uses upsert on landmark name.

Usage:
    python -m database.seeds.seed_landmarks
"""

import asyncio
import logging
import os

import asyncpg

logger = logging.getLogger("tuki.seeds.landmarks")

# Common Angeles City landmarks
# Format: (name, category, latitude, longitude, aliases)
LANDMARKS = [
    # Schools
    ("Holy Angel University", "school", 15.1285, 120.5970, ["HAU"]),
    ("Angeles University Foundation", "school", 15.1380, 120.5910, ["AUF"]),
    ("City College of Angeles", "school", 15.1390, 120.5760, ["City College"]),

    # Malls
    ("SM City Clark", "mall", 15.1688, 120.5773, ["SM Clark"]),
    ("Jenra Mall", "mall", 15.1370, 120.5915, ["Jenra"]),
    ("Nepo Mart", "mall", 15.1275, 120.5870, ["Nepo"]),
    ("Robinsons Starmills", "mall", 15.1435, 120.5900, ["Robinsons", "Starmills"]),
    ("Marquee Mall", "mall", 15.1510, 120.5850, ["Marquee"]),

    # Hospitals
    ("Angeles University Foundation Medical Center", "hospital", 15.1375, 120.5905, ["AUF Medical"]),
    ("The Medical City Clark", "hospital", 15.1550, 120.5800, ["TMC Clark"]),
    ("Sacred Heart Medical Center", "hospital", 15.1340, 120.5890, ["Sacred Heart"]),

    # Government
    ("Angeles City Hall", "government", 15.1340, 120.5750, ["City Hall"]),

    # Churches
    ("Holy Rosary Parish Church", "church", 15.1295, 120.5945, ["Holy Rosary"]),

    # Terminals
    ("Dau Mabalacat Bus Terminal", "terminal", 15.1830, 120.5800, ["Dau Terminal", "Dau"]),
    ("Main Gate Checkpoint", "terminal", 15.1640, 120.5680, ["Main Gate", "Checkpoint"]),

    # Markets
    ("Pampang Market", "market", 15.1400, 120.5920, ["Pampang"]),

    # Restaurants & Food
    ("Everybody's Cafe", "restaurant", 15.1430, 120.5870, ["Everybody's"]),

    # Hotels
    ("Swagman Hotel", "hotel", 15.1580, 120.5700, ["Swagman"]),

    # Parks
    ("Timog Park", "park", 15.1520, 120.5630, ["Timog"]),
]


async def seed_landmarks(database_url: str) -> int:
    """Seed landmarks into the database."""
    conn = await asyncpg.connect(database_url)
    count = 0

    try:
        for name, category, lat, lon, aliases in LANDMARKS:
            await conn.execute(
                """
                INSERT INTO landmarks (id, name, aliases, category, latitude, longitude, geometry, created_at, updated_at)
                VALUES (
                    gen_random_uuid(), $1, $2, $3, $4, $5,
                    ST_SetSRID(ST_MakePoint($5, $4), 4326),
                    NOW(), NOW()
                )
                ON CONFLICT (name) DO UPDATE SET
                    aliases = EXCLUDED.aliases,
                    category = EXCLUDED.category,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    geometry = EXCLUDED.geometry,
                    updated_at = NOW()
                """,
                name, aliases, category, lat, lon,
            )
            count += 1

        logger.info("Successfully seeded %d landmarks", count)

    finally:
        await conn.close()

    return count


async def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")
    await seed_landmarks(database_url)


if __name__ == "__main__":
    asyncio.run(main())
