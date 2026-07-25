"""
Road-following geometry for route segments.

Google Routes is the primary geometry provider when configured. Driving
segments fall back to OSRM, while every failure safely falls back to the
authoritative ordered graph coordinates.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger("tuki.services.road_geometry")

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
OSRM_ROUTES_URL = "https://router.project-osrm.org/route/v1/driving"

_PROVIDER_ENDPOINT_TOLERANCE_M = 200.0
_MAX_GEOMETRY_DETOUR_FACTOR = 5.0
_MIN_MAX_GEOMETRY_LENGTH_M = 2_000.0


class RoadGeometryService:
    """Resolve ordered coordinates to a continuous, road-following polyline."""

    def __init__(self, google_api_key: str | None = None) -> None:
        settings = get_settings()
        self._google_api_key = (
            google_api_key if google_api_key is not None else settings.google_maps_api_key
        )

    async def get_geometry(
        self,
        coordinates: Sequence[Sequence[float]],
        mode: str,
    ) -> list[list[float]]:
        """
        Return an ordered ``[lat, lon]`` polyline anchored to exact endpoints.

        Provider geometry is accepted only when its endpoints and total length
        are plausible for the requested ordered coordinates.
        """
        anchors = _normalise_coordinates(coordinates)
        if len(anchors) < 2:
            return anchors

        geometry: list[list[float]] | None = None

        if self._google_api_key:
            geometry = await self._route_with_google(anchors, mode)
            if geometry and not _is_plausible_geometry(geometry, anchors):
                logger.warning("Discarding implausible Google route geometry")
                geometry = None

        if geometry is None and mode not in ("walk", "transfer"):
            geometry = await self._route_with_osrm(anchors)
            if geometry and not _is_plausible_geometry(geometry, anchors):
                logger.warning("Discarding implausible OSRM route geometry")
                geometry = None

        return _anchor_geometry(geometry or anchors, anchors[0], anchors[-1])

    async def _route_with_google(
        self,
        coordinates: list[list[float]],
        mode: str,
    ) -> list[list[float]] | None:
        body: dict[str, Any] = {
            "origin": _google_waypoint(coordinates[0]),
            "destination": _google_waypoint(coordinates[-1]),
            "travelMode": "WALK" if mode in ("walk", "transfer") else "DRIVE",
            "polylineQuality": "HIGH_QUALITY",
            "polylineEncoding": "ENCODED_POLYLINE",
            "computeAlternativeRoutes": False,
        }
        if len(coordinates) > 2:
            body["intermediates"] = [
                _google_waypoint(coordinate) for coordinate in coordinates[1:-1]
            ]
        if body["travelMode"] == "DRIVE":
            body["routingPreference"] = "TRAFFIC_UNAWARE"

        headers = {
            "X-Goog-Api-Key": self._google_api_key,
            "X-Goog-FieldMask": "routes.polyline.encodedPolyline",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    GOOGLE_ROUTES_URL,
                    json=body,
                    headers=headers,
                )
            response.raise_for_status()
            routes = response.json().get("routes", [])
            if not routes:
                return None
            encoded = routes[0].get("polyline", {}).get("encodedPolyline")
            if not encoded:
                return None
            return decode_google_polyline(encoded)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            logger.warning("Google Routes geometry failed: %s", exc)
            return None

    async def _route_with_osrm(
        self,
        coordinates: list[list[float]],
    ) -> list[list[float]] | None:
        coordinate_path = ";".join(f"{longitude},{latitude}" for latitude, longitude in coordinates)
        url = f"{OSRM_ROUTES_URL}/{coordinate_path}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                return None
            geometry = data["routes"][0]["geometry"]["coordinates"]
            return [[float(latitude), float(longitude)] for longitude, latitude in geometry]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            logger.warning("OSRM geometry failed: %s", exc)
            return None


def decode_google_polyline(encoded: str) -> list[list[float]]:
    """Decode a Google encoded polyline into ordered ``[lat, lon]`` points."""
    coordinates: list[list[float]] = []
    index = 0
    latitude = 0
    longitude = 0

    while index < len(encoded):
        latitude_delta, index = _decode_polyline_value(encoded, index)
        longitude_delta, index = _decode_polyline_value(encoded, index)
        latitude += latitude_delta
        longitude += longitude_delta
        coordinates.append([latitude / 100_000, longitude / 100_000])

    return coordinates


def _decode_polyline_value(encoded: str, index: int) -> tuple[int, int]:
    result = 0
    shift = 0

    while True:
        if index >= len(encoded):
            raise ValueError("Truncated encoded polyline")
        value = ord(encoded[index]) - 63
        index += 1
        result |= (value & 0x1F) << shift
        shift += 5
        if value < 0x20:
            break

    delta = ~(result >> 1) if result & 1 else result >> 1
    return delta, index


def _google_waypoint(coordinate: Sequence[float]) -> dict[str, Any]:
    return {
        "location": {
            "latLng": {
                "latitude": coordinate[0],
                "longitude": coordinate[1],
            }
        }
    }


def _normalise_coordinates(
    coordinates: Sequence[Sequence[float]],
) -> list[list[float]]:
    result: list[list[float]] = []
    for coordinate in coordinates:
        if len(coordinate) < 2:
            continue
        point = [float(coordinate[0]), float(coordinate[1])]
        if not (-90 <= point[0] <= 90 and -180 <= point[1] <= 180):
            continue
        if not result or _haversine_m(result[-1], point) >= 0.5:
            result.append(point)
    return result


def _anchor_geometry(
    geometry: list[list[float]],
    origin: list[float],
    destination: list[float],
) -> list[list[float]]:
    anchored = [point.copy() for point in geometry]

    if not anchored or _haversine_m(anchored[0], origin) >= 0.5:
        anchored.insert(0, origin.copy())
    else:
        anchored[0] = origin.copy()

    if _haversine_m(anchored[-1], destination) >= 0.5:
        anchored.append(destination.copy())
    else:
        anchored[-1] = destination.copy()

    return anchored


def _is_plausible_geometry(
    geometry: list[list[float]],
    anchors: list[list[float]],
) -> bool:
    if len(geometry) < 2:
        return False
    if _haversine_m(geometry[0], anchors[0]) > _PROVIDER_ENDPOINT_TOLERANCE_M:
        return False
    if _haversine_m(geometry[-1], anchors[-1]) > _PROVIDER_ENDPOINT_TOLERANCE_M:
        return False

    anchor_length = _polyline_length_m(anchors)
    geometry_length = _polyline_length_m(geometry)
    maximum_length = max(
        _MIN_MAX_GEOMETRY_LENGTH_M,
        anchor_length * _MAX_GEOMETRY_DETOUR_FACTOR,
    )
    return geometry_length <= maximum_length


def _polyline_length_m(coordinates: Sequence[Sequence[float]]) -> float:
    return sum(
        _haversine_m(source, target)
        for source, target in zip(
            coordinates,
            coordinates[1:],
            strict=False,
        )
    )


def _haversine_m(
    source: Sequence[float],
    target: Sequence[float],
) -> float:
    latitude1, longitude1 = source
    latitude2, longitude2 = target
    radius_m = 6_371_000.0
    phi1 = math.radians(latitude1)
    phi2 = math.radians(latitude2)
    delta_phi = math.radians(latitude2 - latitude1)
    delta_lambda = math.radians(longitude2 - longitude1)
    haversine = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return (
        radius_m
        * 2
        * math.atan2(
            math.sqrt(haversine),
            math.sqrt(1 - haversine),
        )
    )
