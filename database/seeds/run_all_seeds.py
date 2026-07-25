"""
Tuki Database — Seed Orchestrator

Runs all seed scripts in the correct order.
All scripts are idempotent and safe to re-run.

Usage:
    python -m database.seeds.run_all_seeds
"""

import asyncio
import logging
import os

logger = logging.getLogger("tuki.seeds")


async def run_all(database_url: str) -> None:
    """Run all seed scripts in order."""
    from database.seeds.seed_barangays import seed_barangays
    from database.seeds.seed_fare_matrix import seed_fare_matrix
    from database.seeds.seed_jeep_routes import seed_jeep_routes
    from database.seeds.seed_landmarks import seed_landmarks
    from database.seeds.seed_stop_coordinates import seed_coordinates

    logger.info("=" * 60)
    logger.info("TUKI DATABASE SEEDING")
    logger.info("=" * 60)

    # 1. Barangays (no dependencies)
    logger.info("\n[1/5] Seeding barangays...")
    barangay_count = await seed_barangays(database_url)
    logger.info("✓ %d barangays seeded", barangay_count)

    # 2. Jeep routes (no dependencies)
    logger.info("\n[2/5] Seeding jeepney routes...")
    route_count = await seed_jeep_routes(database_url)
    logger.info("✓ %d routes seeded", route_count)

    # 3. Stop coordinates and transfers (depends on routes and stops)
    logger.info("\n[3/5] Updating stop coordinates and transfer points...")
    await seed_coordinates(database_url)

    # 4. Fare matrix (no dependencies)
    logger.info("\n[4/5] Seeding fare matrix...")
    fare_count = await seed_fare_matrix(database_url)
    logger.info("✓ %d fare entries seeded", fare_count)

    # 5. Landmarks (depends on barangays for FK, but FK is nullable)
    logger.info("\n[5/5] Seeding landmarks...")
    landmark_count = await seed_landmarks(database_url)
    logger.info("✓ %d landmarks seeded", landmark_count)

    logger.info("\n" + "=" * 60)
    logger.info("SEEDING COMPLETE")
    logger.info(
        "Totals: %d barangays, %d routes, %d fare entries, %d landmarks",
        barangay_count,
        route_count,
        fare_count,
        landmark_count,
    )
    logger.info("=" * 60)

    logger.info(
        "\nNote: Run 'python -m database.osm.download_walking_network' "
        "separately to import the OSM walking network."
    )


async def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tuki"
    ).replace("postgresql+asyncpg://", "postgresql://")

    await run_all(database_url)


if __name__ == "__main__":
    asyncio.run(main())
