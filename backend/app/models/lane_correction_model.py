from typing import Any

from app.models.traffic_model import utc_now


def build_lane_correction_document(correction_data: dict[str, Any]) -> dict[str, Any]:
    document = correction_data.copy()
    document["timestamp"] = document.get("timestamp") or utc_now()
    return document
