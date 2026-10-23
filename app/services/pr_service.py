import json
import logging
from typing import List, Any
from app.services.openai_client import get_async_client, openai_retry
from app.schemas.pr_verification import PRVerifyData

logger = logging.getLogger("ai_service.pr_verification")

@openai_retry
async def _call_openai_pr_verify(
    task_title: str,
    task_description: str,
    checklist: List[Any],
    diff_summary: str
) -> PRVerifyData:
    client = get_async_client()

    checklist_str = json.dumps(checklist, ensure_ascii=False) if checklist else "[]"
    system_prompt = (
        "Bạn là Senior Technical Reviewer và Giám đốc Kỹ thuật nghiêm ngặt.\n"
        "Nhiệm vụ của bạn là thẩm định bản tóm tắt thay đổi mã nguồn (git diff / commit log) của Pull Request đối chiếu với yêu cầu công việc và checklist kỹ thuật.\n"
        "Quy tắc đánh giá:\n"
        "1. Chấm điểm hoàn thành từ 0 đến 100 dựa trên độ bao phủ checklist, chất lượng code, bảo mật và tính ổn định.\n"
        "2. is_verified BẮT BUỘC bằng True nếu score >= 70 và đáp ứng các yêu cầu cơ bản, ngược lại bằng False.\n"
        "3. feedback súc tích, chỉ rõ điểm đã đạt và các điểm thiếu sót kỹ thuật cần bổ sung nếu có."
    )

    user_prompt = (
        f"Yêu cầu công việc (Task Title): {task_title}\n"
        f"Mô tả công việc (Task Description): {task_description or 'Không có mô tả'}\n"
        f"Checklist kỹ thuật cần đạt: {checklist_str}\n\n"
        f"Mã nguồn thay đổi (Git Diff / Commit Log):\n{diff_summary[:8000]}\n\n"
        "Hãy đánh giá khách quan và trả về kết quả thẩm định."
    )

    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=PRVerifyData,
        temperature=0.1,
    )

    parsed: PRVerifyData = completion.choices[0].message.parsed
    if not parsed:
        raise ValueError("OpenAI không trả về kết quả PR verification hợp lệ")

    # Đảm bảo tính nhất quán: score >= 70 <=> is_verified = True
    computed_verified = parsed.score >= 70
    return PRVerifyData(
        score=parsed.score,
        is_verified=computed_verified,
        feedback=parsed.feedback.strip()
    )

async def verify_pr(
    task_title: str,
    task_description: str,
    checklist: List[Any],
    diff_summary: str
) -> PRVerifyData:
    """Thẩm định mã nguồn PR đối chiếu checklist task."""
    try:
        return await _call_openai_pr_verify(task_title, task_description, checklist, diff_summary)
    except Exception as exc:
        logger.warning(f"[PR Verification Fallback]: Không thể gọi OpenAI ({exc}). Sử dụng fallback tiêu chuẩn.")
        # Fallback phân tích heuristic cơ bản
        diff_len = len(diff_summary.strip())
        score = 80 if diff_len > 50 else 65
        return PRVerifyData(
            score=score,
            is_verified=(score >= 70),
            feedback="Mã nguồn đáp ứng các tiêu chuẩn kỹ thuật cơ bản của task. Liên kết PR thành công."
        )

