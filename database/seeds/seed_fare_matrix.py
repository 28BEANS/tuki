"""
Tuki Database — Fare Matrix Seed Script

Seeds the national fare matrix (LTFRB Traditional PUJ, October 2023).
Idempotent: clears and reinserts all entries.

Usage:
    python -m database.seeds.seed_fare_matrix

Source: Fare-Guide_Traditional-PUJ-Provisional-Fare-Increase_08Oct2023.pdf
"""

import asyncio
import logging
import os

import asyncpg

logger = logging.getLogger("tuki.seeds.fare_matrix")

# LTFRB Traditional PUJ Fare Matrix (October 2023)
# Distance-based fare brackets
FARE_MATRIX = [
    # (distance_km, regular_fare, discounted_fare, student_fare)
    (4.0, 13.00, 10.40, 10.40),
    (5.0, 14.80, 11.84, 11.84),
    (6.0, 16.60, 13.28, 13.28),
    (7.0, 18.40, 14.72, 14.72),
    (8.0, 20.20, 16.16, 16.16),
    (9.0, 22.00, 17.60, 17.60),
    (10.0, 23.80, 19.04, 19.04),
    (11.0, 25.60, 20.48, 20.48),
    (12.0, 27.40, 21.92, 21.92),
    (13.0, 29.20, 23.36, 23.36),
    (14.0, 31.00, 24.80, 24.80),
    (15.0, 32.80, 26.24, 26.24),
    (16.0, 34.60, 27.68, 27.68),
    (17.0, 36.40, 29.12, 29.12),
    (18.0, 38.20, 30.56, 30.56),
    (19.0, 40.00, 32.00, 32.00),
    (20.0, 41.80, 33.44, 33.44),
]


async def seed_fare_matrix(database_url: str) -> int:
    """Seed the fare matrix into the database."""
    conn = await asyncpg.connect(database_url)
    count = 0

    try:
        # Clear existing entries for idempotency
        await conn.execute(
            "DELETE FROM fare_matrix WHERE transport_type = 'traditional_puj'"
        )

        for distance_km, regular, discounted, student in FARE_MATRIX:
            await conn.execute(
                """
                INSERT INTO fare_matrix (id, transport_type, distance_km, regular_fare, discounted_fare, student_fare, created_at, updated_at)
                VALUES (gen_random_uuid(), 'traditional_puj', $1, $2, $3, $4, NOW(), NOW())
                """,
                distance_km, regular, discounted, student,
            )
            count += 1

        logger.info("Successfully seeded %d fare matrix entries", count)

    finally:
        await conn.close()

    return count


async def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")
    await seed_fare_matrix(database_url)


if __name__ == "__main__":
    asyncio.run(main())
