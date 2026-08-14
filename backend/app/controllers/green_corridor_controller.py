from typing import Any

from fastapi import HTTPException, status

from app.schemas.green_corridor_schema import GreenCorridorActivateRequest
from app.services import green_corridor_service


def activate_green_corridor(payload: GreenCorridorActivateRequest) -> dict[str, Any]:
    try:
        return green_corridor_service.activate_green_corridor(payload)
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


def deactivate_green_corridor(corridor_id: str) -> dict[str, Any]:
    try:
        return green_corridor_service.deactivate_green_corridor(corridor_id)
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


def restore_green_corridor(corridor_id: str) -> dict[str, Any]:
    try:
        return green_corridor_service.restore_green_corridor(corridor_id)
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


def get_green_corridor(corridor_id: str) -> dict[str, Any]:
    try:
        return green_corridor_service.get_green_corridor(corridor_id)
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
