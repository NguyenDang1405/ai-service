from enum import Enum
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, computed_field

class UserLevelEnum(str, Enum):
    INTERN = "INTERN"
    FRESHER = "FRESHER"
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"

class ChecklistCategoryEnum(str, Enum):
    PREREQUISITE = "PREREQUISITE"
    IMPLEMENTATION = "IMPLEMENTATION"
    TESTING = "TESTING"
    SECURITY = "SECURITY"

class GuidanceRequest(BaseModel):
    task_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        validation_alias=AliasChoices("task_title", "taskTitle"),
        description="Tiêu đề của công việc cần hướng dẫn"
    )
    task_description: str = Field(
        default="",
        max_length=10000,
        validation_alias=AliasChoices("task_description", "taskDescription"),
        description="Mô tả chi tiết nội dung công việc"
    )
    user_level: UserLevelEnum = Field(
        default=UserLevelEnum.JUNIOR,
        validation_alias=AliasChoices("user_level", "userLevel"),
        description="Cấp bậc của lập trình viên nhận công việc"
    )

    model_config = ConfigDict(populate_by_name=True)

class GuidanceItem(BaseModel):
    id: str = Field(..., description="Mã định danh duy nhất của mục kiểm tra (ví dụ: chk-1)")
    task_text: str = Field(
        ...,
        validation_alias=AliasChoices("task_text", "taskText"),
        description="Nội dung chi tiết mục kiểm tra"
    )
    category: ChecklistCategoryEnum = Field(
        ...,
        description="Phân loại mục kiểm tra"
    )

    model_config = ConfigDict(populate_by_name=True)

    @computed_field
    @property
    def taskText(self) -> str:
        return self.task_text

class GuidanceData(BaseModel):
    items: List[GuidanceItem] = Field(
        ...,
        description="Danh sách các mục công việc kiểm tra"
    )

