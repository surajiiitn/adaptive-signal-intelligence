from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import (
    get_junction_collection,
    get_recommendation_collection,
    get_traffic_collection,
)
from app.models.recommendation_model import build_recommendation_document
from app.schemas.recommendation_schema import (
    RecommendationAction,
    RecommendationPriority,
)
from app.services import congestion_service, density_service


def _to_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def _ensure_junction_exists(junction_object_id: ObjectId) -> dict[str, Any]:
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")
    return junction


def generate_recommendations(junction_id: str) -> list[dict[str, Any]]:
    junction_object_id = _to_object_id(junction_id)
    junction = _ensure_junction_exists(junction_object_id)
    lane_count = junction["lanes"]

    latest_by_direction = _get_latest_observations_by_direction(junction_object_id)
    if not latest_by_direction:
        raise LookupError("Traffic observation not found")

    collection = get_recommendation_collection()
    recommendations: list[dict[str, Any]] = []
    for direction, observation in latest_by_direction.items():
        density = density_service.calculate_density(observation["vehicle_count"], lane_count)
        density_level = density_service.classify_density(density)
        congestion_level = congestion_service.classify_congestion(
            density,
            observation["average_speed"],
            observation["queue_length"],
        )

        rule = _derive_recommendation_rule(
            density_level=density_level.value,
            congestion_level=congestion_level.value,
            average_speed=observation["average_speed"],
            queue_length=observation["queue_length"],
        )

        document = build_recommendation_document(
            {
                "junction_id": junction_object_id,
                "direction": direction,
                "action": rule["action"],
                "green_time_change": rule["green_time_change"],
                "priority": rule["priority"],
                "reason": rule["reason"],
                "vehicle_count": observation["vehicle_count"],
                "density": density,
                "density_level": density_level.value,
                "average_speed": observation["average_speed"],
                "queue_length": observation["queue_length"],
                "congestion_level": congestion_level.value,
            },
        )
        result = collection.insert_one(document)
        document["_id"] = result.inserted_id
        recommendations.append(_serialize_recommendation(document))

    recommendations.sort(key=lambda item: item["direction"])
    return recommendations


def get_recommendation_history(junction_id: str) -> list[dict[str, Any]]:
    junction_object_id = _to_object_id(junction_id)
    _ensure_junction_exists(junction_object_id)

    documents = get_recommendation_collection().find({"junction_id": junction_object_id}).sort(
        "created_at",
        DESCENDING,
    )
    return [_serialize_recommendation(document) for document in documents]


def _get_latest_observations_by_direction(
    junction_object_id: ObjectId,
) -> dict[str, dict[str, Any]]:
    documents = get_traffic_collection().find({"junction_id": junction_object_id}).sort(
        "timestamp",
        DESCENDING,
    )

    latest_by_direction: dict[str, dict[str, Any]] = {}
    for document in documents:
        direction = document.get("direction", "UNKNOWN")
        if direction not in latest_by_direction:
            latest_by_direction[direction] = document
    return latest_by_direction


def _derive_recommendation_rule(
    density_level: str,
    congestion_level: str,
    average_speed: float,
    queue_length: float,
) -> dict[str, Any]:
    if congestion_level == "CRITICAL":
        return {
            "action": RecommendationAction.REDUCE_CONFLICTING_TRAFFIC.value,
            "green_time_change": 30,
            "priority": RecommendationPriority.CRITICAL.value,
            "reason": "Critical congestion detected: very high load and severe delay",
        }

    if congestion_level == "CONGESTED":
        return {
            "action": RecommendationAction.PRIORITIZE_DIRECTION.value,
            "green_time_change": 20,
            "priority": RecommendationPriority.HIGH.value,
            "reason": "Congested flow detected: prioritize this direction to reduce buildup",
        }

    if density_level == "HIGH":
        return {
            "action": RecommendationAction.INCREASE_GREEN_TIME.value,
            "green_time_change": 15,
            "priority": RecommendationPriority.HIGH.value,
            "reason": "High density detected with manageable congestion: increase green time",
        }

    if density_level == "MEDIUM":
        if average_speed < 25 or queue_length >= 80:
            return {
                "action": RecommendationAction.PRIORITIZE_DIRECTION.value,
                "green_time_change": 10,
                "priority": RecommendationPriority.MEDIUM.value,
                "reason": "Moderate density with slowing movement: prioritize this direction",
            }
        return {
            "action": RecommendationAction.KEEP_CURRENT.value,
            "green_time_change": 0,
            "priority": RecommendationPriority.MEDIUM.value,
            "reason": "Balanced medium traffic: keep current signal timing",
        }

    if average_speed >= 40 and queue_length <= 30:
        return {
            "action": RecommendationAction.DECREASE_GREEN_TIME.value,
            "green_time_change": -10,
            "priority": RecommendationPriority.LOW.value,
            "reason": "Low traffic with free flow: reduce green time allocation",
        }

    return {
        "action": RecommendationAction.KEEP_CURRENT.value,
        "green_time_change": 0,
        "priority": RecommendationPriority.LOW.value,
        "reason": "Low traffic with minor queue: keep current cycle",
    }


def _serialize_recommendation(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "junction_id": str(document["junction_id"]),
        "direction": document["direction"],
        "action": document["action"],
        "green_time_change": document["green_time_change"],
        "priority": document["priority"],
        "reason": document["reason"],
        "vehicle_count": document["vehicle_count"],
        "density": document["density"],
        "density_level": document["density_level"],
        "average_speed": document["average_speed"],
        "queue_length": document["queue_length"],
        "congestion_level": document["congestion_level"],
        "created_at": document["created_at"],
    }
