# Smart Workspace AI Microservice (Python FastAPI)

Dịch vụ AI Microservice phụ trách toàn bộ tác vụ xử lý trí tuệ nhân tạo chuyên sâu cho nền tảng Smart Workspace. 

Dịch vụ là một Microservice độc lập hoàn toàn, nằm ngang hàng với `workspace-api` và **chỉ giao tiếp với Next.js Backend qua mạng (HTTP REST API)**.

---

## 1. Cấu trúc Hệ thống Độc Lập

```text
D:\Tot Nghiep\
├── workspace-api/            # Next.js 14 API Backend (Node.js, Port 3000)
│   ├── .env                  # Chứa AI_SERVICE_URL="http://localhost:8000"
│   └── src/lib/openai.ts     # Adapter Client HTTP gọi sang ai-service
└── ai-service/               # Python FastAPI AI Microservice (Port 8000)
    ├── .env                  # Chứa PORT=8000, OPENAI_API_KEY="..."
    ├── requirements.txt      # FastAPI, Uvicorn, Pydantic V2, OpenAI, Tenacity, Pytest
    ├── test_ai_service.py    # Test suite tự động (Pytest + HTTPX)
    └── app/
        ├── main.py           # Khởi tạo FastAPI, CORS (http://localhost:3000), Exception Handlers
        ├── core/config.py    # Pydantic Settings đọc biến môi trường
        ├── schemas/          # Pydantic V2 Schemas (Uniform Envelope Response)
        ├── services/         # Tầng gọi OpenAI SDK, Structured Outputs & Resilience Retry
        └── routers/          # Endpoints API (/api/v1/...) & /health
```

---

## 2. Hướng Dẫn Khởi Chạy 2 Service Độc Lập

Để hệ thống hoạt động đầy đủ, mở **2 cửa sổ Terminal riêng biệt**:

### Terminal 1: Khởi chạy Next.js Backend (`workspace-api`)
```powershell
# Chuyển vào thư mục workspace-api
cd "D:\Tot Nghiep\workspace-api"

# Đảm bảo file .env đã cấu hình: AI_SERVICE_URL="http://localhost:8000"
# Khởi chạy Next.js dev server tại port 3000
npm run dev
```
> Server Next.js sẽ lắng nghe tại: `http://localhost:3000`

---

### Terminal 2: Khởi chạy AI Microservice (`ai-service`)
```powershell
# Chuyển vào thư mục ai-service
cd "D:\Tot Nghiep\ai-service"

# Kích hoạt môi trường ảo Python trên PowerShell (lưu ý có .\ phía trước):
.\.venv\Scripts\Activate.ps1

# Khởi chạy FastAPI server tại port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
> **Mẹo:** Bạn cũng có thể chạy trực tiếp uvicorn từ venv mà không cần kích hoạt:
> ```powershell
> .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
> ```
> AI Microservice sẽ lắng nghe tại: `http://localhost:8000`  
> Swagger Documentation: `http://localhost:8000/docs`

---

## 3. Danh sách Endpoints & Chuẩn Hóa Phản Hồi

Mọi endpoint nghiệp vụ trả về định dạng bọc thống nhất (**Uniform Envelope Response**):
- **Thành công:**
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "..."
  }
  ```
- **Lỗi (422, 500...):**
  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR | INTERNAL_SERVER_ERROR | ...",
      "message": "..."
    }
  }
  ```

| STT | Phương thức | URL | Chức năng | Input Chính | Output Chính (`data`) |
|---|---|---|---|---|---|
| 1 | `GET` | `/health` | Kiểm tra trạng thái hoạt động | Không | `status: "ok"`, `service: "smart-workspace-ai-service"` |
| 2 | `POST` | `/api/v1/embeddings/batch` | Sinh vector embedding 1536 chiều | `texts: string[]` | `embeddings: float[][]` (1536 chiều) |
| 3 | `POST` | `/api/v1/guidance/generate` | Sinh checklist thích ứng theo cấp bậc | `task_title`, `task_description`, `user_level` | `items: [{ id, task_text, category }]` |
| 4 | `POST` | `/api/v1/pr/verify` | Thẩm định Git Diff Pull Request | `task_title`, `checklist`, `diff_summary` | `score`, `is_verified`, `feedback` |
| 5 | `POST` | `/api/v1/standup/generate` | Báo cáo Daily Standup tự động | `context: object` (activities, PRs, blockers) | `summaryYesterday`, `planToday`, `identifiedBlockers` |
| 6 | `POST` | `/api/v1/srs/extract` | Bóc tách User Stories chuẩn INVEST | `raw_content: string` | `stories: [{ storyId, role, action, ... }]` |

---

## 4. Kiểm Thử Tự Động

Chạy bộ kiểm thử tự động xác nhận toàn bộ schemas và endpoints:
```powershell
cd "D:\Tot Nghiep\ai-service"
.venv\Scripts\activate
pytest test_ai_service.py -v
```
