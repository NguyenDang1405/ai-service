from .embeddings import router as embeddings_router
from .guidance import router as guidance_router
from .pr_verification import router as pr_router
from .standup import router as standup_router
from .srs import router as srs_router
from .health import router as health_router

__all__ = [
    "embeddings_router",
    "guidance_router",
    "pr_router",
    "standup_router",
    "srs_router",
    "health_router",
]

