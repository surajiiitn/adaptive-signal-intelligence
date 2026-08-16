from typing import Any

from app.models.traffic_model import utc_now


def build_ml_traffic_frame_document(frame_data: dict[str, Any]) -> dict[str, Any]:
    document = frame_data.copy()
    document["ingested_at"] = utc_now()
    return document
