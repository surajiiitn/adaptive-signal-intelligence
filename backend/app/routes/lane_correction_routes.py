from fastapi import APIRouter, status

from app.controllers import lane_correction_controller
from app.schemas.lane_correction_schema import (
    LaneCorrectionAnalyzeRequest,
    LaneCorrectionResponse,
)


router = APIRouter(prefix="/lane-correction", tags=["Lane Correction"])


@router.post(
    "/analyze",
    response_model=LaneCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_lane_correction(payload: LaneCorrectionAnalyzeRequest) -> dict:
    return lane_correction_controller.analyze_lane_correction(payload)


@router.get("/{junction_id}", response_model=LaneCorrectionResponse)
def get_latest_lane_correction(junction_id: str) -> dict:
    return lane_correction_controller.get_latest_lane_correction(junction_id)


@router.get("/{junction_id}/history", response_model=list[LaneCorrectionResponse])
def get_lane_correction_history(junction_id: str) -> list[dict]:
    return lane_correction_controller.get_lane_correction_history(junction_id)
