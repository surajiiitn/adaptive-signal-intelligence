import utils.clients
import utils.http_session
import utils.transport
import utils.session
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import (
    ambulance_route_routes,
    congestion_routes,
    density_routes,
    emergency_routes,
    green_corridor_routes,
    junction_routes,
    lane_correction_routes,
    ml_ingestion_routes,
    recommendation_routes,
    risk_pattern_routes,
    roadside_display_routes,
    traffic_routes,
)


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.api_v1_prefix}/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(junction_routes.router, prefix=settings.api_v1_prefix)
app.include_router(traffic_routes.router, prefix=settings.api_v1_prefix)
app.include_router(density_routes.router, prefix=settings.api_v1_prefix)
app.include_router(congestion_routes.router, prefix=settings.api_v1_prefix)
app.include_router(recommendation_routes.router, prefix=settings.api_v1_prefix)
app.include_router(emergency_routes.router, prefix=settings.api_v1_prefix)
app.include_router(green_corridor_routes.router, prefix=settings.api_v1_prefix)
app.include_router(ambulance_route_routes.router, prefix=settings.api_v1_prefix)
app.include_router(roadside_display_routes.router, prefix=settings.api_v1_prefix)
app.include_router(risk_pattern_routes.router, prefix=settings.api_v1_prefix)
app.include_router(ml_ingestion_routes.router, prefix=settings.api_v1_prefix)
app.include_router(lane_correction_routes.router, prefix=settings.api_v1_prefix)
