from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import (
    get_green_corridor_collection,
    get_junction_collection,
    get_roadside_display_collection,
)
from app.models.roadside_display_model import build_roadside_display_document
from app.schemas.green_corridor_schema import GreenCorridorStatus
from app.schemas.recommendation_schema import RecommendationPriority
from app.schemas.roadside_display_schema import DisplayMessageType, RoadsideDisplayCreate


def _to_object_id(resource_id: str, resource_name: str) -> ObjectId:
    if not ObjectId.is_valid(resource_id):
        raise ValueError(f"Invalid {resource_name} ID")
    return ObjectId(resource_id)


def create_roadside_display_message(payload: RoadsideDisplayCreate) -> dict[str, Any]:
    junction_object_id = _to_object_id(payload.junction_id, "junction")
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")

    corridor_object_id: ObjectId | None = None
    corridor_status: str | None = None
    if payload.corridor_id is not None:
        corridor_object_id = _to_object_id(payload.corridor_id, "corridor")
        corridor = get_green_corridor_collection().find_one({"_id": corridor_object_id})
        if corridor is None:
            raise LookupError("Green corridor not found")
        corridor_status = corridor["status"]

    message = _build_display_message(
        payload.message_type.value,
        payload.waiting_time_seconds,
        payload.countdown_seconds,
        corridor_status,
    )
    priority = _derive_priority(payload.message_type.value, corridor_status)

    document = build_roadside_display_document(
        {
            "ambulance_id": payload.ambulance_id,
            "junction_id": junction_object_id,
            "corridor_id": corridor_object_id,
            "message_type": payload.message_type.value,
            "message": message,
            "waiting_time_seconds": payload.waiting_time_seconds,
            "countdown_seconds": payload.countdown_seconds,
            "green_corridor_status": corridor_status,
            "priority": priority,
        },
    )
    result = get_roadside_display_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_display(document)


def get_latest_display_message(junction_id: str) -> dict[str, Any]:
    junction_object_id = _to_object_id(junction_id, "junction")
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")
    document = get_roadside_display_collection().find_one(
        {"junction_id": junction_object_id},
        sort=[("timestamp", DESCENDING)],
    )
    if document is None:
        raise LookupError("Roadside display message not found")
    return _serialize_display(document)


def get_display_message_history(junction_id: str) -> list[dict[str, Any]]:
    junction_object_id = _to_object_id(junction_id, "junction")
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")
    documents = get_roadside_display_collection().find({"junction_id": junction_object_id}).sort(
        "timestamp",
        DESCENDING,
    )
    history = [_serialize_display(document) for document in documents]
    if not history:
        raise LookupError("Roadside display message not found")
    return history


def _build_display_message(
    message_type: str,
    waiting_time_seconds: int | None,
    countdown_seconds: int | None,
    corridor_status: str | None,
) -> str:
    if message_type == DisplayMessageType.EMERGENCY_WARNING.value:
        return "EMERGENCY VEHICLE APPROACHING"
    if message_type == DisplayMessageType.AMBULANCE_APPROACHING.value:
        return "AMBULANCE APPROACHING - GIVE WAY"
    if message_type == DisplayMessageType.CLEAR_LANE.value:
        return "CLEAR LANE FOR AMBULANCE"
    if message_type == DisplayMessageType.KEEP_LEFT.value:
        return "KEEP LEFT - EMERGENCY VEHICLE APPROACHING"
    if message_type == DisplayMessageType.WAITING_TIME.value:
        if waiting_time_seconds is None:
            raise ValueError("waiting_time_seconds is required for WAITING_TIME")
        return f"AMBULANCE ARRIVING IN {waiting_time_seconds} SECONDS"
    if message_type == DisplayMessageType.COUNTDOWN.value:
        if countdown_seconds is None:
            raise ValueError("countdown_seconds is required for COUNTDOWN")
        return f"GREEN CORRIDOR - {countdown_seconds} SECONDS"
    if corridor_status == GreenCorridorStatus.ACTIVE.value:
        return "GREEN CORRIDOR ACTIVE - AMBULANCE APPROACHING"
    if corridor_status == GreenCorridorStatus.INACTIVE.value:
        return "GREEN CORRIDOR INACTIVE"
    if corridor_status == GreenCorridorStatus.COMPLETED.value:
        return "GREEN CORRIDOR COMPLETED"
    return "GREEN CORRIDOR STATUS UNKNOWN"


def _derive_priority(message_type: str, corridor_status: str | None) -> str:
    if corridor_status == GreenCorridorStatus.ACTIVE.value:
        return RecommendationPriority.CRITICAL.value
    if message_type in {
        DisplayMessageType.EMERGENCY_WARNING.value,
        DisplayMessageType.AMBULANCE_APPROACHING.value,
        DisplayMessageType.CLEAR_LANE.value,
        DisplayMessageType.KEEP_LEFT.value,
    }:
        return RecommendationPriority.HIGH.value
    if message_type in {
        DisplayMessageType.WAITING_TIME.value,
        DisplayMessageType.COUNTDOWN.value,
    }:
        return RecommendationPriority.MEDIUM.value
    return RecommendationPriority.LOW.value


def _serialize_display(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "ambulance_id": document["ambulance_id"],
        "junction_id": str(document["junction_id"]),
        "corridor_id": str(document["corridor_id"]) if document["corridor_id"] else None,
        "message_type": document["message_type"],
        "message": document["message"],
        "waiting_time_seconds": document["waiting_time_seconds"],
        "countdown_seconds": document["countdown_seconds"],
        "green_corridor_status": document["green_corridor_status"],
        "priority": document["priority"],
        "timestamp": document["timestamp"],
    }
