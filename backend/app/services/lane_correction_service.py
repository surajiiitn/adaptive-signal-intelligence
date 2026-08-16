from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.connection import get_junction_collection, get_lane_correction_collection
from app.models.lane_correction_model import build_lane_correction_document
from app.schemas.lane_correction_schema import (
    LaneCorrectionAnalyzeRequest,
    LaneCorrectionStatus,
    LaneIssueType,
    LaneObservationInput,
    LaneSeverity,
)
from app.schemas.recommendation_schema import RecommendationPriority


def _to_object_id(junction_id: str) -> ObjectId:
    if not ObjectId.is_valid(junction_id):
        raise ValueError("Invalid junction ID")
    return ObjectId(junction_id)


def analyze_lane_correction(payload: LaneCorrectionAnalyzeRequest) -> dict[str, Any]:
    junction_object_id = _to_object_id(payload.junction_id)
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")

    issues: list[dict[str, str]] = []
    for observation in payload.observations:
        issues.extend(_build_lane_issues(observation))

    status = LaneCorrectionStatus.RISK_DETECTED.value if issues else LaneCorrectionStatus.NORMAL.value

    document = build_lane_correction_document(
        {
            "junction_id": junction_object_id,
            "ambulance_id": payload.ambulance_id,
            "status": status,
            "issues": issues,
            "timestamp": payload.timestamp,
        },
    )
    result = get_lane_correction_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_lane_correction(document)


def get_latest_lane_correction(junction_id: str) -> dict[str, Any]:
    junction_object_id = _to_object_id(junction_id)
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")

    document = get_lane_correction_collection().find_one(
        {"junction_id": junction_object_id},
        sort=[("timestamp", DESCENDING)],
    )
    if document is None:
        raise LookupError("Lane correction analysis not found")
    return _serialize_lane_correction(document)


def get_lane_correction_history(junction_id: str) -> list[dict[str, Any]]:
    junction_object_id = _to_object_id(junction_id)
    junction = get_junction_collection().find_one({"_id": junction_object_id})
    if junction is None:
        raise LookupError("Junction not found")

    documents = get_lane_correction_collection().find({"junction_id": junction_object_id}).sort(
        "timestamp",
        DESCENDING,
    )
    history = [_serialize_lane_correction(document) for document in documents]
    if not history:
        raise LookupError("Lane correction analysis not found")
    return history


def _build_lane_issues(observation: LaneObservationInput) -> list[dict[str, str]]:
    lane_issues: list[dict[str, str]] = []

    if observation.expected_direction != observation.observed_direction:
        lane_issues.append(
            {
                "lane_id": observation.lane_id,
                "issue_type": LaneIssueType.WRONG_LANE_MOVEMENT.value,
                "severity": LaneSeverity.MEDIUM.value,
                "priority": RecommendationPriority.HIGH.value,
                "suggestion": "MOVE TO LEFT LANE",
                "reason": "Vehicle movement direction does not match lane direction",
            },
        )

    if observation.is_blocked and observation.is_emergency_lane:
        lane_issues.append(
            {
                "lane_id": observation.lane_id,
                "issue_type": LaneIssueType.EMERGENCY_LANE_BLOCKAGE.value,
                "severity": LaneSeverity.CRITICAL.value,
                "priority": RecommendationPriority.CRITICAL.value,
                "suggestion": "DO NOT BLOCK AMBULANCE LANE",
                "reason": "Emergency lane is blocked and must be cleared immediately",
            },
        )
    elif observation.is_blocked:
        lane_issues.append(
            {
                "lane_id": observation.lane_id,
                "issue_type": LaneIssueType.LANE_BLOCKAGE.value,
                "severity": LaneSeverity.HIGH.value,
                "priority": RecommendationPriority.HIGH.value,
                "suggestion": "LANE BLOCKAGE DETECTED",
                "reason": "Lane blockage observed and traffic flow may degrade",
            },
        )

    if (
        observation.is_blocked
        and observation.is_emergency_lane
        and observation.blocked_vehicle_count > 0
    ):
        lane_issues.append(
            {
                "lane_id": observation.lane_id,
                "issue_type": LaneIssueType.EMERGENCY_LANE_BLOCKAGE.value,
                "severity": LaneSeverity.CRITICAL.value,
                "priority": RecommendationPriority.CRITICAL.value,
                "suggestion": "CLEAR EMERGENCY LANE",
                "reason": "Emergency lane blockage count is non-zero and requires immediate action",
            },
        )
    return lane_issues


def _serialize_lane_correction(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "junction_id": str(document["junction_id"]),
        "ambulance_id": document["ambulance_id"],
        "status": document["status"],
        "issues": document["issues"],
        "timestamp": document["timestamp"],
    }
