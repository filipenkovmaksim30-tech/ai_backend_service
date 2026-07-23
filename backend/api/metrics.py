from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    MetricsServiceDep,
    enforce_metrics_access,
)
from backend.schemas import MetricsResponse

router = APIRouter(prefix="/api", tags=["Metrics"])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    dependencies=[Depends(enforce_metrics_access)],
    summary="Получить метрики"
)
async def get_metrics(service: MetricsServiceDep) -> MetricsResponse:
    return await service.get_metrics()
