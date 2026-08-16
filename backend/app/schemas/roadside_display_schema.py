from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from app.schemas.green_corridor_schema import GreenCorridorStatus
from app.schemas.recommendation_schema import RecommendationPriority


class DisplayMessageType(str, Enum):
    EMERGENCY_WARNING = "EMERGENCY_WARNING"
    AMBULANCE_APPROACHING = "AMBULANCE_APPROACHING"
    CLEAR_LANE = "CLEAR_LANE"
    KEEP_LEFT = "KEEP_LEFT"
    WAITING_TIME = "WAITING_TIME"
    COUNTDOWN = "COUNTDOWN"
    GREEN_CORRIDOR_STATUS = "GREEN_CORRIDOR_STATUS"


class RoadsideDisplayCreate(BaseModel):
    ambulance_id: str = Field(..., min_length=1)
    junction_id: str
    corridor_id: str | None = None
    message_type: DisplayMessageType
    waiting_time_seconds: int | None = Field(default=None, ge=0)
    countdown_seconds: int | None = Field(default=None, ge=0)

    @field_validator("junction_id")
    @classmethod
    def validate_junction_id(cls, value: str) -> str:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid junction ID")
        return value

    @field_validator("corridor_id")
    @classmethod
    def validate_corridor_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid corridor ID")
        return value


class RoadsideDisplayResponse(BaseModel):
    id: str
    ambulance_id: str
    junction_id: str
    corridor_id: str | None
    message_type: DisplayMessageType
    message: str
    waiting_time_seconds: int | None = None
    countdown_seconds: int | None = None
    green_corridor_status: GreenCorridorStatus | None = None
    priority: RecommendationPriority
    timestamp: datetime
