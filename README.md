# ShopeeFood AI Personalized Suggestions

## 1. Mô Tả Đề Tài

**ShopeeFood AI Personalized Suggestions** là bản mẫu tích hợp AI Copilot vào ShopeeFood để giảm tình trạng quá tải lựa chọn khi người dùng mở app tìm món.

Hệ thống tập trung vào một flow chính và các tính năng nâng cấp nổi bật:

```text
Người dùng mở trang chủ ShopeeFood
→ Trang chủ hiển thị song song 2 banner:
   1. Banner Quảng cáo Deal Hot (Campaign Banner): Hiển thị ảnh ad gen bằng AI của quán "Mì Trộn Hàng Xanh" (shopee3.jpg)
   2. Banner Trợ lý AI Tìm Món (AI Banner): Đã cập nhật icon tuỳ chỉnh (iconaichat.jpg)
→ Người dùng có 2 hướng tương tác chính:
   - Hướng A: Click vào Banner Quảng cáo → Mở thẳng trang chi tiết món "Mì Trộn Xá Xíu Trứng Lòng Đào" [food_003] cực kỳ tiện lợi.
   - Hướng B: Click vào Banner AI hoặc Floating Button hoặc ô Tìm kiếm → Mở khung Chatbox AI cá nhân hóa.
→ Chatbox AI trò chuyện bằng avatar robot mới (iconaichat.jpg) và đề xuất món dựa trên ngân sách, khẩu vị và dị ứng của user.
→ Hệ thống Taskbar (Bottom Nav) mở rộng lên 5 tab chuẩn ShopeeFood: Trang chủ 🏠, Yêu thích ❤️, Đơn hàng 📋, Thông báo 🔔, Tôi 👤.
```

AI hiện hỗ trợ gợi ý dựa trên ngân sách nhóm (khẩu vị/sở thích tự chọn theo yêu cầu của user):

- **Học sinh:** ngân sách món dưới 30.000đ.
- **Sinh viên:** ngân sách món từ 30.000đ - 50.000đ.
- **Nhân viên văn phòng:** ngân sách món lên tới 150.000đ.

Quyết định sản phẩm là **Augmentation**: AI chỉ hỗ trợ thu hẹp lựa chọn và giải thích lý do gợi ý; người dùng vẫn là người quyết định cuối cùng.

---

## 2. Cấu Trúc Thư Mục

```text
.
├── README.md                       # Tài liệu giới thiệu tổng quan dự án (đã cập nhật)
├── ai_chat_system_prompt.md        # System prompt cho LLM ShopeeFood AI Copilot
├── ai_chat_mock_data.json          # Mock data lớn: users, banners, push notifications, restaurants/menu
├── evidence_pack.md                # Bằng chứng pain point và insight
├── thin_spec.md                    # Thin spec, build slice, failure mode
├── shopeefood_group_project.md     # Tài liệu phân tích project tổng quan
├── team_onboarding_guide.md        # Hướng dẫn onboarding nhóm và kịch bản demo (đã cập nhật)
├── prototype/                      # Bản prototype visual cũ, chạy tĩnh bằng HTML/CSS/JS
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── mascot.jpg
└── app/
    ├── backend/
    │   ├── main.py                 # FastAPI app, serve API và frontend static
    │   ├── requirements.txt
    │   ├── .env.example            # Mẫu cấu hình Gemini API key
    │   ├── data/
    │   │   └── mock_db.json         # Mock DB nhỏ đang dùng cho các persona
    │   ├── routes/
    │   │   ├── chat.py              # API chat, adapter mock data lớn
    │   │   ├── foods.py             # API catalog món ăn
    │   │   └── users.py             # API persona người dùng
    │   └── services/
    │       └── gemini_service.py    # Gemini integration + fallback recommender
    └── frontend/
        ├── index.html              # Mobile web app chính (giao diện 2 banner, 5 tab bottom nav)
        ├── css/
        │   └── style.css           # CSS giao diện cao cấp, reset ảnh icon AI, campaign banner
        ├── js/
        │   ├── api.js              # API client kết nối backend
        │   ├── app.js              # SPA router, xử lý click banner, toast cảnh báo, 5 tab bottom nav
        │   └── chat.js             # Chatbox AI UI sử dụng iconaichat.jpg vẽ tin nhắn và hiệu ứng gõ chữ
        └── ảnh/                    # Thư mục chứa ảnh và icon tuỳ chỉnh (bao gồm shopee3.jpg và iconaichat.jpg)
```

---

## 3. Workflow Hệ Thống

### 3.1. Frontend Flow

```text
Onboarding chọn persona
→ Home ShopeeFood
   ├─► Click Campaign Banner ➔ Hiển thị ngay chi tiết món Mì Trộn Hàng Xanh [food_003]
   └─► Click AI Banner / Search / Float Button ➔ Mở Chatbox cá nhân hóa dùng iconaichat.jpg
→ Chatbox tương tác:
   ├─► User nhập tự nhiên hoặc click suggestion chip
   ├─► Gọi POST /api/chat
   └─► Render tin nhắn phản hồi của AI cùng ảnh avatar robot (iconaichat.jpg)
→ Nhấp chọn tab dưới Taskbar:
   ├─► Trang chủ 🏠 ➔ Về màn hình chính
   ├─► Yêu thích ❤️ ➔ Toast "Tính năng Yêu thích đang phát triển!"
   ├─► Đơn hàng 📋 ➔ Toast "Tính năng Đơn hàng đang phát triển!"
   ├─► Thông báo 🔔 ➔ Toast "Tính năng Thông báo đang phát triển!"
   └─► Tôi 👤 ➔ Hiển thị thông báo nhanh thông tin Hồ sơ cá nhân
```

### 3.2. Backend Flow

```text
POST /api/chat
→ Load persona từ app/backend/data/mock_db.json
→ Load mock data lớn từ ai_chat_mock_data.json
→ Flatten restaurants[].menu[] thành food_catalog
→ Ghép profile persona hiện tại với một user mẫu trong mock data lớn
→ Nếu có GEMINI_API_KEY:
     gọi Gemini với ai_chat_system_prompt.md + user profile + food catalog + full mock data
   Nếu không có GEMINI_API_KEY:
     dùng fallback recommender rule-based
→ Extract food/item ids từ response LLM
→ Map ids thành suggested_foods cho frontend render card
```

### 3.3. Safety Rules

Backend đang xử lý các ràng buộc quan trọng:

- Không gợi ý món vượt ngân sách persona.
- Nếu user yêu cầu **không cay**, loại bỏ các món cay.
- Nếu user/profile có dị ứng (**đậu phộng, sữa, trứng, hải sản, đậu nành**), loại bỏ các món có thành phần trùng dị ứng.
- Chỉ hiển thị blockquote cảnh báo dị ứng khi món ăn thực tế được gợi ý có chứa thành phần dị ứng của người dùng.

---

## 4. Cách Chạy FE/BE

### 4.1. Chạy backend và phục vụ frontend

Backend FastAPI đồng thời phục vụ frontend tại route `/`, nên chỉ cần chạy một server:

```bash
cd app/backend
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Mở ứng dụng:

```text
http://127.0.0.1:8000/
```

Tài liệu API:

```text
http://127.0.0.1:8000/docs
```

### 4.2. Bật Gemini LLM thật

Copy file env mẫu:

```bash
cd app/backend
cp .env.example .env
```

Điền API key vào `app/backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Khi cấu hình `GEMINI_API_KEY`, API sẽ gọi Gemini thật. Nếu không có key, ứng dụng tự động chạy bằng thuật toán Fallback Recommender để đảm bảo tính sẵn sàng cao.
