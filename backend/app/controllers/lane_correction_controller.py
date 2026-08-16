from typing import Any

from fastapi import HTTPException, status

from app.schemas.lane_correction_schema import LaneCorrectionAnalyzeRequest
from app.services import lane_correction_service


def analyze_lane_correction(payload: LaneCorrectionAnalyzeRequest) -> dict[str, Any]:
    try:
        return lane_correction_service.analyze_lane_correction(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


def get_latest_lane_correction(junction_id: str) -> dict[str, Any]:
    try:
        return lane_correction_service.get_latest_lane_correction(junction_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


def get_lane_correction_history(junction_id: str) -> list[dict[str, Any]]:
    try:
        return lane_correction_service.get_lane_correction_history(junction_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
