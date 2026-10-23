from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, model_validator, computed_field

class StandupRequest(BaseModel):
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dữ liệu ngữ cảnh 24h qua của dự án (activities, PRs, WIP, blockers)"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def extract_context_if_root(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "context" in data and isinstance(data["context"], dict):
                return data
            # If data does not have explicit "context" key, nest the whole dict into context
            return {"context": data}
        return data

class StandupData(BaseModel):
    summaryYesterday: str = Field(
        ...,
        validation_alias=AliasChoices("summaryYesterday", "summary_yesterday"),
        description="Tóm tắt công việc đã thực hiện trong 24 giờ qua"
    )
    planToday: str = Field(
        ...,
        validation_alias=AliasChoices("planToday", "plan_today"),
        description="Kế hoạch và trọng tâm công việc dự kiến cho ngày hôm nay"
    )
    identifiedBlockers: str = Field(
        ...,
        validation_alias=AliasChoices("identifiedBlockers", "identified_blockers"),
        description="Các điểm nghẽn kỹ thuật hoặc vận hành được nhận diện"
    )

    model_config = ConfigDict(populate_by_name=True)

    @computed_field
    @property
    def summary_yesterday(self) -> str:
        return self.summaryYesterday

    @computed_field
    @property
    def plan_today(self) -> str:
        return self.planToday

    @computed_field
    @property
    def identified_blockers(self) -> str:
        return self.identifiedBlockers

