from fastapi import APIRouter, status

from app.controllers import risk_pattern_controller
from app.schemas.risk_pattern_schema import RiskPatternResponse, VehicleMovementCreate


router = APIRouter(prefix="/risk-patterns", tags=["Risk Pattern Detection"])


@router.post(
    "",
    response_model=RiskPatternResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_vehicle_movement(payload: VehicleMovementCreate) -> dict:
    return risk_pattern_controller.analyze_vehicle_movement(payload)


@router.get("/{vehicle_id}", response_model=RiskPatternResponse)
def get_latest_risk_pattern(vehicle_id: str) -> dict:
    return risk_pattern_controller.get_latest_risk_pattern(vehicle_id)


@router.get("/{vehicle_id}/history", response_model=list[RiskPatternResponse])
def get_risk_pattern_history(vehicle_id: str) -> list[dict]:
    return risk_pattern_controller.get_risk_pattern_history(vehicle_id)
