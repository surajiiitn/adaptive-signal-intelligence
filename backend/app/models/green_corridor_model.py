from typing import Any

from app.models.traffic_model import utc_now


def build_green_corridor_document(corridor_data: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    document = corridor_data.copy()
    document["created_at"] = now
    document["updated_at"] = now
    return document


def build_green_corridor_update_document(update_data: dict[str, Any]) -> dict[str, Any]:
    document = update_data.copy()
    document["updated_at"] = utc_now()
    return document
