from typing import Any

from fastapi import HTTPException, status

from app.schemas.ml_traffic_frame_schema import MlTrafficFrameCreate
from app.services import ml_ingestion_service


def ingest_traffic_frame(payload: MlTrafficFrameCreate) -> dict[str, Any]:
    try:
        return ml_ingestion_service.ingest_traffic_frame(payload)
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
