from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class MovementType(str, Enum):
    NORMAL = "NORMAL"
    ZIG_ZAG = "ZIG_ZAG"
    SUDDEN_LANE_DEVIATION = "SUDDEN_LANE_DEVIATION"
    SUDDEN_SPEED_CHANGE = "SUDDEN_SPEED_CHANGE"
    UNSAFE_CUT = "UNSAFE_CUT"
    MULTIPLE_RISK = "MULTIPLE_RISK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VehicleMovementCreate(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    junction_id: str
    lane_id: str = Field(..., min_length=1)
    speed: float = Field(..., ge=0)
    previous_speed: float = Field(..., ge=0)
    direction: str = Field(..., min_length=1)
    previous_direction: str = Field(..., min_length=1)
    lane_position: int = Field(..., ge=0)
    previous_lane_position: int = Field(..., ge=0)
    timestamp: datetime | None = None

    @field_validator("junction_id")
    @classmethod
    def validate_junction_id(cls, value: str) -> str:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid junction ID")
        return value


class RiskPatternResponse(BaseModel):
    id: str
    vehicle_id: str
    junction_id: str
    lane_id: str
    movement_type: MovementType
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    reason: str
    alert_created: bool
    timestamp: datetime
