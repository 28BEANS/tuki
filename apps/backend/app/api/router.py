"""
Tuki Backend — API Router Aggregation

Registers all v1 API sub-routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    fare,
    health,
    landmarks,
    places,
    ride_hailing,
    routes,
    routing,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(landmarks.router, tags=["Landmarks"])
api_router.include_router(routes.router, tags=["Jeep Routes"])
api_router.include_router(fare.router, tags=["Fare"])
api_router.include_router(routing.router, tags=["Routing"])
api_router.include_router(ride_hailing.router, tags=["Ride Hailing"])
api_router.include_router(places.router, tags=["Places"])
api_router.include_router(auth.router, tags=["Auth"])
