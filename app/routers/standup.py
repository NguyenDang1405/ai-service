from fastapi import APIRouter, status
from app.schemas.common import ResponseEnvelope
from app.schemas.standup import StandupRequest, StandupData
from app.services.standup_service import generate_standup

router = APIRouter(prefix="/standup", tags=["Daily Standup"])

@router.post(
    "/generate",
    response_model=ResponseEnvelope[StandupData],
    status_code=status.HTTP_200_OK,
    summary="Tổng hợp báo cáo Daily Standup tự động từ ngữ cảnh dự án 24h",
)
async def create_daily_standup(payload: StandupRequest):
    data: StandupData = await generate_standup(context=payload.context)
    return {
        "success": True,
        "data": data,
        "message": "Daily standup synthesized successfully",
        "summaryYesterday": data.summaryYesterday,
        "planToday": data.planToday,
        "identifiedBlockers": data.identifiedBlockers,
        "summary_yesterday": data.summaryYesterday,
        "plan_today": data.planToday,
        "identified_blockers": data.identifiedBlockers,
    }

