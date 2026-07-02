"""
Tuki Backend — Model Registry

Imports all models so SQLAlchemy can discover them for migrations.
"""

from app.models.barangay import Barangay
from app.models.fare_matrix import FareMatrix
from app.models.jeep_route import JeepRoute
from app.models.jeep_route_stop import JeepRouteStop
from app.models.jeep_stop import JeepStop
from app.models.landmark import Landmark, LandmarkCategory
from app.models.transfer_point import TransferPoint, TransferType
from app.models.tricycle_terminal import TricycleTerminal
from app.models.user_profile import UserProfile
from app.models.walking_edge import WalkingEdge
from app.models.walking_node import WalkingNode

__all__ = [
    "Barangay",
    "FareMatrix",
    "JeepRoute",
    "JeepRouteStop",
    "JeepStop",
    "Landmark",
    "LandmarkCategory",
    "TransferPoint",
    "TransferType",
    "TricycleTerminal",
    "UserProfile",
    "WalkingEdge",
    "WalkingNode",
]
