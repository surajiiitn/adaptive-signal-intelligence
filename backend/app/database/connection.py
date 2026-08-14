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
