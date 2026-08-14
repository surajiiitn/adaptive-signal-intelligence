from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class GreenCorridorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"


class CorridorJunctionInput(BaseModel):
    junction_id: str
    priority_direction: str

    @field_validator("junction_id")
    @classmethod
    def validate_junction_id(cls, value: str) -> str:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid junction ID")
        return value

    @field_validator("priority_direction")
    @classmethod
    def validate_priority_direction(cls, value: str) -> str:
        allowed_directions = {"NORTH", "SOUTH", "EAST", "WEST", "UNKNOWN"}
        normalized_value = value.strip().upper()
        if normalized_value not in allowed_directions:
            raise ValueError("Direction must be NORTH, SOUTH, EAST, WEST, or UNKNOWN")
        return normalized_value


class GreenCorridorActivateRequest(BaseModel):
    ambulance_id: str = Field(..., min_length=1)
    route: list[str] = Field(..., min_length=1)
    upcoming_junctions: list[CorridorJunctionInput] = Field(..., min_length=1)
    destination: str | None = None


class GreenCorridorJunctionAction(BaseModel):
    junction_id: str
    priority_direction: str
    signal_action: str
    conflicting_traffic_action: str
    pre_clear_action: str
    status: GreenCorridorStatus
    timestamp: datetime


class GreenCorridorResponse(BaseModel):
    id: str
    ambulance_id: str
    route: list[str]
    destination: str | None = None
    status: GreenCorridorStatus
    junction_actions: list[GreenCorridorJunctionAction]
    created_at: datetime
    updated_at: datetime
