"""
Tuki Backend — Fare Endpoints
"""

from fastapi import APIRouter, Query

from app.dependencies.database import DBSession
from app.repositories.fare_matrix_repo import FareMatrixRepository
from app.schemas.fare import (
    FareCalculationRequest,
    FareCalculationResponse,
    FareMatrixResponse,
)
from app.services.fare_service import FareService

router = APIRouter(prefix="/fare")


@router.get("/fare-matrix", response_model=list[FareMatrixResponse])
async def get_fare_matrix(
    session: DBSession,
    transport_type: str = Query("traditional_puj", description="Transport type"),
) -> list[FareMatrixResponse]:
    """Get the fare matrix for a transport type."""
    repo = FareMatrixRepository(session)
    items = await repo.get_all_by_type(transport_type)
    return [FareMatrixResponse.model_validate(item) for item in items]


@router.post("/calculate-fare", response_model=FareCalculationResponse)
async def calculate_fare(
    request: FareCalculationRequest,
    session: DBSession,
) -> FareCalculationResponse:
    """Calculate fare based on origin and destination."""
    service = FareService(session)
    return await service.calculate_fare(request)
