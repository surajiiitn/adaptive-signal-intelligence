from copy import deepcopy

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.services import (
    ambulance_route_service,
    congestion_service,
    density_service,
    emergency_service,
    green_corridor_service,
    junction_service,
    lane_correction_service,
    ml_ingestion_service,
    recommendation_service,
    risk_pattern_service,
    roadside_display_service,
    traffic_service,
)


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, key: str, direction: int) -> "FakeCursor":
        self.documents.sort(key=lambda document: document.get(key), reverse=direction == -1)
        return self

    def __iter__(self):
        return iter(deepcopy(self.documents))


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict] = {}

    def insert_one(self, document: dict) -> InsertOneResult:
        stored_document = deepcopy(document)
        stored_document["_id"] = stored_document.get("_id", ObjectId())
        self.documents[stored_document["_id"]] = stored_document
        return InsertOneResult(stored_document["_id"])

    def find(self, filter_query: dict | None = None) -> FakeCursor:
        filter_query = filter_query or {}
        documents = [
            document
            for document in self.documents.values()
            if self._matches(document, filter_query)
        ]
        return FakeCursor(deepcopy(documents))

    def find_one(self, filter_query: dict, sort: list[tuple[str, int]] | None = None):
        cursor = self.find(filter_query)
        if sort:
            key, direction = sort[0]
            cursor.sort(key, direction)
        for document in cursor:
            return document
        return None

    def update_one(self, filter_query: dict, update: dict) -> UpdateResult:
        for document_id, document in self.documents.items():
            if self._matches(document, filter_query):
                self.documents[document_id] = {**document, **update.get("$set", {})}
                return UpdateResult(1)
        return UpdateResult(0)

    @staticmethod
    def _matches(document: dict, filter_query: dict) -> bool:
        return all(document.get(key) == value for key, value in filter_query.items())


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    junctions = FakeCollection()
    traffic_observations = FakeCollection()
    congestion_alerts = FakeCollection()
    recommendations = FakeCollection()
    emergency_triage = FakeCollection()
    green_corridors = FakeCollection()
    ambulance_routes = FakeCollection()
    roadside_displays = FakeCollection()
    risk_patterns = FakeCollection()
    ml_traffic_frames = FakeCollection()
    lane_corrections = FakeCollection()

    monkeypatch.setattr(junction_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(traffic_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(traffic_service, "get_traffic_collection", lambda: traffic_observations)
    monkeypatch.setattr(density_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(density_service, "get_traffic_collection", lambda: traffic_observations)
    monkeypatch.setattr(congestion_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(congestion_service, "get_traffic_collection", lambda: traffic_observations)
    monkeypatch.setattr(
        congestion_service,
        "get_congestion_alert_collection",
        lambda: congestion_alerts,
    )
    monkeypatch.setattr(recommendation_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(
        recommendation_service,
        "get_traffic_collection",
        lambda: traffic_observations,
    )
    monkeypatch.setattr(
        recommendation_service,
        "get_recommendation_collection",
        lambda: recommendations,
    )
    monkeypatch.setattr(emergency_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(emergency_service, "get_traffic_collection", lambda: traffic_observations)
    monkeypatch.setattr(
        emergency_service,
        "get_emergency_triage_collection",
        lambda: emergency_triage,
    )
    monkeypatch.setattr(green_corridor_service, "get_junction_collection", lambda: junctions)
    monkeypatch.setattr(
        green_corridor_service,
        "get_green_corridor_collection",
        lambda: green_corridors,
    )
    monkeypatch.setattr(
        ambulance_route_service,
        "get_junction_collection",
        lambda: junctions,
    )
    monkeypatch.setattr(
        ambulance_route_service,
        "get_traffic_collection",
        lambda: traffic_observations,
    )
    monkeypatch.setattr(
        ambulance_route_service,
        "get_ambulance_route_collection",
        lambda: ambulance_routes,
    )
    monkeypatch.setattr(
        roadside_display_service,
        "get_junction_collection",
        lambda: junctions,
    )
    monkeypatch.setattr(
        roadside_display_service,
        "get_green_corridor_collection",
        lambda: green_corridors,
    )
    monkeypatch.setattr(
        roadside_display_service,
        "get_roadside_display_collection",
        lambda: roadside_displays,
    )
    monkeypatch.setattr(
        risk_pattern_service,
        "get_junction_collection",
        lambda: junctions,
    )
    monkeypatch.setattr(
        risk_pattern_service,
        "get_risk_pattern_collection",
        lambda: risk_patterns,
    )
    monkeypatch.setattr(
        ml_ingestion_service,
        "get_junction_collection",
        lambda: junctions,
    )
    monkeypatch.setattr(
        ml_ingestion_service,
        "get_traffic_collection",
        lambda: traffic_observations,
    )
    monkeypatch.setattr(
        ml_ingestion_service,
        "get_ml_traffic_frame_collection",
        lambda: ml_traffic_frames,
    )
    monkeypatch.setattr(
        lane_correction_service,
        "get_junction_collection",
        lambda: junctions,
    )
    monkeypatch.setattr(
        lane_correction_service,
        "get_lane_correction_collection",
        lambda: lane_corrections,
    )

    return TestClient(app)


def create_junction(client: TestClient, lanes: int = 4) -> str:
    response = client.post(
        "/api/v1/junctions",
        json={
            "name": "Junction For Task 9-12",
            "latitude": 21.1458,
            "longitude": 79.0882,
            "roads": ["Road 1", "Road 2"],
            "lanes": lanes,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_traffic(
    client: TestClient,
    junction_id: str,
    direction: str,
    vehicle_count: int,
    average_speed: float,
    queue_length: float,
) -> None:
    cars = int(vehicle_count * 0.6)
    motorcycles = int(vehicle_count * 0.25)
    buses = int(vehicle_count * 0.05)
    trucks = vehicle_count - cars - motorcycles - buses

    response = client.post(
        "/api/v1/traffic",
        json={
            "junction_id": junction_id,
            "direction": direction,
            "vehicle_count": vehicle_count,
            "cars": cars,
            "motorcycles": motorcycles,
            "buses": buses,
            "trucks": trucks,
            "average_speed": average_speed,
            "queue_length": queue_length,
        },
    )
    assert response.status_code == 201


def build_ml_payload(junction_id: str) -> dict:
    return {
        "frame_id": 14523,
        "timestamp": "2026-08-16T10:30:00.123Z",
        "source": "aic21_cam_5.mp4",
        "junction_id": junction_id,
        "detections": [
            {
                "vehicle_id": "VEH-0042",
                "class": "car",
                "class_id": 0,
                "confidence": 0.92,
                "bbox": {"x1": 120, "y1": 340, "x2": 280, "y2": 450},
                "centroid": {"x": 200, "y": 395},
                "speed_kmh": 28.5,
                "heading_degrees": 175.3,
                "in_roi": "NORTH",
                "track_age_frames": 47,
            }
        ],
        "direction_analytics": {
            "NORTH": {
                "vehicle_count": 45,
                "vehicle_breakdown": {
                    "cars": 22,
                    "motorcycles": 15,
                    "buses": 3,
                    "trucks": 5,
                },
                "density_ratio": 0.68,
                "density_level": "HIGH",
                "average_speed_kmh": 12.3,
                "queue_length_meters": 185.0,
                "flow_rate_veh_per_min": 8.2,
                "occupancy_percent": 78.5,
            }
        },
        "anomalies": [
            {
                "vehicle_id": "VEH-0117",
                "type": "ERRATIC_DRIVING",
                "subtype": "ZIGZAG_MOVEMENT",
                "confidence": 0.78,
                "risk_score": 7.2,
                "bbox": {"x1": 450, "y1": 280, "x2": 520, "y2": 360},
                "centroid": {"x": 485, "y": 320},
                "heading_variance_deg": 42.5,
                "lateral_deviation_px": 85,
                "description": "Zig-zag movement detected",
            }
        ],
        "aggregate_stats": {
            "total_vehicles": 142,
            "total_by_class": {
                "cars": 68,
                "motorcycles": 48,
                "buses": 10,
                "trucks": 16,
            },
            "avg_speed_kmh": 22.1,
            "max_density_direction": "NORTH",
            "overall_congestion_score": 2.45,
            "overall_congestion_level": "CONGESTED",
            "active_tracks": 142,
            "new_tracks_this_frame": 3,
            "lost_tracks_this_frame": 1,
        },
        "frame_metadata": {
            "resolution": {"width": 1920, "height": 1080},
            "inference_time_ms": 18.4,
            "tracking_time_ms": 3.2,
            "total_processing_time_ms": 24.8,
            "model_name": "yolov8n_aic21_finetuned",
            "tracker": "bytetrack",
        },
    }


def test_ambulance_route_post_get_and_history(client: TestClient) -> None:
    first_junction = create_junction(client)
    second_junction = create_junction(client)
    create_traffic(client, first_junction, "NORTH", 100, 30, 80)
    create_traffic(client, second_junction, "EAST", 200, 12, 210)

    payload = {
        "ambulance_id": "AMB-901",
        "current_location": "Sitabuldi Square",
        "route": ["seg-1", "seg-2", "seg-3"],
        "upcoming_junctions": [first_junction, second_junction],
        "destination": "City Hospital",
        "average_speed": 45,
    }
    post_response_one = client.post("/api/v1/ambulance/routes", json=payload)
    post_response_two = client.post("/api/v1/ambulance/routes", json=payload)
    get_response = client.get("/api/v1/ambulance/routes/AMB-901")
    history_response = client.get("/api/v1/ambulance/routes/AMB-901/history")

    assert post_response_one.status_code == 201
    assert post_response_one.json()["congestion_prediction"] in {
        "WARNING",
        "CONGESTION_LIKELY",
        "CRITICAL",
        "CLEAR",
    }
    assert post_response_one.json()["estimated_delay_minutes"] >= 0
    assert post_response_two.status_code == 201
    assert get_response.status_code == 200
    assert get_response.json()["ambulance_id"] == "AMB-901"
    assert history_response.status_code == 200
    assert len(history_response.json()) == 2


def test_ambulance_route_validation_and_not_found(client: TestClient) -> None:
    junction_id = create_junction(client)
    invalid_payload = {
        "ambulance_id": "AMB-902",
        "current_location": "Start",
        "route": ["seg-1"],
        "upcoming_junctions": ["bad-id"],
        "destination": "Hospital",
        "average_speed": 40,
    }
    bad_request = client.post("/api/v1/ambulance/routes", json=invalid_payload)
    missing_junction = client.post(
        "/api/v1/ambulance/routes",
        json={
            "ambulance_id": "AMB-903",
            "current_location": "Start",
            "route": ["seg-1"],
            "upcoming_junctions": [str(ObjectId())],
            "destination": "Hospital",
            "average_speed": 40,
        },
    )
    unknown_route = client.get("/api/v1/ambulance/routes/AMB-NOT-FOUND")
    valid_route = client.post(
        "/api/v1/ambulance/routes",
        json={
            "ambulance_id": "AMB-904",
            "current_location": "Start",
            "route": ["seg-1"],
            "upcoming_junctions": [junction_id],
            "destination": "Hospital",
            "average_speed": 40,
        },
    )
    assert bad_request.status_code == 422
    assert missing_junction.status_code == 404
    assert unknown_route.status_code == 404
    assert valid_route.status_code == 201


def test_roadside_display_messages_history_and_status_integration(client: TestClient) -> None:
    junction_id = create_junction(client)
    corridor_junction = create_junction(client)
    corridor_response = client.post(
        "/api/v1/green-corridor/activate",
        json={
            "ambulance_id": "AMB-905",
            "route": ["Road A"],
            "upcoming_junctions": [
                {"junction_id": corridor_junction, "priority_direction": "NORTH"},
            ],
            "destination": "Hospital",
        },
    )
    assert corridor_response.status_code == 201
    corridor_id = corridor_response.json()["id"]

    warning = client.post(
        "/api/v1/roadside-display",
        json={
            "ambulance_id": "AMB-905",
            "junction_id": junction_id,
            "message_type": "EMERGENCY_WARNING",
        },
    )
    countdown = client.post(
        "/api/v1/roadside-display",
        json={
            "ambulance_id": "AMB-905",
            "junction_id": junction_id,
            "message_type": "COUNTDOWN",
            "countdown_seconds": 30,
            "corridor_id": corridor_id,
        },
    )
    latest = client.get(f"/api/v1/roadside-display/{junction_id}")
    history = client.get(f"/api/v1/roadside-display/{junction_id}/history")

    assert warning.status_code == 201
    assert warning.json()["message"] == "EMERGENCY VEHICLE APPROACHING"
    assert countdown.status_code == 201
    assert countdown.json()["green_corridor_status"] == "ACTIVE"
    assert latest.status_code == 200
    assert latest.json()["message_type"] == "COUNTDOWN"
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_roadside_display_validation_and_not_found(client: TestClient) -> None:
    junction_id = create_junction(client)
    missing_countdown = client.post(
        "/api/v1/roadside-display",
        json={
            "ambulance_id": "AMB-906",
            "junction_id": junction_id,
            "message_type": "COUNTDOWN",
        },
    )
    invalid_id = client.post(
        "/api/v1/roadside-display",
        json={
            "ambulance_id": "AMB-906",
            "junction_id": "bad-id",
            "message_type": "KEEP_LEFT",
        },
    )
    unknown_junction = client.get(f"/api/v1/roadside-display/{str(ObjectId())}")
    assert missing_countdown.status_code == 400
    assert invalid_id.status_code == 422
    assert unknown_junction.status_code == 404


def test_risk_pattern_normal_and_multiple_risk(client: TestClient) -> None:
    junction_id = create_junction(client)
    normal = client.post(
        "/api/v1/risk-patterns",
        json={
            "vehicle_id": "VEH-1001",
            "junction_id": junction_id,
            "lane_id": "L1",
            "speed": 30,
            "previous_speed": 28,
            "direction": "NORTH",
            "previous_direction": "NORTH",
            "lane_position": 1,
            "previous_lane_position": 1,
        },
    )
    risky = client.post(
        "/api/v1/risk-patterns",
        json={
            "vehicle_id": "VEH-1001",
            "junction_id": junction_id,
            "lane_id": "L1",
            "speed": 58,
            "previous_speed": 30,
            "direction": "EAST",
            "previous_direction": "NORTH",
            "lane_position": 3,
            "previous_lane_position": 1,
        },
    )
    latest = client.get("/api/v1/risk-patterns/VEH-1001")
    history = client.get("/api/v1/risk-patterns/VEH-1001/history")

    assert normal.status_code == 201
    assert normal.json()["movement_type"] == "NORMAL"
    assert risky.status_code == 201
    assert risky.json()["risk_score"] >= 60
    assert risky.json()["movement_type"] == "MULTIPLE_RISK"
    assert latest.status_code == 200
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_risk_pattern_validation_and_missing_resource(client: TestClient) -> None:
    invalid_junction = client.post(
        "/api/v1/risk-patterns",
        json={
            "vehicle_id": "VEH-1002",
            "junction_id": "bad-id",
            "lane_id": "L1",
            "speed": 40,
            "previous_speed": 20,
            "direction": "NORTH",
            "previous_direction": "SOUTH",
            "lane_position": 2,
            "previous_lane_position": 1,
        },
    )
    unknown_vehicle = client.get("/api/v1/risk-patterns/VEH-NOT-FOUND")
    assert invalid_junction.status_code == 422
    assert unknown_vehicle.status_code == 404


def test_ml_ingestion_valid_mapped_to_existing_junction(client: TestClient) -> None:
    junction_id = create_junction(client, lanes=3)
    response = client.post("/api/v1/ml/traffic-frame", json=build_ml_payload(junction_id))
    traffic_history = client.get(f"/api/v1/traffic/history/{junction_id}")

    assert response.status_code == 201
    data = response.json()
    assert data["mapped_junction_id"] == junction_id
    assert data["ingested_traffic_observations"] == 1
    assert traffic_history.status_code == 200
    assert len(traffic_history.json()) == 1


def test_ml_ingestion_contract_only_without_mapping(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ml/traffic-frame",
        json=build_ml_payload("junction_nagpur_sitabuldi"),
    )
    assert response.status_code == 201
    assert response.json()["mapped_junction_id"] is None
    assert response.json()["ingested_traffic_observations"] == 0


def test_ml_ingestion_invalid_payload_and_missing_mapped_junction(client: TestClient) -> None:
    payload = build_ml_payload(str(ObjectId()))
    missing_junction = client.post("/api/v1/ml/traffic-frame", json=payload)

    invalid = build_ml_payload("junction_nagpur_sitabuldi")
    invalid["direction_analytics"]["NORTH"]["occupancy_percent"] = 120
    invalid_payload = client.post("/api/v1/ml/traffic-frame", json=invalid)

    assert missing_junction.status_code == 404
    assert invalid_payload.status_code == 422


def test_lane_correction_analyze_get_and_history(client: TestClient) -> None:
    junction_id = create_junction(client)
    first = client.post(
        "/api/v1/lane-correction/analyze",
        json={
            "junction_id": junction_id,
            "ambulance_id": "AMB-910",
            "observations": [
                {
                    "lane_id": "L1",
                    "expected_direction": "NORTH",
                    "observed_direction": "SOUTH",
                    "is_blocked": True,
                    "blocked_vehicle_count": 2,
                    "is_emergency_lane": True,
                }
            ],
        },
    )
    second = client.post(
        "/api/v1/lane-correction/analyze",
        json={
            "junction_id": junction_id,
            "observations": [
                {
                    "lane_id": "L2",
                    "expected_direction": "NORTH",
                    "observed_direction": "NORTH",
                    "is_blocked": False,
                    "blocked_vehicle_count": 0,
                    "is_emergency_lane": False,
                }
            ],
        },
    )
    latest = client.get(f"/api/v1/lane-correction/{junction_id}")
    history = client.get(f"/api/v1/lane-correction/{junction_id}/history")

    assert first.status_code == 201
    assert first.json()["status"] == "RISK_DETECTED"
    assert len(first.json()["issues"]) >= 2
    assert second.status_code == 201
    assert second.json()["status"] == "NORMAL"
    assert latest.status_code == 200
    assert latest.json()["status"] == "NORMAL"
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_lane_correction_invalid_and_missing(client: TestClient) -> None:
    invalid = client.post(
        "/api/v1/lane-correction/analyze",
        json={
            "junction_id": "bad-id",
            "observations": [
                {
                    "lane_id": "L1",
                    "expected_direction": "NORTH",
                    "observed_direction": "NORTH",
                }
            ],
        },
    )
    unknown = client.get(f"/api/v1/lane-correction/{str(ObjectId())}")
    assert invalid.status_code == 422
    assert unknown.status_code == 404
