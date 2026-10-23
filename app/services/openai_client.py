import logging
from typing import Optional
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APITimeoutError, InternalServerError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger("ai_service.openai_client")

# Async client instance
_async_client: Optional[AsyncOpenAI] = None

def get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    return _async_client

# Retry decorator for transient OpenAI API failures
openai_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((
        RateLimitError,
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
    )),
    before_sleep=lambda retry_state: logger.warning(
        f"[OpenAI Retry] Lần thử {retry_state.attempt_number} gặp lỗi: {retry_state.outcome.exception()}. Đang thử lại..."
    )
)

