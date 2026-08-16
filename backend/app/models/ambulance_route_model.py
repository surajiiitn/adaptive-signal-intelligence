from typing import Any

from app.models.traffic_model import utc_now


def build_ambulance_route_document(route_data: dict[str, Any]) -> dict[str, Any]:
    document = route_data.copy()
    document["timestamp"] = utc_now()
    return document
