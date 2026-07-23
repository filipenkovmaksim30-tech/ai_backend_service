from fastapi import APIRouter, Depends, status

from backend.api.dependencies import ContactServiceDep, enforce_contact_rate_limit
from backend.schemas import ContactCreate, ContactResponse

router = APIRouter(prefix="/api", tags=["Contact"])


@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_contact_rate_limit)],
    summary="Создать контакт"
)
async def create_contact(
    payload: ContactCreate,
    service: ContactServiceDep,
) -> ContactResponse:
    return await service.create_contact(payload)
