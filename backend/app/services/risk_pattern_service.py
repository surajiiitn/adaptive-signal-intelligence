from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import (
    get_junction_collection,
    get_risk_pattern_collection,
)
from app.models.risk_pattern_model import build_risk_pattern_document
from app.schemas.risk_pattern_schema import MovementType, RiskLevel, VehicleMovementCreate


def _to_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def analyze_vehicle_movement(payload: VehicleMovementCreate) -> dict[str, Any]:
    junction_object_id = _to_object_id(payload.junction_id)
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")

    movement_type, risk_score, reason = _analyze_movement_rules(payload)
    risk_level = _classify_risk_level(risk_score)
    alert_created = risk_score >= 60

    document = build_risk_pattern_document(
        {
            "vehicle_id": payload.vehicle_id,
            "junction_id": junction_object_id,
            "lane_id": payload.lane_id,
            "movement_type": movement_type,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reason": reason,
            "alert_created": alert_created,
            "timestamp": payload.timestamp,
        },
    )
    result = get_risk_pattern_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_pattern(document)


def get_latest_risk_pattern(vehicle_id: str) -> dict[str, Any]:
    document = get_risk_pattern_collection().find_one(
        {"vehicle_id": vehicle_id},
        sort=[("timestamp", DESCENDING)],
    )
    if document is None:
        raise LookupError("Risk pattern not found")
    return _serialize_pattern(document)


def get_risk_pattern_history(vehicle_id: str) -> list[dict[str, Any]]:
    documents = get_risk_pattern_collection().find({"vehicle_id": vehicle_id}).sort(
        "timestamp",
        DESCENDING,
    )
    history = [_serialize_pattern(document) for document in documents]
    if not history:
        raise LookupError("Risk pattern not found")
    return history


def _analyze_movement_rules(payload: VehicleMovementCreate) -> tuple[str, int, str]:
    speed_delta = abs(payload.speed - payload.previous_speed)
    lane_delta = abs(payload.lane_position - payload.previous_lane_position)
    direction_changed = payload.direction != payload.previous_direction
    speed_changed = speed_delta >= 20
    lane_deviation = lane_delta >= 2
    zig_zag = direction_changed and lane_delta >= 1
    unsafe_cut = direction_changed and lane_delta >= 1 and speed_delta >= 15

    score = 0
    reasons: list[str] = []
    anomaly_count = 0

    if zig_zag:
        score += 30
        anomaly_count += 1
        reasons.append("Zig-zag movement detected")
    if lane_deviation:
        score += 25
        anomaly_count += 1
        reasons.append("Sudden lane deviation detected")
    if speed_changed:
        score += 20
        anomaly_count += 1
        reasons.append("Large sudden speed change detected")
    if unsafe_cut:
        score += 30
        anomaly_count += 1
        reasons.append("Unsafe cut movement detected")
    if anomaly_count >= 2:
        score += 10
        reasons.append("Multiple risk patterns detected simultaneously")

    score = min(score, 100)
    if anomaly_count == 0:
        return (
            MovementType.NORMAL.value,
            10,
            "Normal vehicle movement",
        )
    if anomaly_count >= 2:
        return (
            MovementType.MULTIPLE_RISK.value,
            score,
            "; ".join(reasons),
        )
    if unsafe_cut:
        return (
            MovementType.UNSAFE_CUT.value,
            score,
            "; ".join(reasons),
        )
    if zig_zag:
        return (
            MovementType.ZIG_ZAG.value,
            score,
            "; ".join(reasons),
        )
    if lane_deviation:
        return (
            MovementType.SUDDEN_LANE_DEVIATION.value,
            score,
            "; ".join(reasons),
        )
    return (
        MovementType.SUDDEN_SPEED_CHANGE.value,
        score,
        "; ".join(reasons),
    )


def _classify_risk_level(score: int) -> str:
    if score <= 20:
        return RiskLevel.LOW.value
    if score <= 60:
        return RiskLevel.MEDIUM.value
    if score <= 80:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


def _serialize_pattern(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "vehicle_id": document["vehicle_id"],
        "junction_id": str(document["junction_id"]),
        "lane_id": document["lane_id"],
        "movement_type": document["movement_type"],
        "risk_score": document["risk_score"],
        "risk_level": document["risk_level"],
        "reason": document["reason"],
        "alert_created": document["alert_created"],
        "timestamp": document["timestamp"],
    }
