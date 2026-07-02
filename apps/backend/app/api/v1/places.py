"""
Tuki Backend — Google Places Proxy Endpoints

Proxies Google APIs for autocomplete and geocoding.
Google is ONLY used for search/locate — never for routing.
"""

from fastapi import APIRouter, Query

from app.services.google_places_service import GooglePlacesService

router = APIRouter(prefix="/places")


@router.get("/autocomplete")
async def autocomplete(
    query: str = Query(..., min_length=1, description="Search text"),
    session_token: str | None = Query(None, description="Session token for billing"),
) -> dict:
    """
    Get place autocomplete suggestions from Google Places.

    Results are biased toward Angeles City, Pampanga.
    """
    service = GooglePlacesService()
    predictions = await service.autocomplete(query, session_token)
    return {"predictions": predictions}


@router.get("/geocode")
async def geocode(
    address: str | None = Query(None, description="Address for forward geocoding"),
    lat: float | None = Query(None, description="Latitude for reverse geocoding"),
    lon: float | None = Query(None, description="Longitude for reverse geocoding"),
) -> dict:
    """
    Forward or reverse geocoding via Google Geocoding API.

    Provide 'address' for forward geocoding, or 'lat'/'lon' for reverse.
    """
    service = GooglePlacesService()
    results = await service.geocode(address=address, lat=lat, lon=lon)
    return {"results": results}
