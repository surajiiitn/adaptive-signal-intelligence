from typing import Any

from fastapi import HTTPException, status

from app.services import recommendation_service


def generate_recommendations(junction_id: str) -> list[dict[str, Any]]:
    try:
        return recommendation_service.generate_recommendations(junction_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


def get_recommendation_history(junction_id: str) -> list[dict[str, Any]]:
    try:
        return recommendation_service.get_recommendation_history(junction_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
