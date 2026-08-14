from fastapi import APIRouter, status

from app.controllers import recommendation_controller
from app.schemas.recommendation_schema import TrafficRecommendationResponse


router = APIRouter(prefix="/traffic/recommendations", tags=["Traffic Recommendations"])


@router.post(
    "/{junction_id}",
    response_model=list[TrafficRecommendationResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_recommendations(junction_id: str) -> list[dict]:
    return recommendation_controller.generate_recommendations(junction_id)


@router.get(
    "/{junction_id}",
    response_model=list[TrafficRecommendationResponse],
)
def get_recommendation_history(junction_id: str) -> list[dict]:
    return recommendation_controller.get_recommendation_history(junction_id)
