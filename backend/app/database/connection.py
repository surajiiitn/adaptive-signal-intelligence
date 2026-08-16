from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import settings


client = MongoClient(settings.mongodb_uri)


def get_database() -> Database:
    return client[settings.mongodb_database]


def get_junction_collection() -> Collection:
    return get_database()["junctions"]


def get_traffic_collection() -> Collection:
    return get_database()["traffic_observations"]


def get_congestion_alert_collection() -> Collection:
    return get_database()["congestion_alerts"]


def get_recommendation_collection() -> Collection:
    return get_database()["traffic_recommendations"]


def get_emergency_triage_collection() -> Collection:
    return get_database()["emergency_triage"]


def get_green_corridor_collection() -> Collection:
    return get_database()["green_corridors"]


def get_ambulance_route_collection() -> Collection:
    return get_database()["ambulance_routes"]


def get_roadside_display_collection() -> Collection:
    return get_database()["roadside_displays"]


def get_risk_pattern_collection() -> Collection:
    return get_database()["risk_patterns"]


def get_ml_traffic_frame_collection() -> Collection:
    return get_database()["ml_traffic_frames"]


def get_lane_correction_collection() -> Collection:
    return get_database()["lane_corrections"]
