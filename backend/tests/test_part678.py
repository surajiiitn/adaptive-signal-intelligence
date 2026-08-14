from copy import deepcopy

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.services import (
    congestion_service,
    density_service,
    emergency_service,
    green_corridor_service,
    junction_service,
    recommendation_service,
    traffic_service,
)


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count


class DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, key: str, direction: int) -> "FakeCursor":
        self.documents.sort(
            key=lambda document: document.get(key),
            reverse=direction == -1,
        )
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

    def delete_one(self, filter_query: dict) -> DeleteResult:
        for document_id, document in list(self.documents.items()):
            if self._matches(document, filter_query):
                del self.documents[document_id]
                return DeleteResult(1)
        return DeleteResult(0)

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
    monkeypatch.setattr(
        recommendation_service,
        "get_junction_collection",
        lambda: junctions,
    )
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

    return TestClient(app)


def create_junction(client: TestClient, lanes: int = 4) -> str:
    response = client.post(
        "/api/v1/junctions",
        json={
            "name": "Junction For Task 6-8",
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


# ------------------ Task 6: Dynamic Traffic Suggestions ------------------ #


def test_recommendation_low_traffic(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 40, 45, 20)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")

    assert response.status_code == 201
    recommendation = response.json()[0]
    assert recommendation["action"] == "DECREASE_GREEN_TIME"
    assert recommendation["priority"] == "LOW"


def test_recommendation_medium_traffic(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 100, 40, 35)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")

    assert response.status_code == 201
    recommendation = response.json()[0]
    assert recommendation["action"] == "KEEP_CURRENT"
    assert recommendation["priority"] == "MEDIUM"


def test_recommendation_high_density(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 180, 42, 40)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")

    assert response.status_code == 201
    recommendation = response.json()[0]
    assert recommendation["density_level"] == "HIGH"
    assert recommendation["action"] == "INCREASE_GREEN_TIME"
    assert recommendation["green_time_change"] > 0


def test_recommendation_critical_congestion(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 220, 10, 220)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")

    assert response.status_code == 201
    recommendation = response.json()[0]
    assert recommendation["congestion_level"] == "CRITICAL"
    assert recommendation["action"] == "REDUCE_CONFLICTING_TRAFFIC"
    assert recommendation["priority"] == "CRITICAL"


def test_recommendation_speed_impact(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 100, 40, 40)
    create_traffic(client, junction_id, "SOUTH", 100, 20, 40)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")
    recommendations = response.json()
    north = next(item for item in recommendations if item["direction"] == "NORTH")
    south = next(item for item in recommendations if item["direction"] == "SOUTH")

    assert north["action"] == "KEEP_CURRENT"
    assert south["action"] in {"PRIORITIZE_DIRECTION", "INCREASE_GREEN_TIME"}


def test_recommendation_queue_impact(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 100, 40, 30)
    create_traffic(client, junction_id, "SOUTH", 100, 40, 100)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")
    recommendations = response.json()
    north = next(item for item in recommendations if item["direction"] == "NORTH")
    south = next(item for item in recommendations if item["direction"] == "SOUTH")

    assert north["action"] == "KEEP_CURRENT"
    assert south["action"] == "PRIORITIZE_DIRECTION"


def test_recommendation_density_impact(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 40, 40, 25)
    create_traffic(client, junction_id, "SOUTH", 180, 40, 25)

    response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")
    recommendations = response.json()
    north = next(item for item in recommendations if item["direction"] == "NORTH")
    south = next(item for item in recommendations if item["direction"] == "SOUTH")

    assert north["density_level"] == "LOW"
    assert south["density_level"] == "HIGH"
    assert south["green_time_change"] > north["green_time_change"]


def test_recommendation_reason_priority_and_api_history(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 120, 28, 90)

    first_response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")
    second_response = client.post(f"/api/v1/traffic/recommendations/{junction_id}")
    history_response = client.get(f"/api/v1/traffic/recommendations/{junction_id}")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["reason"]
    assert history[0]["priority"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_recommendation_invalid_junction(client: TestClient) -> None:
    response = client.post("/api/v1/traffic/recommendations/not-a-valid-id")
    assert response.status_code == 400


# ---------------------- Task 7: Emergency Triage ---------------------- #


def test_triage_critical_patient(client: TestClient) -> None:
    response = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-001",
            "patient_severity": "CRITICAL",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "CRITICAL"
    assert data["emergency_status"] == "CRITICAL"


def test_triage_serious_patient(client: TestClient) -> None:
    response = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-002",
            "patient_severity": "SERIOUS",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "HIGH"
    assert data["emergency_status"] == "HIGH"


def test_triage_stable_patient(client: TestClient) -> None:
    response = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-003",
            "patient_severity": "STABLE",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["priority"] == "NORMAL"
    assert data["emergency_status"] == "NORMAL"


def test_triage_priority_with_congestion(client: TestClient) -> None:
    junction_id = create_junction(client)
    create_traffic(client, junction_id, "NORTH", 220, 10, 220)

    response = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-004",
            "patient_severity": "STABLE",
            "junction_id": junction_id,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["congestion_level"] == "CRITICAL"
    assert data["priority"] == "HIGH"
    assert data["emergency_status"] == "HIGH"


def test_triage_invalid_severity(client: TestClient) -> None:
    response = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-005",
            "patient_severity": "UNKNOWN",
        },
    )
    assert response.status_code == 422


def test_triage_missing_required_fields(client: TestClient) -> None:
    response = client.post(
        "/api/v1/emergency/triage",
        json={"patient_severity": "CRITICAL"},
    )
    assert response.status_code == 422


def test_triage_post_get_and_history_api(client: TestClient) -> None:
    post_response_one = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-006",
            "patient_severity": "SERIOUS",
        },
    )
    post_response_two = client.post(
        "/api/v1/emergency/triage",
        json={
            "ambulance_id": "AMB-006",
            "patient_severity": "CRITICAL",
        },
    )
    get_response = client.get("/api/v1/emergency/triage/AMB-006")
    history_response = client.get("/api/v1/emergency/triage/history/AMB-006")

    assert post_response_one.status_code == 201
    assert post_response_two.status_code == 201
    assert get_response.status_code == 200
    assert get_response.json()["patient_severity"] == "CRITICAL"
    assert history_response.status_code == 200
    assert len(history_response.json()) == 2


def test_triage_invalid_ambulance_lookup(client: TestClient) -> None:
    response = client.get("/api/v1/emergency/triage/AMB-NOT-EXIST")
    assert response.status_code == 404


# ---------------------- Task 8: Green Corridor ---------------------- #


def test_green_corridor_activation_and_active_state(client: TestClient) -> None:
    first_junction = create_junction(client)
    second_junction = create_junction(client)

    response = client.post(
        "/api/v1/green-corridor/activate",
        json={
            "ambulance_id": "AMB-101",
            "route": ["Hospital Road", "Main Road"],
            "upcoming_junctions": [
                {"junction_id": first_junction, "priority_direction": "NORTH"},
                {"junction_id": second_junction, "priority_direction": "EAST"},
            ],
            "destination": "City Hospital",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert len(data["junction_actions"]) == 2
    assert data["junction_actions"][0]["signal_action"] == "PRIORITIZE_DIRECTION"
    assert data["junction_actions"][0]["pre_clear_action"] == "PRE_CLEAR_JUNCTION"
    assert data["junction_actions"][0]["conflicting_traffic_action"] == "HOLD_CONFLICTING_TRAFFIC"


def test_green_corridor_deactivate_and_restore(client: TestClient) -> None:
    first_junction = create_junction(client)

    activate_response = client.post(
        "/api/v1/green-corridor/activate",
        json={
            "ambulance_id": "AMB-102",
            "route": ["Ring Road"],
            "upcoming_junctions": [
                {"junction_id": first_junction, "priority_direction": "SOUTH"},
            ],
            "destination": "Trauma Center",
        },
    )
    corridor_id = activate_response.json()["id"]

    deactivate_response = client.post(f"/api/v1/green-corridor/deactivate/{corridor_id}")
    restore_response = client.post(f"/api/v1/green-corridor/{corridor_id}/restore")

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["status"] == "INACTIVE"
    assert (
        deactivate_response.json()["junction_actions"][0]["conflicting_traffic_action"]
        == "RELEASE_CONFLICTING_TRAFFIC"
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "COMPLETED"
    assert (
        restore_response.json()["junction_actions"][0]["signal_action"]
        == "NORMAL_SIGNAL_CYCLE_RESTORED"
    )


def test_green_corridor_get_and_persisted_state(client: TestClient) -> None:
    first_junction = create_junction(client)
    activate_response = client.post(
        "/api/v1/green-corridor/activate",
        json={
            "ambulance_id": "AMB-103",
            "route": ["Airport Road"],
            "upcoming_junctions": [
                {"junction_id": first_junction, "priority_direction": "WEST"},
            ],
            "destination": "Airport Trauma Unit",
        },
    )

    corridor_id = activate_response.json()["id"]
    get_response = client.get(f"/api/v1/green-corridor/{corridor_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == corridor_id
    assert data["ambulance_id"] == "AMB-103"
    assert data["junction_actions"][0]["priority_direction"] == "WEST"


def test_green_corridor_invalid_id(client: TestClient) -> None:
    response = client.post("/api/v1/green-corridor/deactivate/not-a-valid-id")
    assert response.status_code == 400
