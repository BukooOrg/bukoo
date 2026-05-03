from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    health_status: str
    environment: str
    version: str
    timestamp: str
