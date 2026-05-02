from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_configs

# from app.domain.exceptions import InvalidCredentialsError
from app.presentation.schemas.health_schema import HealthCheckResponse

router = APIRouter(tags=["health"])

STATUS_HEALTHY = "healthy"


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=200,
    operation_id="healthCheck",
)
async def health() -> HealthCheckResponse:
    configs = get_configs()

    response = {
        "health_status": STATUS_HEALTHY,
        "environment": configs.ENVIRONMENT.value,
        "version": configs.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    # raise InvalidCredentialsError()

    return HealthCheckResponse(**response)
