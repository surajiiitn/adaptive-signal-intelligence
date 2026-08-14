from typing import Any

from app.models.traffic_model import utc_now


def build_emergency_triage_document(triage_data: dict[str, Any]) -> dict[str, Any]:
    document = triage_data.copy()
    document["timestamp"] = utc_now()
    return document
