import logging
from typing import List
from app.services.openai_client import get_async_client, openai_retry
from app.schemas.guidance import GuidanceData, GuidanceItem, UserLevelEnum, ChecklistCategoryEnum

logger = logging.getLogger("ai_service.guidance")

def _get_fallback_checklist(user_level: UserLevelEnum, task_title: str) -> List[GuidanceItem]:
    level = user_level.value.upper()
    if level in ["INTERN", "FRESHER"]:
        return [
            GuidanceItem(
                id="chk-1",
                task_text=f"Đọc kỹ tài liệu đặc tả và xác nhận lại yêu cầu cho task '{task_title}' với Leader/Mentor",
                category=ChecklistCategoryEnum.PREREQUISITE
            ),
            GuidanceItem(
                id="chk-2",
                task_text="Tuân thủ coding conventions của dự án, thiết lập TypeScript strict mode và format code sạch sẽ",
                category=ChecklistCategoryEnum.IMPLEMENTATION
            ),
            GuidanceItem(
                id="chk-3",
                task_text="Xử lý đầy đủ các nhánh điều kiện biên (edge cases) và kiểm tra tham số đầu vào chặt chẽ",
                category=ChecklistCategoryEnum.IMPLEMENTATION
            ),
            GuidanceItem(
                id="chk-4",
                task_text="Viết unit tests bao phủ các luồng nghiệp vụ chính và các trường hợp lỗi thường gặp",
                category=ChecklistCategoryEnum.TESTING
            ),
            GuidanceItem(
                id="chk-5",
                task_text="Tự thực hiện self-review toàn bộ thay đổi mã nguồn trước khi khởi tạo Pull Request",
                category=ChecklistCategoryEnum.TESTING
            ),
            GuidanceItem(
                id="chk-6",
                task_text="Kiểm tra an toàn bảo mật cơ bản: tuyệt đối không hardcode bí mật, validate dữ liệu đầu vào",
                category=ChecklistCategoryEnum.SECURITY
            ),
        ]
    elif level in ["JUNIOR", "MIDDLE"]:
        return [
            GuidanceItem(
                id="chk-1",
                task_text=f"Kiểm tra lược đồ dữ liệu và sự tương thích của API hiện hành đối với task '{task_title}'",
                category=ChecklistCategoryEnum.PREREQUISITE
            ),
            GuidanceItem(
                id="chk-2",
                task_text="Triển khai nghiệp vụ cốt lõi, xử lý toàn vẹn lỗi (Edge Cases) và phòng chống race condition",
                category=ChecklistCategoryEnum.IMPLEMENTATION
            ),
            GuidanceItem(
                id="chk-3",
                task_text="Tích hợp middleware xác thực, phân quyền RBAC và kiểm soát truy cập tài nguyên an toàn",
                category=ChecklistCategoryEnum.SECURITY
            ),
            GuidanceItem(
                id="chk-4",
                task_text="Viết kiểm thử tự động xác minh tính đúng đắn luồng nghiệp vụ và kiểm tra khả năng phục hồi",
                category=ChecklistCategoryEnum.TESTING
            ),
        ]
    else:  # SENIOR
        return [
            GuidanceItem(
                id="chk-1",
                task_text=f"Thẩm định thiết kế kiến trúc phân tán, độ mở rộng và tính toàn vẹn hệ thống cho '{task_title}'",
                category=ChecklistCategoryEnum.PREREQUISITE
            ),
            GuidanceItem(
                id="chk-2",
                task_text="Tối ưu hóa hiệu năng, giảm thiểu độ trễ I/O, tối ưu câu truy vấn cơ sở dữ liệu và đánh chỉ mục",
                category=ChecklistCategoryEnum.IMPLEMENTATION
            ),
            GuidanceItem(
                id="chk-3",
                task_text="Đánh giá an ninh bảo mật chuyên sâu, phân tích lỗ hổng, phòng thủ theo chiều sâu và thiết lập observability",
                category=ChecklistCategoryEnum.SECURITY
            ),
        ]

@openai_retry
async def _call_openai_guidance(task_title: str, task_description: str, user_level: UserLevelEnum) -> GuidanceData:
    client = get_async_client()
    level_str = user_level.value.upper()

    count_rule = ""
    if level_str in ["INTERN", "FRESHER"]:
        count_rule = "BẮT BUỘC trả về chính xác từ 5 đến 7 mục chi tiết (tập trung clean code, coding convention, viết test)."
    elif level_str in ["JUNIOR", "MIDDLE"]:
        count_rule = "BẮT BUỘC trả về chính xác từ 3 đến 5 mục (tập trung edge cases, validation, xử lý ngoại lệ toàn vẹn)."
    else:
        count_rule = "BẮT BUỘC trả về chính xác từ 2 đến 3 mục (tập trung kiến trúc cấp cao, benchmark hiệu năng, bảo mật chuyên sâu)."

    system_prompt = (
        "Bạn là Technical Leader và Chuyên gia Kiến trúc Phần mềm giàu kinh nghiệm.\n"
        "Nhiệm vụ của bạn là tạo danh sách các mục công việc kiểm tra (guidance checklist) phù hợp chính xác theo cấp bậc của lập trình viên.\n"
        f"Cấp bậc nhân sự: {level_str}.\n"
        f"Quy tắc số lượng mục: {count_rule}\n"
        "Mỗi mục phải có category thuộc một trong: PREREQUISITE, IMPLEMENTATION, TESTING, SECURITY.\n"
        "id định dạng: chk-1, chk-2, ..."
    )

    user_prompt = (
        f"Tiêu đề task: {task_title}\n"
        f"Mô tả task: {task_description or 'Không có mô tả chi tiết'}\n\n"
        f"Hãy sinh danh sách checklist tuân thủ nghiêm ngặt số lượng mục theo cấp bậc {level_str}."
    )

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=GuidanceData,
        temperature=0.2,
    )

    parsed: GuidanceData = completion.choices[0].message.parsed
    if not parsed or not parsed.items:
        raise ValueError("OpenAI không trả về danh sách items hợp lệ")

    # Kiểm tra lại số lượng items theo quy tắc cấp bậc, nếu OpenAI vi phạm số lượng thì điều chỉnh hoặc dùng fallback
    count = len(parsed.items)
    is_valid = False
    if level_str in ["INTERN", "FRESHER"] and 5 <= count <= 7:
        is_valid = True
    elif level_str in ["JUNIOR", "MIDDLE"] and 3 <= count <= 5:
        is_valid = True
    elif level_str == "SENIOR" and 2 <= count <= 3:
        is_valid = True

    if not is_valid:
        logger.warning(f"OpenAI trả về {count} items cho cấp {level_str}, không khớp ràng buộc. Sử dụng fallback an toàn.")
        return GuidanceData(items=_get_fallback_checklist(user_level, task_title))

    return parsed

async def generate_guidance(task_title: str, task_description: str, user_level: UserLevelEnum) -> GuidanceData:
    """Tạo checklist hướng dẫn thích ứng dựa trên cấp bậc nhân sự."""
    try:
        return await _call_openai_guidance(task_title, task_description, user_level)
    except Exception as exc:
        logger.warning(f"[Guidance Service Fallback]: Không thể gọi OpenAI ({exc}). Sử dụng fallback checklist chuẩn.")
        return GuidanceData(items=_get_fallback_checklist(user_level, task_title))

