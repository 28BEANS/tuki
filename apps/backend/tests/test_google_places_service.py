"""Tests for place-detail normalization and service-area enforcement."""

import httpx
import pytest

from app.core.exceptions import ExternalServiceError
from app.services.google_places_service import GooglePlacesService


@pytest.mark.anyio
async def test_place_details_returns_exact_coordinate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = httpx.Response(
        200,
        json={
            "status": "OK",
            "result": {
                "place_id": "hau",
                "name": "Holy Angel University",
                "formatted_address": "Holy Angel Street, Angeles",
                "geometry": {
                    "location": {
                        "lat": 15.133078,
                        "lng": 120.590011,
                    }
                },
            },
        },
        request=httpx.Request("GET", "https://example.test"),
    )

    async def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        return response

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    service = GooglePlacesService()

    result = await service.place_details("hau")

    assert result["name"] == "Holy Angel University"
    assert result["latitude"] == 15.133078
    assert result["longitude"] == 120.590011


@pytest.mark.anyio
async def test_place_details_rejects_places_outside_service_area(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = httpx.Response(
        200,
        json={
            "status": "OK",
            "result": {
                "place_id": "manila",
                "name": "Manila",
                "geometry": {
                    "location": {
                        "lat": 14.5995,
                        "lng": 120.9842,
                    }
                },
            },
        },
        request=httpx.Request("GET", "https://example.test"),
    )

    async def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        return response

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    service = GooglePlacesService()

    with pytest.raises(ExternalServiceError, match="outside"):
        await service.place_details("manila")
