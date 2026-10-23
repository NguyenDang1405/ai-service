from typing import List
from pydantic import BaseModel, Field, field_validator

class EmbeddingBatchRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Danh sách các đoạn văn bản cần tạo vector embedding"
    )

    @field_validator("texts")
    @classmethod
    def validate_non_empty_texts(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v]
        if any(len(t) == 0 for t in cleaned):
            raise ValueError("Văn bản trong danh sách texts không được để trống")
        return cleaned

class EmbeddingBatchData(BaseModel):
    embeddings: List[List[float]] = Field(
        ...,
        description="Mảng 2 chiều chứa các vector embedding (kích thước 1536 chiều)"
    )

    @field_validator("embeddings")
    @classmethod
    def validate_embedding_dimensions(cls, v: List[List[float]]) -> List[List[float]]:
        for i, vec in enumerate(v):
            if len(vec) != 1536:
                raise ValueError(f"Vector tại vị trí {i} phải có chính xác 1536 chiều (hiện có {len(vec)})")
        return v

