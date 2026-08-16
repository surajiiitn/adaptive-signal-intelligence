from fastapi import APIRouter, status

from app.controllers import ml_ingestion_controller
from app.schemas.ml_traffic_frame_schema import MlTrafficFrameCreate, MlTrafficFrameResponse


router = APIRouter(prefix="/ml", tags=["ML Ingestion"])


@router.post(
    "/traffic-frame",
    response_model=MlTrafficFrameResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_traffic_frame(payload: MlTrafficFrameCreate) -> dict:
    return ml_ingestion_controller.ingest_traffic_frame(payload)
