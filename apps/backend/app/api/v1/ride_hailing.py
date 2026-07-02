"""
Tuki Backend — Ride-Hailing Comparison Endpoint
"""

from fastapi import APIRouter, Query

from app.schemas.ride_hailing import RideComparisonResponse
from app.services.ride_hailing_service import RideHailingService

router = APIRouter()


@router.get("/compare-ride-options", response_model=RideComparisonResponse)
async def compare_ride_options(
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lon: float = Query(..., description="Origin longitude"),
    destination_lat: float = Query(..., description="Destination latitude"),
    destination_lon: float = Query(..., description="Destination longitude"),
) -> RideComparisonResponse:
    """Compare ride-hailing options (Grab & Maxim) for a trip."""
    from app.schemas.ride_hailing import RideComparisonRequest

    service = RideHailingService()
    request = RideComparisonRequest(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
    )
    return await service.compare_options(request)
