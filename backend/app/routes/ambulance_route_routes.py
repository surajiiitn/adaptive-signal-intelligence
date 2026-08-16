from fastapi import APIRouter, status

from app.controllers import ambulance_route_controller
from app.schemas.ambulance_route_schema import (
    AmbulanceRouteCreate,
    AmbulanceRouteResponse,
)


router = APIRouter(prefix="/ambulance/routes", tags=["Ambulance Routes"])


@router.post(
    "",
    response_model=AmbulanceRouteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ambulance_route_analysis(payload: AmbulanceRouteCreate) -> dict:
    return ambulance_route_controller.create_ambulance_route_analysis(payload)


@router.get("/{ambulance_id}", response_model=AmbulanceRouteResponse)
def get_latest_ambulance_route(ambulance_id: str) -> dict:
    return ambulance_route_controller.get_latest_ambulance_route(ambulance_id)


@router.get("/{ambulance_id}/history", response_model=list[AmbulanceRouteResponse])
def get_ambulance_route_history(ambulance_id: str) -> list[dict]:
    return ambulance_route_controller.get_ambulance_route_history(ambulance_id)
