import hashlib
import logging
import math
from typing import List
from app.services.openai_client import get_async_client, openai_retry
from app.schemas.embeddings import EmbeddingBatchData

logger = logging.getLogger("ai_service.embeddings")

def _generate_deterministic_fallback_vector(text: str, dim: int = 1536) -> List[float]:
    """Tạo vector xác định 1536 chiều từ chuỗi văn bản phục vụ fallback khi mất kết nối."""
    base_hash = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    # Sinh đủ 1536 số thực từ hash lặp
    for i in range(dim):
        byte_val = base_hash[i % len(base_hash)]
        # Tạo giá trị dao động quanh 0
        val = math.sin((i + 1) * byte_val) * 0.05
        values.append(val)
    # Chuẩn hóa L2 norm
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [round(v / norm, 6) for v in values]

@openai_retry
async def _call_openai_embeddings(texts: List[str]) -> List[List[float]]:
    client = get_async_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        encoding_format="float"
    )
    # Sắp xếp đúng theo index thứ tự ban đầu
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]

async def create_embeddings_batch(texts: List[str]) -> EmbeddingBatchData:
    """Tạo danh sách các vector 1536 chiều từ danh sách văn bản."""
    try:
        embeddings = await _call_openai_embeddings(texts)
        return EmbeddingBatchData(embeddings=embeddings)
    except Exception as exc:
        logger.warning(f"[Embeddings Service Fallback]: Không thể gọi OpenAI API ({exc}). Sử dụng fallback xác định.")
        fallback_embeddings = [_generate_deterministic_fallback_vector(t) for t in texts]
        return EmbeddingBatchData(embeddings=fallback_embeddings)

