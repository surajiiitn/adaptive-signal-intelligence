from fastapi import APIRouter, status

from app.controllers import green_corridor_controller
from app.schemas.green_corridor_schema import (
    GreenCorridorActivateRequest,
    GreenCorridorResponse,
)


router = APIRouter(prefix="/green-corridor", tags=["Green Corridor"])


@router.post(
    "/activate",
    response_model=GreenCorridorResponse,
    status_code=status.HTTP_201_CREATED,
)
def activate_green_corridor(payload: GreenCorridorActivateRequest) -> dict:
    return green_corridor_controller.activate_green_corridor(payload)


@router.post(
    "/deactivate/{corridor_id}",
    response_model=GreenCorridorResponse,
)
def deactivate_green_corridor(corridor_id: str) -> dict:
    return green_corridor_controller.deactivate_green_corridor(corridor_id)


@router.post(
    "/{corridor_id}/restore",
    response_model=GreenCorridorResponse,
)
def restore_green_corridor(corridor_id: str) -> dict:
    return green_corridor_controller.restore_green_corridor(corridor_id)


@router.get(
    "/{corridor_id}",
    response_model=GreenCorridorResponse,
)
def get_green_corridor(corridor_id: str) -> dict:
    return green_corridor_controller.get_green_corridor(corridor_id)
