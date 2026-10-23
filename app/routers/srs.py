from fastapi import APIRouter, status
from app.schemas.common import ResponseEnvelope
from app.schemas.srs import SRSExtractRequest, SRSExtractData
from app.services.srs_service import extract_stories

router = APIRouter(prefix="/srs", tags=["SRS Extraction"])

@router.post(
    "/extract",
    response_model=ResponseEnvelope[SRSExtractData],
    status_code=status.HTTP_200_OK,
    summary="Trích xuất danh sách User Stories đạt chuẩn Agile / INVEST từ tài liệu SRS",
)
async def extract_user_stories_from_srs(payload: SRSExtractRequest):
    data: SRSExtractData = await extract_stories(raw_content=payload.raw_content)
    stories_dump = [s.model_dump() for s in data.stories]
    return {
        "success": True,
        "data": data,
        "message": "User stories extracted successfully",
        "stories": stories_dump,
    }

