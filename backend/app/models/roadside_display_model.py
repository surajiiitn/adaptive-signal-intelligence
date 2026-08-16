from typing import Any

from app.models.traffic_model import utc_now


def build_roadside_display_document(display_data: dict[str, Any]) -> dict[str, Any]:
    document = display_data.copy()
    document["timestamp"] = utc_now()
    return document
