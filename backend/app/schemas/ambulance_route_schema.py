from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from app.schemas.congestion_schema import CongestionLevel
from app.schemas.density_schema import DensityLevel


class RouteTrafficCondition(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PredictionStatus(str, Enum):
    CLEAR = "CLEAR"
    WARNING = "WARNING"
    CONGESTION_LIKELY = "CONGESTION_LIKELY"
    CRITICAL = "CRITICAL"


class AmbulanceRouteCreate(BaseModel):
    ambulance_id: str = Field(..., min_length=1)
    current_location: str = Field(..., min_length=1)
    route: list[str] = Field(..., min_length=1)
    upcoming_junctions: list[str] = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    average_speed: float = Field(..., gt=0)

    @field_validator("upcoming_junctions")
    @classmethod
    def validate_upcoming_junctions(cls, value: list[str]) -> list[str]:
        for junction_id in value:
            if not ObjectId.is_valid(junction_id):
                raise ValueError("Invalid junction ID")
        return value


class RouteJunctionTrafficCondition(BaseModel):
    junction_id: str
    traffic_condition: RouteTrafficCondition
    density: float = Field(..., ge=0)
    density_level: DensityLevel
    congestion_level: CongestionLevel | None = None
    average_speed: float = Field(..., ge=0)
    queue_length: float = Field(..., ge=0)


class AmbulanceRouteResponse(BaseModel):
    id: str
    ambulance_id: str
    current_location: str
    route: list[str]
    destination: str
    average_speed: float
    eta_minutes: float = Field(..., ge=0)
    upcoming_junctions: list[str]
    traffic_conditions: list[RouteJunctionTrafficCondition]
    congestion_prediction: PredictionStatus
    estimated_delay_minutes: float = Field(..., ge=0)
    total_route_distance: float = Field(..., ge=0)
    timestamp: datetime
