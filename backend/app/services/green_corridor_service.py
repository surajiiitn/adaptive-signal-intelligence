from typing import Any

from bson import ObjectId

from app.database.connection import get_green_corridor_collection, get_junction_collection
from app.models.green_corridor_model import (
    build_green_corridor_document,
    build_green_corridor_update_document,
)
from app.models.traffic_model import utc_now
from app.schemas.green_corridor_schema import GreenCorridorActivateRequest, GreenCorridorStatus


def _to_object_id(corridor_id: str) -> ObjectId:
    if not ObjectId.is_valid(corridor_id):
        raise ValueError("Invalid corridor ID")
    return ObjectId(corridor_id)


def _to_junction_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def activate_green_corridor(payload: GreenCorridorActivateRequest) -> dict[str, Any]:
    junction_actions: list[dict[str, Any]] = []
    for junction in payload.upcoming_junctions:
        junction_object_id = _to_junction_object_id(junction.junction_id)
        junction_exists = get_junction_collection().find_one({"_id": junction_object_id})
        if junction_exists is None:
            raise LookupError("Junction not found")

        junction_actions.append(
            {
                "junction_id": junction_object_id,
                "priority_direction": junction.priority_direction,
                "signal_action": "PRIORITIZE_DIRECTION",
                "conflicting_traffic_action": "HOLD_CONFLICTING_TRAFFIC",
                "pre_clear_action": "PRE_CLEAR_JUNCTION",
                "status": GreenCorridorStatus.ACTIVE.value,
                "timestamp": utc_now(),
            },
        )

    document = build_green_corridor_document(
        {
            "ambulance_id": payload.ambulance_id,
            "route": payload.route,
            "destination": payload.destination,
            "status": GreenCorridorStatus.ACTIVE.value,
            "junction_actions": junction_actions,
        },
    )

    result = get_green_corridor_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_corridor(document)


def deactivate_green_corridor(corridor_id: str) -> dict[str, Any]:
    corridor_object_id = _to_object_id(corridor_id)
    collection = get_green_corridor_collection()
    corridor = collection.find_one({"_id": corridor_object_id})
    if corridor is None:
        raise LookupError("Green corridor not found")

    updated_actions = [
        {
            **junction_action,
            "signal_action": "RESTORE_NORMAL_SIGNAL",
            "conflicting_traffic_action": "RELEASE_CONFLICTING_TRAFFIC",
            "pre_clear_action": "JUNCTION_RELEASED",
            "status": GreenCorridorStatus.INACTIVE.value,
            "timestamp": utc_now(),
        }
        for junction_action in corridor["junction_actions"]
    ]

    update_document = build_green_corridor_update_document(
        {
            "status": GreenCorridorStatus.INACTIVE.value,
            "junction_actions": updated_actions,
        },
    )
    collection.update_one({"_id": corridor_object_id}, {"$set": update_document})
    updated_corridor = collection.find_one({"_id": corridor_object_id})
    if updated_corridor is None:
        raise LookupError("Green corridor not found")
    return _serialize_corridor(updated_corridor)


def restore_green_corridor(corridor_id: str) -> dict[str, Any]:
    corridor_object_id = _to_object_id(corridor_id)
    collection = get_green_corridor_collection()
    corridor = collection.find_one({"_id": corridor_object_id})
    if corridor is None:
        raise LookupError("Green corridor not found")

    updated_actions = [
        {
            **junction_action,
            "signal_action": "NORMAL_SIGNAL_CYCLE_RESTORED",
            "conflicting_traffic_action": "NORMAL_TRAFFIC_FLOW",
            "pre_clear_action": "NORMAL_OPERATION",
            "status": GreenCorridorStatus.COMPLETED.value,
            "timestamp": utc_now(),
        }
        for junction_action in corridor["junction_actions"]
    ]

    update_document = build_green_corridor_update_document(
        {
            "status": GreenCorridorStatus.COMPLETED.value,
            "junction_actions": updated_actions,
        },
    )
    collection.update_one({"_id": corridor_object_id}, {"$set": update_document})
    updated_corridor = collection.find_one({"_id": corridor_object_id})
    if updated_corridor is None:
        raise LookupError("Green corridor not found")
    return _serialize_corridor(updated_corridor)


def get_green_corridor(corridor_id: str) -> dict[str, Any]:
    corridor_object_id = _to_object_id(corridor_id)
    corridor = get_green_corridor_collection().find_one({"_id": corridor_object_id})
    if corridor is None:
        raise LookupError("Green corridor not found")
    return _serialize_corridor(corridor)


def _serialize_corridor(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "ambulance_id": document["ambulance_id"],
        "route": document["route"],
        "destination": document["destination"],
        "status": document["status"],
        "junction_actions": [_serialize_junction_action(item) for item in document["junction_actions"]],
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }


def _serialize_junction_action(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "junction_id": str(document["junction_id"]),
        "priority_direction": document["priority_direction"],
        "signal_action": document["signal_action"],
        "conflicting_traffic_action": document["conflicting_traffic_action"],
        "pre_clear_action": document["pre_clear_action"],
        "status": document["status"],
        "timestamp": document["timestamp"],
    }
