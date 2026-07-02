"""
Tuki Backend — Schema Validation Tests
"""

import pytest

from app.schemas.routing import RouteRequest, RouteResponse, RouteSegment, NavigationInstruction
from app.schemas.fare import FareCalculationRequest, FareCalculationResponse
from app.schemas.ride_hailing import RideComparisonResponse, RideOption


class TestRouteSchemas:
    """Tests for routing schemas."""

    def test_route_request_valid(self):
        """Valid route request passes validation."""
        req = RouteRequest(
            origin_lat=15.1450,
            origin_lon=120.5887,
            destination_lat=15.1380,
            destination_lon=120.5910,
        )
        assert req.prefer == "fastest"
        assert req.is_student is False

    def test_route_segment_jeep(self):
        """Jeep segment has route info."""
        seg = RouteSegment(
            mode="jeep",
            route="Yellow",
            route_color="Yellow",
            board_at="HAU",
            alight_at="Jenra Mall",
            distance_m=3200,
            duration_min=12,
            fare=13,
        )
        assert seg.mode == "jeep"
        assert seg.fare == 13

    def test_route_segment_walk(self):
        """Walk segment has no fare."""
        seg = RouteSegment(mode="walk", distance_m=180)
        assert seg.fare is None

    def test_route_response_complete(self):
        """Complete route response validates."""
        resp = RouteResponse(
            total_fare=38,
            total_distance_m=4430,
            travel_time_min=22,
            segments=[
                RouteSegment(mode="jeep", fare=13),
                RouteSegment(mode="walk", distance_m=180),
            ],
            instructions=[
                NavigationInstruction(step=1, instruction="Board the jeep.", mode="jeep"),
            ],
            transfers=1,
        )
        assert resp.total_fare == 38
        assert len(resp.segments) == 2


class TestFareSchemas:
    """Tests for fare schemas."""

    def test_fare_request_student(self):
        """Student fare request."""
        req = FareCalculationRequest(
            origin_lat=15.145,
            origin_lon=120.588,
            destination_lat=15.138,
            destination_lon=120.591,
            is_student=True,
        )
        assert req.is_student is True
        assert req.is_discounted is False

    def test_fare_response(self):
        """Fare response with breakdown."""
        resp = FareCalculationResponse(
            total_fare=13.0,
            distance_km=3.5,
            fare_type="regular",
            breakdown=[{"mode": "jeep", "fare": 13.0}],
        )
        assert resp.total_fare == 13.0


class TestRideHailingSchemas:
    """Tests for ride-hailing schemas."""

    def test_ride_option(self):
        """Ride option schema validates."""
        opt = RideOption(
            provider="grab",
            service_type="car",
            estimated_fare_min=85.0,
            estimated_fare_max=120.0,
            estimated_duration_min=15.0,
        )
        assert opt.surge_multiplier == 1.0

    def test_comparison_response(self):
        """Comparison response with options."""
        resp = RideComparisonResponse(
            distance_km=5.2,
            options=[
                RideOption(
                    provider="grab",
                    service_type="car",
                    estimated_fare_min=85.0,
                    estimated_fare_max=120.0,
                    estimated_duration_min=15.0,
                ),
            ],
        )
        assert len(resp.options) == 1
