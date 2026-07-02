"""
Tuki Backend — Google Places Service

Proxies Google Places API calls for autocomplete, search, and geocoding.
Google APIs are ONLY used for search/locate — never for routing.
"""

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger("tuki.services.google_places")

PLACES_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class GooglePlacesService:
    """
    Service for Google Places API interactions.

    Used ONLY for:
    - Place Autocomplete
    - Place Search / Details
    - Geocoding / Reverse Geocoding

    NEVER used for routing or directions.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.google_maps_api_key
        # Bias results toward Angeles City
        self.location_bias = "15.1450,120.5887"  # Angeles City center
        self.radius = 15000  # 15km radius

    async def autocomplete(
        self,
        query: str,
        session_token: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get place autocomplete predictions.

        Biased toward Angeles City, Pampanga.
        """
        params: dict[str, Any] = {
            "input": query,
            "key": self.api_key,
            "location": self.location_bias,
            "radius": self.radius,
            "components": "country:ph",
            "language": "en",
        }
        if session_token:
            params["sessiontoken"] = session_token

        async with httpx.AsyncClient() as client:
            response = await client.get(PLACES_AUTOCOMPLETE_URL, params=params)

        if response.status_code != 200:
            raise ExternalServiceError("Google Places", f"HTTP {response.status_code}")

        data = response.json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            raise ExternalServiceError("Google Places", data.get("error_message", "Unknown error"))

        return data.get("predictions", [])

    async def geocode(
        self,
        address: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Forward or reverse geocoding.

        Provide 'address' for forward geocoding, or 'lat'/'lon' for reverse.
        """
        params: dict[str, Any] = {
            "key": self.api_key,
            "language": "en",
        }

        if address:
            params["address"] = address
            params["components"] = "country:PH"
        elif lat is not None and lon is not None:
            params["latlng"] = f"{lat},{lon}"
        else:
            raise ExternalServiceError("Google Geocoding", "Provide address or lat/lon")

        async with httpx.AsyncClient() as client:
            response = await client.get(GEOCODING_URL, params=params)

        if response.status_code != 200:
            raise ExternalServiceError("Google Geocoding", f"HTTP {response.status_code}")

        data = response.json()
        return data.get("results", [])
