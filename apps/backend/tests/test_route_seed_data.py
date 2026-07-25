"""Regression tests for the canonical Angeles City jeepney route data."""

import importlib.util
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

    missing = {
        stop for route in routes for stop in route["stops"] if stop not in coordinates
    }

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
