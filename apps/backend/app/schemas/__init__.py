"""Tuki Backend — Pydantic Schemas package."""

from app.schemas.barangay import BarangayDetail, BarangayResponse
from app.schemas.common import ErrorResponse, GeoJSONPoint, PaginatedResponse
from app.schemas.fare import FareCalculationRequest, FareCalculationResponse, FareMatrixResponse
from app.schemas.jeep_route import JeepRouteDetail, JeepRouteResponse
from app.schemas.jeep_stop import JeepStopResponse
from app.schemas.landmark import LandmarkQuery, LandmarkResponse
from app.schemas.ride_hailing import RideComparisonRequest, RideComparisonResponse, RideOption
from app.schemas.routing import NavigationInstruction, RouteRequest, RouteResponse, RouteSegment
from app.schemas.transfer_point import TransferPointResponse
from app.schemas.user import UserProfileCreate, UserProfileResponse

__all__ = [
    "BarangayDetail",
    "BarangayResponse",
    "ErrorResponse",
    "FareCalculationRequest",
    "FareCalculationResponse",
    "FareMatrixResponse",
    "GeoJSONPoint",
    "JeepRouteDetail",
    "JeepRouteResponse",
    "JeepStopResponse",
    "LandmarkQuery",
    "LandmarkResponse",
    "NavigationInstruction",
    "PaginatedResponse",
    "RideComparisonRequest",
    "RideComparisonResponse",
    "RideOption",
    "RouteRequest",
    "RouteResponse",
    "RouteSegment",
    "TransferPointResponse",
    "UserProfileCreate",
    "UserProfileResponse",
]
