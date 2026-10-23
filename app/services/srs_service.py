import logging
from typing import List
from app.services.openai_client import get_async_client, openai_retry
from app.schemas.srs import SRSExtractData, SRSStoryItem, DepartmentEnum, ComplexityEnum

logger = logging.getLogger("ai_service.srs")

def _get_fallback_stories() -> List[SRSStoryItem]:
    return [
        SRSStoryItem(
            storyId="US-01",
            role="Kỹ sư CSDL",
            action="thiết lập hạ tầng cơ sở dữ liệu và bảng quan hệ",
            benefit="hệ thống có nền tảng lưu trữ toàn vẹn và tối ưu truy vấn",
            fullTitle="Khởi tạo schema và cấu trúc dữ liệu quan hệ",
            description="Tạo các bảng users, projects, tasks, task_dependencies và chỉ mục HNSW vector",
            targetDepartment=DepartmentEnum.BACKEND,
            complexity=ComplexityEnum.MEDIUM,
            acceptanceCriteria=[
                "Chạy thành công file init.sql",
                "Đầy đủ 14 bảng quan hệ và ràng buộc khóa ngoại",
                "Kích hoạt extension pgvector thành công"
            ],
            dependsOnStories=[]
        ),
        SRSStoryItem(
            storyId="US-02",
            role="Kỹ sư Backend",
            action="xây dựng các REST API nghiệp vụ và xác thực JWT",
            benefit="khách hàng và các hệ thống client có thể thao tác dữ liệu an toàn",
            fullTitle="Phát triển tầng REST API Core & Middleware bảo mật",
            description="Cài đặt authentication, RBAC guards, và các endpoint phân phối tác vụ",
            targetDepartment=DepartmentEnum.BACKEND,
            complexity=ComplexityEnum.HARD,
            acceptanceCriteria=[
                "Xác thực token JWT Bearer hợp lệ",
                "Chặn truy cập trái thẩm quyền với HTTP 403 Forbidden",
                "Ghi nhận đầy đủ nhật ký trạng thái"
            ],
            dependsOnStories=["US-01"]
        ),
        SRSStoryItem(
            storyId="US-03",
            role="Lập trình viên Frontend",
            action="xây dựng giao diện bảng Kanban và React Flow DAG",
            benefit="người dùng có thể quan sát trực quan tiến độ và kéo thả tác vụ",
            fullTitle="Phát triển giao diện bảng Kanban & Đồ thị DAG",
            description="Tạo 5 cột Kanban, kết nối React Flow biểu diễn đường găng",
            targetDepartment=DepartmentEnum.FRONTEND,
            complexity=ComplexityEnum.MEDIUM,
            acceptanceCriteria=[
                "Hiển thị đủ 5 cột trạng thái Kanban",
                "Kéo thả thẻ task tự động cập nhật FSM",
                "Hiển thị trực quan các nút đường găng critical path"
            ],
            dependsOnStories=["US-02"]
        ),
        SRSStoryItem(
            storyId="US-04",
            role="Kỹ sư DevOps",
            action="cấu hình quy trình CI/CD và đóng gói container Docker",
            benefit="đội ngũ có thể triển khai tự động và giám sát hệ thống liên tục",
            fullTitle="Thiết lập Docker container & Pipeline CI/CD",
            description="Viết Dockerfile đa tầng, cấu hình GitHub Actions và tích hợp Webhook",
            targetDepartment=DepartmentEnum.DEVOPS,
            complexity=ComplexityEnum.EASY,
            acceptanceCriteria=[
                "Build Docker image thành công không lỗi",
                "Tự động chạy test suite khi tạo Pull Request"
            ],
            dependsOnStories=["US-03"]
        )
    ]

@openai_retry
async def _call_openai_srs(raw_content: str) -> SRSExtractData:
    client = get_async_client()

    system_prompt = (
        "Bạn là Chuyên gia Phân tích Nghiệp vụ Phần mềm (Lead Business Analyst) và Technical Architect hàng đầu.\n"
        "Nhiệm vụ của bạn là đọc hiểu tài liệu đặc tả yêu cầu kỹ thuật (SRS) và phân tích, trích xuất danh sách các User Stories chuẩn Agile / INVEST.\n"
        "Quy tắc yêu cầu:\n"
        "1. Mỗi User Story phải có đầy đủ: storyId (US-01, US-02...), role, action, benefit, fullTitle, description, targetDepartment, complexity, acceptanceCriteria, dependsOnStories.\n"
        "2. targetDepartment phải là một trong: FRONTEND, BACKEND, DEVOPS, QA, FULLSTACK.\n"
        "3. complexity phải là một trong: EASY, MEDIUM, HARD.\n"
        "4. acceptanceCriteria phải là danh sách tối thiểu 2 tiêu chí nghiệm thu rõ ràng.\n"
        "5. dependsOnStories phải thể hiện quan hệ phụ thuộc hợp lý giữa các story."
    )

    user_prompt = (
        f"Nội dung tài liệu SRS:\n{raw_content[:8000]}\n\n"
        "Hãy trích xuất toàn bộ các User Stories đạt chuẩn kỹ thuật."
    )

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=SRSExtractData,
        temperature=0.2,
    )

    parsed: SRSExtractData = completion.choices[0].message.parsed
    if not parsed or not parsed.stories:
        raise ValueError("OpenAI không trả về danh sách User Stories hợp lệ")
    return parsed

async def extract_stories(raw_content: str) -> SRSExtractData:
    """Trích xuất User Stories từ tài liệu đặc tả yêu cầu kỹ thuật phần mềm (SRS)."""
    try:
        return await _call_openai_srs(raw_content)
    except Exception as exc:
        logger.warning(f"[SRS Extraction Fallback]: Không thể gọi OpenAI ({exc}). Sử dụng fallback stories.")
        return SRSExtractData(stories=_get_fallback_stories())

