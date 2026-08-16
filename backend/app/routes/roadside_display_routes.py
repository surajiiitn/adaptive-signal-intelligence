from fastapi import APIRouter, status

from app.controllers import roadside_display_controller
from app.schemas.roadside_display_schema import RoadsideDisplayCreate, RoadsideDisplayResponse


router = APIRouter(prefix="/roadside-display", tags=["Roadside Display"])


@router.post(
    "",
    response_model=RoadsideDisplayResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_roadside_display_message(payload: RoadsideDisplayCreate) -> dict:
    return roadside_display_controller.create_roadside_display_message(payload)


@router.get("/{junction_id}", response_model=RoadsideDisplayResponse)
def get_latest_display_message(junction_id: str) -> dict:
    return roadside_display_controller.get_latest_display_message(junction_id)


@router.get("/{junction_id}/history", response_model=list[RoadsideDisplayResponse])
def get_display_message_history(junction_id: str) -> list[dict]:
    return roadside_display_controller.get_display_message_history(junction_id)
