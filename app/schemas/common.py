from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Mã lỗi hệ thống hoặc nghiệp vụ")
    message: str = Field(..., description="Thông điệp chi tiết về lỗi phát sinh")

class ErrorEnvelope(BaseModel):
    success: bool = Field(default=False, description="Trạng thái thực thi thất bại")
    error: ErrorDetail

class ResponseEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="allow")

    success: bool = Field(default=True, description="Trạng thái thực thi thành công")
    data: T = Field(..., description="Dữ liệu kết quả nghiệp vụ")
    message: str = Field(default="Success", description="Thông báo kết quả thực thi")

