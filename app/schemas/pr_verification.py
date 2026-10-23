from typing import List, Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, computed_field

class PRVerifyRequest(BaseModel):
    task_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        validation_alias=AliasChoices("task_title", "taskTitle"),
        description="Tiêu đề tác vụ cần đối soát với PR"
    )
    task_description: str = Field(
        default="",
        max_length=10000,
        validation_alias=AliasChoices("task_description", "taskDescription"),
        description="Mô tả tác vụ"
    )
    checklist: List[Any] = Field(
        default_factory=list,
        description="Danh sách checklist kỹ thuật cần kiểm tra"
    )
    diff_summary: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("diff_summary", "diffSummary"),
        description="Bản tóm tắt mã nguồn thay đổi (git diff / commit log)"
    )

    model_config = ConfigDict(populate_by_name=True)

class PRVerifyData(BaseModel):
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Điểm đánh giá mức độ hoàn thành và chất lượng code (0 - 100)"
    )
    is_verified: bool = Field(
        ...,
        validation_alias=AliasChoices("is_verified", "isVerified"),
        description="Đạt chuẩn kiểm định (score >= 70)"
    )
    feedback: str = Field(
        ...,
        description="Nhận xét súc tích về điểm đạt và thiếu sót của mã nguồn"
    )

    model_config = ConfigDict(populate_by_name=True)

    @computed_field
    @property
    def isVerified(self) -> bool:
        return self.is_verified

