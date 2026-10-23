from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["Health"])

class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Trạng thái dịch vụ")
    service: str = Field(default="ai-service", description="Tên dịch vụ")

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def check_health():
    return HealthResponse(
        status="ok",
        service="ai-service"
    )
