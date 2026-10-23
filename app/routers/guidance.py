from fastapi import APIRouter, status
from app.schemas.common import ResponseEnvelope
from app.schemas.guidance import GuidanceRequest, GuidanceData
from app.services.guidance_service import generate_guidance

router = APIRouter(prefix="/guidance", tags=["Adaptive Guidance"])

@router.post(
    "/generate",
    response_model=ResponseEnvelope[GuidanceData],
    status_code=status.HTTP_200_OK,
    summary="Sinh danh sách checklist kiểm tra thích ứng theo cấp bậc nhân sự",
)
async def create_guidance_checklist(payload: GuidanceRequest):
    data: GuidanceData = await generate_guidance(
        task_title=payload.task_title,
        task_description=payload.task_description,
        user_level=payload.user_level,
    )
    items_dump = [item.model_dump() for item in data.items]
    return {
        "success": True,
        "data": data,
        "message": "Adaptive guidance checklist generated successfully",
        "items": items_dump,
        "checklist": items_dump,
    }

