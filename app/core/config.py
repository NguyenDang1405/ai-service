import json
from pathlib import Path
from typing import List, Union
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    OPENAI_API_KEY: str = "dummy-key-for-dev"
    OPENAI_TIMEOUT_SECONDS: float = 15.0
    SERVICE_PORT: int = Field(default=8000, validation_alias=AliasChoices("SERVICE_PORT", "PORT"))
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_NAME: str = "ai-service"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Chuyển đổi chuỗi CORS_ORIGINS ngăn cách bởi dấu phẩy thành danh sách nguồn hợp lệ."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            val = v.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def PORT(self) -> int:
        return self.SERVICE_PORT

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
