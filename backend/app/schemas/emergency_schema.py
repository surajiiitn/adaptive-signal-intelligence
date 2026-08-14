from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

from app.schemas.congestion_schema import CongestionLevel


class PatientSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    SERIOUS = "SERIOUS"
    STABLE = "STABLE"


class EmergencyPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class EmergencyStatus(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class EmergencyTriageCreate(BaseModel):
    ambulance_id: str = Field(..., min_length=1)
    patient_severity: PatientSeverity
    junction_id: str | None = None
    current_location: str | None = None
    destination: str | None = None

    @field_validator("junction_id")
    @classmethod
    def validate_junction_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid junction ID")
        return value


class EmergencyTriageResponse(BaseModel):
    id: str
    ambulance_id: str
    patient_severity: PatientSeverity
    priority: EmergencyPriority
    emergency_status: EmergencyStatus
    reason: str
    junction_id: str | None = None
    current_location: str | None = None
    destination: str | None = None
    congestion_level: CongestionLevel | None = None
    timestamp: datetime
