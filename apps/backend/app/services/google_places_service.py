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

_SERVICE_BOUNDS = {
    "south": 15.08,
    "west": 120.48,
    "north": 15.22,
    "east": 120.65,
}


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
            "strictbounds": "true",
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

    async def place_details(
        self,
        place_id: str,
        session_token: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a Google place ID to an exact coordinate inside Tuki's area."""
        params: dict[str, Any] = {
            "place_id": place_id,
            "fields": "place_id,name,formatted_address,geometry",
            "key": self.api_key,
            "language": "en",
        }
        if session_token:
            params["sessiontoken"] = session_token

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(PLACES_DETAILS_URL, params=params)

        if response.status_code != 200:
            raise ExternalServiceError(
                "Google Places",
                f"HTTP {response.status_code}",
            )

        data = response.json()
        if data.get("status") != "OK":
            raise ExternalServiceError(
                "Google Places",
                data.get("error_message", data.get("status", "Unknown error")),
            )

        result = data["result"]
        location = result["geometry"]["location"]
        latitude = float(location["lat"])
        longitude = float(location["lng"])
        if not (
            _SERVICE_BOUNDS["south"] <= latitude <= _SERVICE_BOUNDS["north"]
            and _SERVICE_BOUNDS["west"] <= longitude <= _SERVICE_BOUNDS["east"]
        ):
            raise ExternalServiceError(
                "Google Places",
                "Selected place is outside the Tuki service area",
            )

        return {
            "place_id": result.get("place_id", place_id),
            "name": result.get("name", result.get("formatted_address", "Selected place")),
            "formatted_address": result.get("formatted_address"),
            "latitude": latitude,
            "longitude": longitude,
        }

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
