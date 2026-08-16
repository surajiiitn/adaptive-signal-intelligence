from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from app.schemas.recommendation_schema import RecommendationPriority


class LaneIssueType(str, Enum):
    WRONG_LANE_MOVEMENT = "WRONG_LANE_MOVEMENT"
    LANE_BLOCKAGE = "LANE_BLOCKAGE"
    EMERGENCY_LANE_BLOCKAGE = "EMERGENCY_LANE_BLOCKAGE"


class LaneSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LaneCorrectionStatus(str, Enum):
    NORMAL = "NORMAL"
    RISK_DETECTED = "RISK_DETECTED"


class LaneObservationInput(BaseModel):
    lane_id: str = Field(..., min_length=1)
    expected_direction: str = Field(..., min_length=1)
    observed_direction: str = Field(..., min_length=1)
    is_blocked: bool = False
    blocked_vehicle_count: int = Field(default=0, ge=0)
    is_emergency_lane: bool = False

    @field_validator("expected_direction", "observed_direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        allowed_directions = {"NORTH", "SOUTH", "EAST", "WEST", "UNKNOWN"}
        normalized = value.strip().upper()
        if normalized not in allowed_directions:
            raise ValueError("Direction must be NORTH, SOUTH, EAST, WEST, or UNKNOWN")
        return normalized


class LaneCorrectionAnalyzeRequest(BaseModel):
    junction_id: str
    ambulance_id: str | None = None
    observations: list[LaneObservationInput] = Field(..., min_length=1)
    timestamp: datetime | None = None

    @field_validator("junction_id")
    @classmethod
    def validate_junction_id(cls, value: str) -> str:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid junction ID")
        return value


class LaneCorrectionIssue(BaseModel):
    lane_id: str
    issue_type: LaneIssueType
    severity: LaneSeverity
    priority: RecommendationPriority
    suggestion: str
    reason: str


class LaneCorrectionResponse(BaseModel):
    id: str
    junction_id: str
    ambulance_id: str | None = None
    status: LaneCorrectionStatus
    issues: list[LaneCorrectionIssue]
    timestamp: datetime
