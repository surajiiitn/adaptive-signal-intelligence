from typing import Any

from app.models.traffic_model import utc_now


def build_risk_pattern_document(pattern_data: dict[str, Any]) -> dict[str, Any]:
    document = pattern_data.copy()
    document["timestamp"] = document.get("timestamp") or utc_now()
    return document
