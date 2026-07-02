"""
Tuki Database — Barangay Seed Script

Imports Angeles City barangay boundaries from GeoJSON into PostGIS.
Idempotent: uses upsert on barangay_name.

Usage:
    python -m database.seeds.seed_barangays

Requires:
    - database/geojson/angeles-city-barangays.geojson
    - DATABASE_URL environment variable
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import asyncpg

logger = logging.getLogger("tuki.seeds.barangays")

# Path to GeoJSON file
GEOJSON_PATH = Path(__file__).parent.parent / "geojson" / "angeles-city-barangays.geojson"


async def seed_barangays(database_url: str) -> int:
    """
    Import barangay boundaries from GeoJSON into the database.

    Returns the number of barangays imported.
    """
    if not GEOJSON_PATH.exists():
        logger.error("GeoJSON file not found: %s", GEOJSON_PATH)
        sys.exit(1)

    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    logger.info("Found %d barangay features in GeoJSON", len(features))

    # Connect to database
    conn = await asyncpg.connect(database_url)
    count = 0

    try:
        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            name = props.get("name", "").strip()
            psgc_code = props.get("psgc", "").strip() or None

            if not name:
                logger.warning("Skipping feature with empty name: %s", props)
                continue

            # Convert geometry to GeoJSON string
            geom_json = json.dumps(geometry)

            # Upsert: insert or update on conflict
            await conn.execute(
                """
                INSERT INTO barangays (id, barangay_name, psgc_code, geometry, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON($3), 4326)), NOW(), NOW())
                ON CONFLICT (barangay_name) DO UPDATE SET
                    psgc_code = EXCLUDED.psgc_code,
                    geometry = EXCLUDED.geometry,
                    updated_at = NOW()
                """,
                name, psgc_code, geom_json,
            )
            count += 1

        logger.info("Successfully imported %d barangays", count)

    finally:
        await conn.close()

    return count


async def main() -> None:
    """CLI entry point."""
    import os
    logging.basicConfig(level=logging.INFO)

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/tuki",
    )
    # asyncpg uses plain postgresql:// not postgresql+asyncpg://
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    await seed_barangays(database_url)


if __name__ == "__main__":
    asyncio.run(main())
