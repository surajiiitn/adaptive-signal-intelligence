from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MlBoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class MlCentroid(BaseModel):
    x: float
    y: float


class MlDetection(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    class_name: str = Field(..., alias="class", min_length=1)
    class_id: int
    confidence: float = Field(..., ge=0, le=1)
    bbox: MlBoundingBox
    centroid: MlCentroid
    speed_kmh: float = Field(..., ge=0)
    heading_degrees: float
    in_roi: str = Field(..., min_length=1)
    track_age_frames: int = Field(..., ge=0)

    model_config = {"populate_by_name": True}


class MlDirectionStats(BaseModel):
    vehicle_count: int = Field(..., ge=0)
    vehicle_breakdown: dict[str, int] = Field(default_factory=dict)
    density_ratio: float = Field(..., ge=0)
    density_level: str = Field(..., min_length=1)
    average_speed_kmh: float = Field(..., ge=0)
    queue_length_meters: float = Field(..., ge=0)
    flow_rate_veh_per_min: float = Field(..., ge=0)
    occupancy_percent: float = Field(..., ge=0, le=100)


class MlAnomaly(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    subtype: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0)
    bbox: MlBoundingBox
    centroid: MlCentroid
    heading_variance_deg: float | None = None
    lateral_deviation_px: float | None = None
    description: str = Field(..., min_length=1)


class MlAggregateStats(BaseModel):
    total_vehicles: int = Field(..., ge=0)
    total_by_class: dict[str, int] = Field(default_factory=dict)
    avg_speed_kmh: float = Field(..., ge=0)
    max_density_direction: str = Field(..., min_length=1)
    overall_congestion_score: float = Field(..., ge=0)
    overall_congestion_level: str = Field(..., min_length=1)
    active_tracks: int = Field(..., ge=0)
    new_tracks_this_frame: int = Field(..., ge=0)
    lost_tracks_this_frame: int = Field(..., ge=0)


class MlFrameResolution(BaseModel):
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class MlFrameMetadata(BaseModel):
    resolution: MlFrameResolution
    inference_time_ms: float = Field(..., ge=0)
    tracking_time_ms: float = Field(..., ge=0)
    total_processing_time_ms: float = Field(..., ge=0)
    model_name: str = Field(..., min_length=1)
    tracker: str = Field(..., min_length=1)


class MlTrafficFrameCreate(BaseModel):
    frame_id: int = Field(..., ge=0)
    timestamp: datetime
    source: str = Field(..., min_length=1)
    junction_id: str = Field(..., min_length=1)
    detections: list[MlDetection] = Field(default_factory=list)
    direction_analytics: dict[str, MlDirectionStats] = Field(..., min_length=1)
    anomalies: list[MlAnomaly] = Field(default_factory=list)
    aggregate_stats: MlAggregateStats
    frame_metadata: MlFrameMetadata


class MlDirectionIngestSummary(BaseModel):
    direction: str
    vehicle_count: int
    average_speed: float
    queue_length: float
    density_level: str


class MlTrafficFrameResponse(BaseModel):
    id: str
    frame_id: int
    junction_id: str
    mapped_junction_id: str | None = None
    ingested_traffic_observations: int = Field(..., ge=0)
    normalized_directions: list[MlDirectionIngestSummary]
    timestamp: datetime
    ingested_at: datetime
    source: str
    metadata: dict[str, Any]
