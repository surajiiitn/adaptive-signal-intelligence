from fastapi import APIRouter, status

from app.controllers import emergency_controller
from app.schemas.emergency_schema import EmergencyTriageCreate, EmergencyTriageResponse


router = APIRouter(prefix="/emergency/triage", tags=["Emergency Triage"])


@router.post(
    "",
    response_model=EmergencyTriageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_emergency_triage(triage: EmergencyTriageCreate) -> dict:
    return emergency_controller.create_emergency_triage(triage)


@router.get("/{ambulance_id}", response_model=EmergencyTriageResponse)
def get_current_triage(ambulance_id: str) -> dict:
    return emergency_controller.get_current_triage(ambulance_id)


@router.get("/history/{ambulance_id}", response_model=list[EmergencyTriageResponse])
def get_triage_history(ambulance_id: str) -> list[dict]:
    return emergency_controller.get_triage_history(ambulance_id)
