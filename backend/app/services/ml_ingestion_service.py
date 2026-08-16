from typing import Any

from bson import ObjectId

from app.database.connection import (
    get_junction_collection,
    get_ml_traffic_frame_collection,
    get_traffic_collection,
)
from app.models.ml_traffic_frame_model import build_ml_traffic_frame_document
from app.models.traffic_model import build_traffic_observation_document
from app.schemas.ml_traffic_frame_schema import MlTrafficFrameCreate
from app.services import density_service


def ingest_traffic_frame(payload: MlTrafficFrameCreate) -> dict[str, Any]:
    mapped_junction_object_id: ObjectId | None = None
    if ObjectId.is_valid(payload.junction_id):
        possible_junction_id = ObjectId(payload.junction_id)
        junction = get_junction_collection().find_one({"_id": possible_junction_id})
        if junction is None:
            raise LookupError("Junction not found")
        mapped_junction_object_id = possible_junction_id

    normalized_directions = _normalize_direction_analytics(payload, mapped_junction_object_id)
    ingested_traffic_count = _ingest_direction_traffic_observations(
        mapped_junction_object_id,
        normalized_directions,
    )

    document = build_ml_traffic_frame_document(
        {
            "frame_id": payload.frame_id,
            "timestamp": payload.timestamp,
            "source": payload.source,
            "junction_id": payload.junction_id,
            "mapped_junction_id": mapped_junction_object_id,
            "raw_payload": payload.model_dump(by_alias=True),
            "normalized_directions": normalized_directions,
            "ingested_traffic_observations": ingested_traffic_count,
            "metadata": {
                "ingestion_mode": "contract_only_with_rule_normalization",
                "ml_model_bound": False,
            },
        },
    )
    result = get_ml_traffic_frame_collection().insert_one(document)
    document["_id"] = result.inserted_id
    return _serialize_ingestion(document)


def _normalize_direction_analytics(
    payload: MlTrafficFrameCreate,
    mapped_junction_object_id: ObjectId | None,
) -> list[dict[str, Any]]:
    lane_count = None
    if mapped_junction_object_id is not None:
        junction = get_junction_collection().find_one({"_id": mapped_junction_object_id})
        if junction is not None:
            lane_count = junction.get("lanes")

    normalized: list[dict[str, Any]] = []
    for direction, analytics in payload.direction_analytics.items():
        normalized_direction = direction.strip().upper()
        breakdown = analytics.vehicle_breakdown or {}
        cars = int(breakdown.get("cars", 0))
        motorcycles = int(breakdown.get("motorcycles", 0))
        buses = int(breakdown.get("buses", 0))
        trucks = int(breakdown.get("trucks", 0))
        vehicle_count = analytics.vehicle_count

        if lane_count and lane_count > 0:
            density = density_service.calculate_density(vehicle_count, lane_count)
            density_level = density_service.classify_density(density).value
        else:
            density = round(analytics.density_ratio, 2)
            density_level = analytics.density_level.strip().upper()

        normalized.append(
            {
                "direction": normalized_direction,
                "vehicle_count": vehicle_count,
                "cars": cars,
                "motorcycles": motorcycles,
                "buses": buses,
                "trucks": trucks,
                "average_speed": analytics.average_speed_kmh,
                "queue_length": analytics.queue_length_meters,
                "density": density,
                "density_level": density_level,
            },
        )
    normalized.sort(key=lambda item: item["direction"])
    return normalized


def _ingest_direction_traffic_observations(
    mapped_junction_object_id: ObjectId | None,
    normalized_directions: list[dict[str, Any]],
) -> int:
    if mapped_junction_object_id is None:
        return 0

    count = 0
    for direction in normalized_directions:
        observation_data = {
            "direction": direction["direction"],
            "vehicle_count": direction["vehicle_count"],
            "cars": direction["cars"],
            "motorcycles": direction["motorcycles"],
            "buses": direction["buses"],
            "trucks": direction["trucks"],
            "average_speed": direction["average_speed"],
            "queue_length": direction["queue_length"],
        }
        document = build_traffic_observation_document(observation_data, mapped_junction_object_id)
        get_traffic_collection().insert_one(document)
        count += 1
    return count


def _serialize_ingestion(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "frame_id": document["frame_id"],
        "junction_id": document["junction_id"],
        "mapped_junction_id": (
            str(document["mapped_junction_id"]) if document["mapped_junction_id"] else None
        ),
        "ingested_traffic_observations": document["ingested_traffic_observations"],
        "normalized_directions": [
            {
                "direction": item["direction"],
                "vehicle_count": item["vehicle_count"],
                "average_speed": item["average_speed"],
                "queue_length": item["queue_length"],
                "density_level": item["density_level"],
            }
            for item in document["normalized_directions"]
        ],
        "timestamp": document["timestamp"],
        "ingested_at": document["ingested_at"],
        "source": document["source"],
        "metadata": document["metadata"],
    }
