from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import (
    get_ambulance_route_collection,
    get_junction_collection,
    get_traffic_collection,
)
from app.models.ambulance_route_model import build_ambulance_route_document
from app.schemas.ambulance_route_schema import (
    AmbulanceRouteCreate,
    PredictionStatus,
    RouteTrafficCondition,
)
from app.schemas.density_schema import DensityLevel
from app.services import congestion_service, density_service


def _to_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def create_ambulance_route_analysis(payload: AmbulanceRouteCreate) -> dict[str, Any]:
    traffic_conditions: list[dict[str, Any]] = []
    congestion_labels: list[str] = []
    density_labels: list[str] = []
    condition_labels: list[str] = []

    for junction_id in payload.upcoming_junctions:
        junction_object_id = _to_object_id(junction_id)
        junction = get_junction_collection().find_one({"_id": junction_object_id})
        if junction is None:
            raise LookupError("Junction not found")

        latest_traffic = get_traffic_collection().find_one(
            {"junction_id": junction_object_id},
            sort=[("timestamp", DESCENDING)],
        )

        if latest_traffic is None:
            traffic_conditions.append(
                {
                    "junction_id": junction_id,
                    "traffic_condition": RouteTrafficCondition.UNKNOWN.value,
                    "density": 0.0,
                    "density_level": DensityLevel.LOW.value,
                    "congestion_level": None,
                    "average_speed": 0.0,
                    "queue_length": 0.0,
                },
            )
            condition_labels.append(RouteTrafficCondition.UNKNOWN.value)
            continue

        density = density_service.calculate_density(
            latest_traffic["vehicle_count"],
            junction["lanes"],
        )
        density_level = density_service.classify_density(density)
        congestion_level = congestion_service.classify_congestion(
            density,
            latest_traffic["average_speed"],
            latest_traffic["queue_length"],
        )
        traffic_condition = _resolve_route_traffic_condition(
            density_level.value,
            congestion_level.value,
        )

        traffic_conditions.append(
            {
                "junction_id": junction_id,
                "traffic_condition": traffic_condition,
                "density": density,
                "density_level": density_level.value,
                "congestion_level": congestion_level.value,
                "average_speed": latest_traffic["average_speed"],
                "queue_length": latest_traffic["queue_length"],
            },
        )
        congestion_labels.append(congestion_level.value)
        density_labels.append(density_level.value)
        condition_labels.append(traffic_condition)

    prediction = _predict_congestion(congestion_labels, density_labels)
    delay_minutes = _estimate_delay_minutes(condition_labels)
    total_route_distance = float(len(payload.route))
    effective_speed = _calculate_effective_speed(payload.average_speed, condition_labels)
    eta_minutes = round((total_route_distance / effective_speed) * 60, 2)

    document = build_ambulance_route_document(
        {
            "ambulance_id": payload.ambulance_id,
            "current_location": payload.current_location,
            "route": payload.route,
            "destination": payload.destination,
            "average_speed": payload.average_speed,
            "eta_minutes": eta_minutes,
            "upcoming_junctions": payload.upcoming_junctions,
            "traffic_conditions": traffic_conditions,
            "congestion_prediction": prediction,
            "estimated_delay_minutes": delay_minutes,
            "total_route_distance": total_route_distance,
        },
    )
    result = get_ambulance_route_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_route(document)


def get_latest_ambulance_route(ambulance_id: str) -> dict[str, Any]:
    document = get_ambulance_route_collection().find_one(
        {"ambulance_id": ambulance_id},
        sort=[("timestamp", DESCENDING)],
    )
    if document is None:
        raise LookupError("Ambulance route not found")
    return _serialize_route(document)


def get_ambulance_route_history(ambulance_id: str) -> list[dict[str, Any]]:
    documents = get_ambulance_route_collection().find({"ambulance_id": ambulance_id}).sort(
        "timestamp",
        DESCENDING,
    )
    history = [_serialize_route(document) for document in documents]
    if not history:
        raise LookupError("Ambulance route not found")
    return history


def _resolve_route_traffic_condition(density_level: str, congestion_level: str) -> str:
    if congestion_level == "CRITICAL":
        return RouteTrafficCondition.CRITICAL.value
    if congestion_level == "CONGESTED":
        return RouteTrafficCondition.HIGH.value
    if density_level == "HIGH":
        return RouteTrafficCondition.HIGH.value
    if density_level == "MEDIUM":
        return RouteTrafficCondition.MEDIUM.value
    return RouteTrafficCondition.LOW.value


def _predict_congestion(congestion_levels: list[str], density_levels: list[str]) -> str:
    if "CRITICAL" in congestion_levels:
        return PredictionStatus.CRITICAL.value
    if "CONGESTED" in congestion_levels:
        return PredictionStatus.CONGESTION_LIKELY.value
    if "HIGH" in density_levels:
        return PredictionStatus.WARNING.value
    return PredictionStatus.CLEAR.value


def _calculate_effective_speed(ambulance_speed: float, conditions: list[str]) -> float:
    if RouteTrafficCondition.CRITICAL.value in conditions:
        factor = 0.4
    elif RouteTrafficCondition.HIGH.value in conditions:
        factor = 0.6
    elif RouteTrafficCondition.MEDIUM.value in conditions:
        factor = 0.8
    elif RouteTrafficCondition.UNKNOWN.value in conditions:
        factor = 0.8
    else:
        factor = 1.0
    return max(ambulance_speed * factor, 1.0)


def _estimate_delay_minutes(conditions: list[str]) -> float:
    delay_map = {
        RouteTrafficCondition.LOW.value: 0.0,
        RouteTrafficCondition.MEDIUM.value: 2.0,
        RouteTrafficCondition.HIGH.value: 5.0,
        RouteTrafficCondition.CRITICAL.value: 10.0,
        RouteTrafficCondition.UNKNOWN.value: 3.0,
    }
    return round(sum(delay_map[condition] for condition in conditions), 2)


def _serialize_route(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "ambulance_id": document["ambulance_id"],
        "current_location": document["current_location"],
        "route": document["route"],
        "destination": document["destination"],
        "average_speed": document["average_speed"],
        "eta_minutes": document["eta_minutes"],
        "upcoming_junctions": document["upcoming_junctions"],
        "traffic_conditions": document["traffic_conditions"],
        "congestion_prediction": document["congestion_prediction"],
        "estimated_delay_minutes": document["estimated_delay_minutes"],
        "total_route_distance": document["total_route_distance"],
        "timestamp": document["timestamp"],
    }
