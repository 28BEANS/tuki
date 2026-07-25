"""Regression tests for the canonical Angeles City jeepney route data."""

import importlib.util
import math
from pathlib import Path
from types import ModuleType


def _load_seed_module(filename: str) -> ModuleType:
    path = Path(__file__).parents[3] / "database" / "seeds" / filename
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_seeded_stop_has_coordinates() -> None:
    routes = _load_seed_module("seed_jeep_routes.py").ROUTES
    coordinates = _load_seed_module("seed_stop_coordinates.py").STOP_COORDS

    missing = {stop for route in routes for stop in route["stops"] if stop not in coordinates}

    assert missing == set()


def test_routes_follow_the_canonical_reference_order() -> None:
    routes = {
        route["route_name"]: route["stops"]
        for route in _load_seed_module("seed_jeep_routes.py").ROUTES
    }

    assert routes["Pandang – Pampang"] == [
        "City Hall",
        "Mining",
        "MacArthur Highway",
        "Kuliat",
        "Pamintuan Residence",
        "Plaridel",
    ]
    assert routes["Capaya – Angeles"] == [
        "Citicenter",
        "Mining",
        "MacArthur Highway",
        "Kuliat",
        "Plaridel",
    ]
    assert routes["Checkpoint – Holy – Highway"][-5:] == [
        "Holy Angel University",
        "Holy",
        "Rizal",
        "Pampang Market",
        "Richtofen Crossing",
    ]


def test_route_coordinates_do_not_create_multi_kilometre_spikes() -> None:
    routes = _load_seed_module("seed_jeep_routes.py").ROUTES
    coordinates = _load_seed_module("seed_stop_coordinates.py").STOP_COORDS

    for route in routes:
        for source_name, target_name in zip(route["stops"], route["stops"][1:], strict=False):
            source = coordinates[source_name]
            target = coordinates[target_name]
            distance_km = _haversine_km(source, target)
            assert distance_km < 4.5, (
                f"{route['route_name']} jumps {distance_km:.1f}km "
                f"from {source_name} to {target_name}"
            )


def _haversine_km(
    source: tuple[float, float],
    target: tuple[float, float],
) -> float:
    lat1, lon1 = source
    lat2, lon2 = target
    radius_km = 6_371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    haversine = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return (
        radius_km
        * 2
        * math.atan2(
            math.sqrt(haversine),
            math.sqrt(1 - haversine),
        )
    )
