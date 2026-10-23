import json
import logging
from typing import Dict, Any
from app.services.openai_client import get_async_client, openai_retry
from app.schemas.standup import StandupData

logger = logging.getLogger("ai_service.standup")

def _get_fallback_standup(context: Dict[str, Any]) -> StandupData:
    acts = context.get("activities24h", []) or []
    prs = context.get("pullRequests", []) or []
    wip = context.get("wipPlan", []) or []
    blk = context.get("blockers", []) or []

    if acts or prs:
        yesterday = f"Đội ngũ đã chuyển đổi trạng thái {len(acts)} tác vụ và ghi nhận {len(prs)} Pull Requests trong 24 giờ qua."
    else:
        yesterday = "Đội ngũ tiếp tục duy trì và triển khai các tác vụ theo tiến độ danh định."

    if wip:
        critical_count = sum(1 for t in wip if isinstance(t, dict) and t.get("isCritical"))
        today = f"Tập trung giải quyết {len(wip)} tác vụ đang mở ({critical_count} tác vụ nằm trên đường găng critical path)."
    else:
        today = "Tập trung giải quyết các tác vụ trong kế hoạch sprint hiện tại."

    if blk:
        reasons = []
        for b in blk:
            if isinstance(b, dict):
                t_name = b.get("task", b.get("title", "Tác vụ"))
                t_reason = b.get("reason", "chưa rõ nguyên nhân")
                reasons.append(f'Tác vụ "{t_name}" bị nghẽn do {t_reason}')
        blockers_str = f"Phát hiện {len(blk)} điểm nghẽn: {'; '.join(reasons)}. Cần ưu tiên phối hợp tháo gỡ."
    else:
        blockers_str = "Không có điểm nghẽn nào được ghi nhận."

    return StandupData(
        summaryYesterday=yesterday,
        planToday=today,
        identifiedBlockers=blockers_str
    )

@openai_retry
async def _call_openai_standup(context: Dict[str, Any]) -> StandupData:
    client = get_async_client()

    project_name = context.get("projectName", "Dự án")
    context_str = json.dumps(context, ensure_ascii=False, indent=2)

    system_prompt = (
        "Bạn là Trợ lý AI Scrum Master chuyên nghiệp và giàu kinh nghiệm.\n"
        "Nhiệm vụ của bạn là tổng hợp bản báo cáo Daily Standup ngắn gọn, chuyên nghiệp, súc tích và có giá trị hành động cao "
        "dựa trên các sự kiện, hoạt động và số liệu thực tế trong 24 giờ qua của dự án.\n"
        "Báo cáo gồm 3 trường cốt lõi:\n"
        "1. summaryYesterday: Tóm tắt 2-3 câu các task đã hoàn thành/chuyển trạng thái hoặc các PRs đã tạo/merge hôm qua.\n"
        "2. planToday: Tóm tắt 2-3 câu trọng tâm công việc hôm nay, nhấn mạnh các task đường găng (critical path) nếu có.\n"
        "3. identifiedBlockers: Liệt kê chi tiết các điểm nghẽn, nguyên nhân hoặc ghi 'Không có điểm nghẽn nào được ghi nhận' nếu không có sự cố."
    )

    user_prompt = (
        f"Dữ liệu dự án: {project_name}\n"
        f"Ngữ cảnh hoạt động 24h qua:\n{context_str[:6000]}\n\n"
        "Hãy xuất bản báo cáo Daily Standup hoàn chỉnh."
    )

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=StandupData,
        temperature=0.2,
    )

    parsed: StandupData = completion.choices[0].message.parsed
    if not parsed:
        raise ValueError("OpenAI không trả về cấu trúc StandupData hợp lệ")
    return parsed

async def generate_standup(context: Dict[str, Any]) -> StandupData:
    """Tổng hợp báo cáo Daily Standup tự động từ ngữ cảnh 24h."""
    try:
        return await _call_openai_standup(context)
    except Exception as exc:
        logger.warning(f"[Standup Service Fallback]: Không thể gọi OpenAI ({exc}). Sử dụng fallback template.")
        return _get_fallback_standup(context)

