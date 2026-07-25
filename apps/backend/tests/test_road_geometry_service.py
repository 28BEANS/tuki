"""Tests for road-following route geometry."""

from unittest.mock import AsyncMock

import pytest

from app.services.road_geometry_service import (
    RoadGeometryService,
    decode_google_polyline,
)


def test_decodes_google_polyline() -> None:
    assert decode_google_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@") == [
        [38.5, -120.2],
        [40.7, -120.95],
        [43.252, -126.453],
    ]


@pytest.mark.anyio
async def test_google_geometry_is_anchored_to_exact_user_coordinates() -> None:
    service = RoadGeometryService(google_api_key="test-key")
    service._route_with_google = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            [15.133080, 120.590010],
            [15.150000, 120.590000],
            [15.167270, 120.580110],
        ]
    )
    coordinates = [
        [15.133078, 120.590011],
        [15.167271, 120.580113],
    ]

    geometry = await service.get_geometry(coordinates, "jeep")

    assert geometry[0] == coordinates[0]
    assert geometry[-1] == coordinates[-1]


@pytest.mark.anyio
async def test_implausible_provider_geometry_falls_back_to_ordered_anchors() -> None:
    service = RoadGeometryService(google_api_key="test-key")
    service._route_with_google = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            [14.5995, 120.9842],
            [14.6000, 120.9900],
        ]
    )
    service._route_with_osrm = AsyncMock(return_value=None)  # type: ignore[method-assign]
    coordinates = [
        [15.133078, 120.590011],
        [15.167271, 120.580113],
    ]

    geometry = await service.get_geometry(coordinates, "jeep")

    assert geometry == coordinates


@pytest.mark.anyio
async def test_walking_geometry_does_not_use_driving_fallback() -> None:
    service = RoadGeometryService(google_api_key="")
    service._route_with_osrm = AsyncMock()  # type: ignore[method-assign]
    coordinates = [
        [15.133078, 120.590011],
        [15.134258, 120.590159],
    ]

    geometry = await service.get_geometry(coordinates, "walk")

    assert geometry == coordinates
    service._route_with_osrm.assert_not_awaited()
