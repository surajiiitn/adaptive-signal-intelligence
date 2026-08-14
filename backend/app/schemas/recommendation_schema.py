from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.congestion_schema import CongestionLevel
from app.schemas.density_schema import DensityLevel


class RecommendationAction(str, Enum):
    INCREASE_GREEN_TIME = "INCREASE_GREEN_TIME"
    DECREASE_GREEN_TIME = "DECREASE_GREEN_TIME"
    KEEP_CURRENT = "KEEP_CURRENT"
    PRIORITIZE_DIRECTION = "PRIORITIZE_DIRECTION"
    REDUCE_CONFLICTING_TRAFFIC = "REDUCE_CONFLICTING_TRAFFIC"


class RecommendationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TrafficRecommendationResponse(BaseModel):
    id: str
    junction_id: str
    direction: str
    action: RecommendationAction
    green_time_change: int
    priority: RecommendationPriority
    reason: str
    vehicle_count: int = Field(..., ge=0)
    density: float = Field(..., ge=0)
    density_level: DensityLevel
    average_speed: float = Field(..., ge=0)
    queue_length: float = Field(..., ge=0)
    congestion_level: CongestionLevel
    created_at: datetime
