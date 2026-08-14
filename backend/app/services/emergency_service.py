from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import (
    get_emergency_triage_collection,
    get_junction_collection,
    get_traffic_collection,
)
from app.models.emergency_model import build_emergency_triage_document
from app.schemas.emergency_schema import EmergencyTriageCreate
from app.services import congestion_service, density_service


def _to_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def create_emergency_triage(triage: EmergencyTriageCreate) -> dict[str, Any]:
    triage_data = triage.model_dump()
    junction_object_id: ObjectId | None = None
    congestion_level: str | None = None
    congestion_note = ""

    if triage.junction_id is not None:
        junction_object_id = _to_object_id(triage.junction_id)
        junction = get_junction_collection().find_one({"_id": junction_object_id})
        if junction is None:
            raise LookupError("Junction not found")

        latest_traffic = get_traffic_collection().find_one(
            {"junction_id": junction_object_id},
            sort=[("timestamp", DESCENDING)],
        )
        if latest_traffic is not None:
            density = density_service.calculate_density(
                latest_traffic["vehicle_count"],
                junction["lanes"],
            )
            congestion_level = congestion_service.classify_congestion(
                density,
                latest_traffic["average_speed"],
                latest_traffic["queue_length"],
            ).value
            if congestion_level == "CRITICAL":
                congestion_note = " Route is critically congested."
            elif congestion_level == "CONGESTED":
                congestion_note = " Route is congested."

    priority, status, reason = _determine_triage(triage.patient_severity.value, congestion_level)
    reason = f"{reason}{congestion_note}".strip()

    document = build_emergency_triage_document(
        {
            "ambulance_id": triage_data["ambulance_id"],
            "patient_severity": triage_data["patient_severity"].value,
            "priority": priority,
            "emergency_status": status,
            "reason": reason,
            "junction_id": junction_object_id,
            "current_location": triage_data["current_location"],
            "destination": triage_data["destination"],
            "congestion_level": congestion_level,
        },
    )
    result = get_emergency_triage_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_triage(document)


def get_current_triage(ambulance_id: str) -> dict[str, Any]:
    document = get_emergency_triage_collection().find_one(
        {"ambulance_id": ambulance_id},
        sort=[("timestamp", DESCENDING)],
    )
    if document is None:
        raise LookupError("Emergency triage not found")
    return _serialize_triage(document)


def get_triage_history(ambulance_id: str) -> list[dict[str, Any]]:
    documents = get_emergency_triage_collection().find(
        {"ambulance_id": ambulance_id},
    ).sort(
        "timestamp",
        DESCENDING,
    )
    history = [_serialize_triage(document) for document in documents]
    if not history:
        raise LookupError("Emergency triage not found")
    return history


def _determine_triage(
    patient_severity: str,
    congestion_level: str | None,
) -> tuple[str, str, str]:
    if patient_severity == "CRITICAL":
        return (
            "CRITICAL",
            "CRITICAL",
            "Critical patient requires immediate traffic priority",
        )

    if patient_severity == "SERIOUS":
        if congestion_level == "CRITICAL":
            return (
                "CRITICAL",
                "CRITICAL",
                "Serious patient elevated due to critical congestion",
            )
        return ("HIGH", "HIGH", "Serious patient requires urgent movement")

    if congestion_level in {"CRITICAL", "CONGESTED"}:
        return (
            "HIGH",
            "HIGH",
            "Stable patient elevated due to heavy traffic conditions",
        )
    return ("NORMAL", "NORMAL", "Stable patient in routine transport condition")


def _serialize_triage(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "ambulance_id": document["ambulance_id"],
        "patient_severity": document["patient_severity"],
        "priority": document["priority"],
        "emergency_status": document["emergency_status"],
        "reason": document["reason"],
        "junction_id": str(document["junction_id"]) if document["junction_id"] else None,
        "current_location": document["current_location"],
        "destination": document["destination"],
        "congestion_level": document["congestion_level"],
        "timestamp": document["timestamp"],
    }
