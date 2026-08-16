from typing import Any

from fastapi import HTTPException, status

from app.schemas.roadside_display_schema import RoadsideDisplayCreate
from app.services import roadside_display_service


def create_roadside_display_message(payload: RoadsideDisplayCreate) -> dict[str, Any]:
    try:
        return roadside_display_service.create_roadside_display_message(payload)
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


def get_latest_display_message(junction_id: str) -> dict[str, Any]:
    try:
        return roadside_display_service.get_latest_display_message(junction_id)
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


def get_display_message_history(junction_id: str) -> list[dict[str, Any]]:
    try:
        return roadside_display_service.get_display_message_history(junction_id)
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
