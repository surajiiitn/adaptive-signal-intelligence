from typing import Any

from fastapi import HTTPException, status

from app.schemas.risk_pattern_schema import VehicleMovementCreate
from app.services import risk_pattern_service


def analyze_vehicle_movement(payload: VehicleMovementCreate) -> dict[str, Any]:
    try:
        return risk_pattern_service.analyze_vehicle_movement(payload)
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


def get_latest_risk_pattern(vehicle_id: str) -> dict[str, Any]:
    try:
        return risk_pattern_service.get_latest_risk_pattern(vehicle_id)
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


def get_risk_pattern_history(vehicle_id: str) -> list[dict[str, Any]]:
    try:
        return risk_pattern_service.get_risk_pattern_history(vehicle_id)
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
