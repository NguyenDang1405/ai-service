from enum import Enum
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

class DepartmentEnum(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DEVOPS = "DEVOPS"
    QA = "QA"
    FULLSTACK = "FULLSTACK"

class ComplexityEnum(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class SRSExtractRequest(BaseModel):
    raw_content: str = Field(
        ...,
        min_length=10,
        validation_alias=AliasChoices("raw_content", "rawContent"),
        description="Nội dung văn bản đặc tả yêu cầu kỹ thuật phần mềm (SRS)"
    )

    model_config = ConfigDict(populate_by_name=True)

class SRSStoryItem(BaseModel):
    storyId: str = Field(..., description="Mã định danh User Story (e.g. US-01)")
    role: str = Field(..., description="Vai trò người dùng (e.g. Lập trình viên Backend)")
    action: str = Field(..., description="Hành động mong muốn thực thi")
    benefit: str = Field(..., description="Lợi ích mang lại cho hệ thống hoặc người dùng")
    fullTitle: str = Field(..., description="Tiêu đề đầy đủ chuẩn hóa của User Story")
    description: str = Field(..., description="Mô tả kỹ thuật chi tiết của User Story")
    targetDepartment: DepartmentEnum = Field(..., description="Phòng ban kỹ thuật phụ trách")
    complexity: ComplexityEnum = Field(..., description="Độ phức tạp ước lượng")
    acceptanceCriteria: List[str] = Field(
        default_factory=list,
        description="Danh sách tiêu chí nghiệm thu kiểm thử (Acceptance Criteria)"
    )
    dependsOnStories: List[str] = Field(
        default_factory=list,
        description="Danh sách mã User Story phụ thuộc (dependencies)"
    )

    model_config = ConfigDict(populate_by_name=True)

class SRSExtractData(BaseModel):
    stories: List[SRSStoryItem] = Field(
        ...,
        description="Danh sách các User Stories chuẩn hóa INVEST được bóc tách"
    )

