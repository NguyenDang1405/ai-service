from fastapi import APIRouter, status
from app.schemas.common import ResponseEnvelope
from app.schemas.pr_verification import PRVerifyRequest, PRVerifyData
from app.services.pr_service import verify_pr

router = APIRouter(prefix="/pr", tags=["PR Verification"])

@router.post(
    "/verify",
    response_model=ResponseEnvelope[PRVerifyData],
    status_code=status.HTTP_200_OK,
    summary="Thẩm định chất lượng mã nguồn PR đối chiếu checklist task",
)
async def verify_pull_request(payload: PRVerifyRequest):
    data: PRVerifyData = await verify_pr(
        task_title=payload.task_title,
        task_description=payload.task_description,
        checklist=payload.checklist,
        diff_summary=payload.diff_summary,
    )
    return {
        "success": True,
        "data": data,
        "message": "PR verification completed successfully",
        "score": data.score,
        "is_verified": data.is_verified,
        "isVerified": data.is_verified,
        "feedback": data.feedback,
    }

