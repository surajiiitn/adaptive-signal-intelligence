from typing import Any

from fastapi import HTTPException, status

from app.schemas.ambulance_route_schema import AmbulanceRouteCreate
from app.services import ambulance_route_service


def create_ambulance_route_analysis(payload: AmbulanceRouteCreate) -> dict[str, Any]:
    try:
        return ambulance_route_service.create_ambulance_route_analysis(payload)
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


def get_latest_ambulance_route(ambulance_id: str) -> dict[str, Any]:
    try:
        return ambulance_route_service.get_latest_ambulance_route(ambulance_id)
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


def get_ambulance_route_history(ambulance_id: str) -> list[dict[str, Any]]:
    try:
        return ambulance_route_service.get_ambulance_route_history(ambulance_id)
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
