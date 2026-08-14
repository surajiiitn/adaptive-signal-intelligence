from typing import Any

from app.models.traffic_model import utc_now


def build_recommendation_document(recommendation_data: dict[str, Any]) -> dict[str, Any]:
    document = recommendation_data.copy()
    document["created_at"] = utc_now()
    return document
