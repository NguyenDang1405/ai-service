import logging
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.common import ErrorEnvelope, ErrorDetail
from app.routers.embeddings import router as embeddings_router
from app.routers.guidance import router as guidance_router
from app.routers.pr_verification import router as pr_router
from app.routers.standup import router as standup_router
from app.routers.srs import router as srs_router
from app.routers.health import router as health_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_service.main")

# Initialize FastAPI app
app = FastAPI(
    title="Smart Workspace AI Microservice",
    version=settings.SERVICE_VERSION,
    description=(
        "Microservice Python (FastAPI) cung cấp các năng lực Trí tuệ Nhân tạo chuyên sâu: "
        "Vector Embeddings (pgvector), Adaptive Guidance Checklist, PR Code Review Verification, "
        "Automated Daily Standup Synthesis, và INVEST SRS User Story Extraction."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for Pydantic request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Dữ liệu không hợp lệ")
        error_messages.append(f"{loc}: {msg}")

    detail_str = "; ".join(error_messages)
    logger.warning(f"[Validation Error] {request.method} {request.url.path}: {detail_str}")

    error_response = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=f"Dữ liệu đầu vào không hợp lệ: {detail_str}",
        ),
    )
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
    )

# Exception handler for HTTPExceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"[HTTP Exception] {request.method} {request.url.path} - {exc.status_code}: {exc.detail}")
    error_response = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )

# Global catch-all exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"[Unhandled Server Error] {request.method} {request.url.path}: {exc}", exc_info=True)
    error_response = ErrorEnvelope(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="Đã có lỗi hệ thống phát sinh trong quá trình xử lý yêu cầu AI.",
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )

# Register Routers
app.include_router(health_router)
app.include_router(embeddings_router, prefix="/api/v1")
app.include_router(guidance_router, prefix="/api/v1")
app.include_router(pr_router, prefix="/api/v1")
app.include_router(standup_router, prefix="/api/v1")
app.include_router(srs_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.PORT,
        reload=True,
    )
