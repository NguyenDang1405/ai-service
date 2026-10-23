import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Kiểm thử GET /health"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"

@pytest.mark.asyncio
async def test_embeddings_batch(client: AsyncClient):
    """Kiểm thử POST /api/v1/embeddings/batch"""
    payload = {
        "texts": [
            "Lập trình viên backend phát triển API với NestJS và PostgreSQL",
            "Thiết kế giao diện người dùng bằng Tailwind CSS và React Flow"
        ]
    }
    response = await client.post("/api/v1/embeddings/batch", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    # Kiểm tra Uniform Envelope
    assert res_json["success"] is True
    assert "data" in res_json
    assert "message" in res_json

    # Kiểm tra dữ liệu vector embeddings 1536 chiều
    embeddings = res_json["data"]["embeddings"]
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536
    assert len(embeddings[1]) == 1536
    assert all(isinstance(val, float) for val in embeddings[0])

@pytest.mark.asyncio
async def test_embeddings_batch_validation_error(client: AsyncClient):
    """Kiểm thử bắt lỗi xác thực đầu vào cho POST /api/v1/embeddings/batch"""
    payload = {"texts": ["   "]}  # Text rỗng sau khi strip
    response = await client.post("/api/v1/embeddings/batch", json=payload)
    assert response.status_code == 422
    res_json = response.json()

    # Kiểm tra Error Envelope
    assert res_json["success"] is False
    assert "error" in res_json
    assert res_json["error"]["code"] == "VALIDATION_ERROR"
    assert len(res_json["error"]["message"]) > 0

@pytest.mark.asyncio
async def test_guidance_generate_intern(client: AsyncClient):
    """Kiểm thử POST /api/v1/guidance/generate cho cấp INTERN (kỳ vọng 5-7 items)"""
    payload = {
        "taskTitle": "Khởi tạo kết nối Prisma CSDL",
        "taskDescription": "Cấu hình DATABASE_URL và kiểm tra seed mẫu",
        "userLevel": "INTERN"
    }
    response = await client.post("/api/v1/guidance/generate", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    items = res_json["data"]["items"]
    assert 5 <= len(items) <= 7

    for item in items:
        assert "id" in item
        assert "task_text" in item or "taskText" in item
        assert item["category"] in ["PREREQUISITE", "IMPLEMENTATION", "TESTING", "SECURITY"]

@pytest.mark.asyncio
async def test_guidance_generate_senior(client: AsyncClient):
    """Kiểm thử POST /api/v1/guidance/generate cho cấp SENIOR (kỳ vọng 2-3 items)"""
    payload = {
        "task_title": "Kiến trúc Multi-tenant Zero Downtime",
        "task_description": "Phân mảnh database và đồng bộ cache",
        "user_level": "SENIOR"
    }
    response = await client.post("/api/v1/guidance/generate", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    items = res_json["data"]["items"]
    assert 2 <= len(items) <= 3

@pytest.mark.asyncio
async def test_pr_verify(client: AsyncClient):
    """Kiểm thử POST /api/v1/pr/verify"""
    payload = {
        "taskTitle": "Phát triển tính năng đăng ký người dùng",
        "taskDescription": "Tạo API auth register, hash mật khẩu bằng bcrypt",
        "checklist": [
            {"id": "chk-1", "taskText": "Băm mật khẩu trước khi lưu DB", "category": "SECURITY"},
            {"id": "chk-2", "taskText": "Validate email hợp lệ và kiểm tra trùng lặp", "category": "IMPLEMENTATION"}
        ],
        "diffSummary": (
            "+ const hash = await bcrypt.hash(password, 10);\n"
            "+ const user = await prisma.user.create({ data: { email, passwordHash: hash } });\n"
            "+ return res.status(201).json(user);"
        )
    }
    response = await client.post("/api/v1/pr/verify", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    data = res_json["data"]
    assert 0 <= data["score"] <= 100
    assert isinstance(data["is_verified"], bool)
    assert data["is_verified"] == (data["score"] >= 70)
    assert len(data["feedback"]) > 0

@pytest.mark.asyncio
async def test_standup_generate(client: AsyncClient):
    """Kiểm thử POST /api/v1/standup/generate"""
    payload = {
        "context": {
            "projectName": "Smart Workspace Platform",
            "activities24h": [
                {"action": "TASK_TRANSITION", "taskId": "t-1", "toStatus": "DONE"},
                {"action": "PR_MERGED", "prNumber": 12}
            ],
            "pullRequests": [{"id": "pr-12", "title": "feat: add vector embeddings"}],
            "wipPlan": [{"id": "t-2", "title": "Build Kanban board", "isCritical": True}],
            "blockers": [{"task": "Docker Compose", "reason": "Port 5433 conflict"}]
        }
    }
    response = await client.post("/api/v1/standup/generate", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    data = res_json["data"]
    assert len(data["summaryYesterday"]) > 0
    assert len(data["planToday"]) > 0
    assert len(data["identifiedBlockers"]) > 0

@pytest.mark.asyncio
async def test_srs_extract(client: AsyncClient):
    """Kiểm thử POST /api/v1/srs/extract"""
    payload = {
        "rawContent": (
            "# HỆ THỐNG QUẢN LÝ DỰ ÁN THÔNG MINH\n"
            "## 1. Yêu cầu Cơ sở dữ liệu và Xác thực\n"
            "- Người dùng có thể đăng ký tài khoản mới và đăng nhập an toàn bằng JWT.\n"
            "- Hệ thống hỗ trợ phân quyền người dùng theo các vai trò ADMIN và MEMBER.\n"
            "## 2. Yêu cầu Giao diện Kanban\n"
            "- Người dùng có thể kéo thả các thẻ tác vụ trên bảng Kanban 5 cột.\n"
        )
    }
    response = await client.post("/api/v1/srs/extract", json=payload)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    stories = res_json["data"]["stories"]
    assert len(stories) >= 1

    first_story = stories[0]
    assert "storyId" in first_story
    assert "role" in first_story
    assert "action" in first_story
    assert "benefit" in first_story
    assert "fullTitle" in first_story
    assert first_story["targetDepartment"] in ["FRONTEND", "BACKEND", "DEVOPS", "QA", "FULLSTACK"]
    assert first_story["complexity"] in ["EASY", "MEDIUM", "HARD"]
    assert isinstance(first_story["acceptanceCriteria"], list)
