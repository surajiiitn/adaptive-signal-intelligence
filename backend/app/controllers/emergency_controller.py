from typing import Any

from fastapi import HTTPException, status

from app.schemas.emergency_schema import EmergencyTriageCreate
from app.services import emergency_service


def create_emergency_triage(triage: EmergencyTriageCreate) -> dict[str, Any]:
    try:
        return emergency_service.create_emergency_triage(triage)
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


def get_current_triage(ambulance_id: str) -> dict[str, Any]:
    try:
        return emergency_service.get_current_triage(ambulance_id)
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


def get_triage_history(ambulance_id: str) -> list[dict[str, Any]]:
    try:
        return emergency_service.get_triage_history(ambulance_id)
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
