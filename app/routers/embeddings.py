from fastapi import APIRouter, status
from app.schemas.common import ResponseEnvelope
from app.schemas.embeddings import EmbeddingBatchRequest, EmbeddingBatchData
from app.services.embeddings_service import create_embeddings_batch

router = APIRouter(prefix="/embeddings", tags=["Vector Embeddings"])

@router.post(
    "/batch",
    response_model=ResponseEnvelope[EmbeddingBatchData],
    status_code=status.HTTP_200_OK,
    summary="Sinh danh sách vector embeddings 1536 chiều cho văn bản",
)
async def generate_embeddings_batch(payload: EmbeddingBatchRequest):
    data: EmbeddingBatchData = await create_embeddings_batch(payload.texts)
    # Trả về ResponseEnvelope chuẩn hóa kèm trường 'embeddings' đồng bộ ở root
    return {
        "success": True,
        "data": data,
        "message": "Vector embeddings generated successfully",
        "embeddings": data.embeddings,
    }

