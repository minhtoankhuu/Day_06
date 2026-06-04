# Hướng Dẫn Đồng Hành Dự Án (Team Onboarding Guide)
## Dự Án: ShopeeFood AI Personalized Suggestions

Chào mừng cả team đến với dự án **ShopeeFood AI Personalized Suggestions**. Tài liệu này hướng dẫn chi tiết cách thức hoạt động của bản mẫu (Prototype), cấu trúc mã nguồn trong thư mục, và các nhiệm vụ cụ thể để các thành viên có thể theo dõi và thực hiện.

---

## 🎯 1. Mục Tiêu Dự Án (Project Goal)

Khắc phục điểm đau **quá tải lựa chọn (Discovery Overload)** và **gợi ý món ăn thiếu cá nhân hóa** của ShopeeFood bằng cách tích hợp lớp trí tuệ nhân tạo (AI Engine) trực tiếp lên trang chủ và khung chat tìm món. Bản nâng cấp mới của chúng ta bao gồm:
1. **Trải nghiệm trang chủ cải tiến (Dual Banners):** Hiển thị song song cả **Banner Quảng cáo Deal Hot** (Campaign Banner) và **Banner Trợ lý AI Tìm Món** (AI Banner) để tăng tỷ lệ nhấp chuột (CTR) và chuyển đổi.
2. **Ảnh quảng cáo sinh động bằng AI:** Banner quảng cáo cho quán **Mì Trộn Hàng Xanh** được tạo sinh động, chân thực bằng AI (lưu tại `shopee3.jpg`), hỗ trợ click mở trực tiếp trang chi tiết món ăn **Mì Trộn Xá Xíu Trứng Lòng Đào** (`food_003`).
3. **Cá nhân hóa linh vật trợ lý (Custom Robot Avatar):** Thay thế toàn bộ biểu tượng cảm xúc robot mặc định (`🤖`) thành biểu tượng robot cam đặc trưng của ShopeeFood (`iconaichat.jpg`) ở tất cả các vị trí: nút chat nổi, tiêu đề khung chat, các bong bóng chat AI và hiệu ứng đang soạn tin nhắn.
4. **Hệ thống Taskbar hoàn chỉnh (5-Tab Bottom Nav):** Bổ sung thêm hai tab **Yêu thích** ❤️ và **Thông báo** 🔔 tạo thành hệ thống 5 tab chuyên nghiệp như ứng dụng thật.

---

## 📁 2. Cấu Trúc Thư Mục & Tài Liệu Dự Án

Thư mục dự án `/shopee_food` chứa các thành phần sau:

```text
├── README.md                       # Giới thiệu tổng quan và hướng dẫn khởi chạy dự án
├── ai_chat_system_prompt.md        # System prompt chuẩn cho mô hình LLM chatbox
├── ai_chat_mock_data.json          # Mock data lớn: restaurants, menu, users
├── evidence_pack.md                # Bằng chứng pain point và nghiên cứu đối thủ
├── thin_spec.md                    # Đặc tả tính năng rút gọn & kịch bản kiểm thử
├── team_onboarding_guide.md        # Tài liệu hướng dẫn này dành cho team (đã cập nhật)
├── prototype/                      # Thư mục mã nguồn bản mẫu cũ (chạy tĩnh)
└── app/                            # Thư mục ứng dụng di động chính thức (FastAPI + SPA)
    ├── backend/                    # Server FastAPI cung cấp API đề xuất và chat
    └── frontend/                   # Giao diện web app chính (HTML/CSS/JS)
        ├── index.html              # Màn hình SPA tích hợp 2 banner và 5 tab bottom nav
        ├── js/                     # Xử lý logic route, click banner, chatbox và Toast
        └── ảnh/                    # Chứa các ảnh icon và banner (iconaichat.jpg, shopee3.jpg)
```

---

## ⚙️ 3. Quy Trình Tích Hợp Hệ Thống (Workflow 5 Giai Đoạn)

Bản mẫu của chúng ta mô phỏng chân thực hệ thống backend của ShopeeFood qua sơ đồ tương tác góc phải màn hình:

1. **Giai đoạn 1: Feature Store**: Đồng bộ hóa dữ liệu hành vi thực tế (địa điểm GPS trường học/công sở, giá trị giỏ hàng trung bình AOV, lịch sử tìm kiếm, thói quen ăn uống).
2. **Giai đoạn 2: AI Classifier**: Phân loại đối tượng (Học sinh, Sinh viên, Nhân viên văn phòng) và xác định ngữ cảnh thời gian trong ngày.
3. **Giai đoạn 3: Taste & Budget Matcher**: Thuật toán đề xuất món ăn tối ưu, lọc món theo khẩu vị cá nhân và túi tiền phù hợp với từng phân khúc người dùng.
4. **Giai đoạn 4: GenAI Copywriter**: Tùy biến tiêu đề banner và nội dung trò chuyện của chatbot theo Tone of Voice của nhóm tuổi.
5. **Giai đoạn 5: UI Dispatcher & Feedback Loop**: Hiển thị trên app và thu thập tỷ lệ chuyển đổi khi người dùng click xem quán/chốt đơn để huấn luyện ngược lại mô hình.

---

## 🤝 4. Phân Chia Nhiệm Vụ Thành Viên (Owner Plan)

Để chuẩn bị cho buổi báo cáo và chấm điểm, các thành viên trong nhóm cần phối hợp theo phân vai dưới đây:

### 🎒 Research Owner
* **Nhiệm vụ:**
  * Kiểm tra lại tệp [evidence_pack.md](file:///Users/Student/Downloads/shopee_food/evidence_pack.md).
  * Chuẩn bị thêm các tệp ảnh screenshot lỗi từ ShopeeFood thật để chứng minh pain point của người dùng hiện nay.

### 📝 SPEC Owner
* **Nhiệm vụ:**
  * Đọc kỹ [thin_spec.md](file:///Users/Student/Downloads/shopee_food/thin_spec.md) để nắm chắc lý do lựa chọn giải pháp **Augmentation** thay vì tự động hóa hoàn toàn.
  * Giải trình về luồng lọc cứng (Cay/Không cay, Ngân sách, Dị ứng) trước khi đưa dữ liệu cho AI.

### 🖥️ Prototype Owner
* **Nhiệm vụ:**
  * Quản lý mã nguồn trong thư mục `/app/`.
  * Hướng dẫn nhóm cách chạy FastAPI server (`uvicorn main:app --reload`) và mở địa chỉ `http://127.0.0.1:8000/`.
  * Hướng dẫn sửa đổi catalog món ăn trong `app/backend/data/mock_db.json`.

### 🧪 Test & Failure Owner
* **Nhiệm vụ:**
  * Kiểm thử các failure mode, đặc biệt là việc ngăn ngừa gợi ý nhầm món gây dị ứng bằng cách quét bộ lọc thành phần cứng trên backend.
  * Xác minh hoạt động của các nút trên giao diện 5 tab và 2 banner.

### 🎤 Demo & Presentation Owner
* **Nhiệm vụ:**
  * Soạn kịch bản nói và chuẩn bị slide thuyết trình dài 3-5 phút dựa trên kịch bản demo bên dưới.
  * Phối hợp thao tác trên màn hình điện thoại mượt mà khớp với bài thuyết trình.

---

## 🎬 5. Kịch Bản Demo Trình Diễn (Demo Script)

Khi demo trước hội đồng, hãy thực hiện theo đúng các bước sau để đảm bảo ghi điểm tối đa:

1. **Bước 1: Trình diễn giao diện trang chủ nâng cấp (Dual Banners & 5-Tab Nav)**
   * Mở trình duyệt truy cập `http://127.0.0.1:8000/`.
   * Thuyết trình: *"Ứng dụng ShopeeFood của chúng em đã tối ưu trang chủ bằng việc hiển thị song song hai banner. Banner phía trên là **Quảng cáo Deal Hot** thúc đẩy chuyển đổi, và banner phía dưới là **Trợ lý AI Tìm Món** giúp giảm tải lựa chọn. Đồng thời, thanh Taskbar phía dưới đã được hoàn thiện đủ 5 tab tiêu chuẩn."*
2. **Bước 2: Trình diễn click chuyển tiếp quảng cáo quán ăn (Campaign Redirect)**
   * Nhấn vào **Banner Quảng cáo Deal Hot (Mì Trộn Hàng Xanh)**. Giao diện sẽ trượt mượt mà sang màn hình chi tiết món ăn **Mì Trộn Xá Xíu Trứng Lòng Đào** (`food_003`).
   * Thuyết trình: *"Khi người dùng hứng thú với Deal Hot 6.6 trên ảnh banner quảng cáo (được gen tự động bằng AI), họ chỉ cần click là có thể xem ngay chi tiết món ăn để tiến hành đặt giao ngay, rút ngắn tối đa hành trình mua sắm."*
   * Nhấn nút **◀** ở góc trên để quay lại trang chủ.
3. **Bước 3: Trình diễn các tab điều hướng phụ (Bottom Nav Toast)**
   * Nhấn chọn lần lượt tab **Yêu thích** ❤️ và **Thông báo** 🔔 trên thanh Bottom Nav. Quan sát các thông báo Toast nhẹ nhàng xuất hiện trên màn hình báo hiệu tính năng đang được phát triển.
4. **Bước 4: Trình diễn Trợ lý AI Tìm Món cá nhân hóa (Active AI Chat & Custom Avatar)**
   * Nhấn nút **AI Tìm Món** trên banner hoặc nhấn nút chat nổi ở góc phải bên dưới màn hình.
   * Thuyết trình: *"Màn hình trò chuyện AI mở ra. Toàn bộ icon robot mặc định đã được thay thế bằng hình ảnh Mascot Robot Cam độc quyền (`iconaichat.jpg`) của ShopeeFood ở cả tiêu đề, bong bóng chat và lúc đang soạn tin nhắn."*
   * Bấm chọn nhóm hồ sơ (ví dụ: **Sinh viên**). Trò chuyện với AI bằng cách chọn một chip gợi ý (ví dụ: *Mì trộn xá xíu* hoặc *Trà chanh tắc*).
   * Quan sát câu trả lời sinh động từ AI với đại diện avatar tùy chỉnh, hiển thị thông tin món ăn kèm nút **"Ghé Quán"**. Click **"Ghé Quán"** để xem trang chi tiết.
5. **Bước 5: Kết thúc demo**
   * Nhấn nút **Quay lại** và nhấn nút **Trang Chủ** để kết thúc kịch bản trình diễn.

---

## 📋 6. Kế Hoạch Sprint Tiếp Theo (Next Sprint Task List)
Dưới đây là bảng phân chia công việc chi tiết dành cho các thành viên trong nhóm để phát triển hoàn thiện ứng dụng có giao diện và trải nghiệm (UI/UX) hoàn chỉnh trên thực tế:

### 🎨 UI/UX Designer
* [ ] **Figma Design System**: Thiết kế bộ thư viện màu sắc động phù hợp với 3 nhóm khách hàng.
* [ ] **High-Fidelity UI Mockups**: Thiết kế chi tiết tất cả các màn hình của app di động (Home, Chatbot AI Assistant, Menu quán ăn, Giỏ hàng, Đơn đặt hàng).
* [ ] **Micro-animations & Mascot**: Thiết kế các hiệu ứng động của linh vật trợ lý AI ở góc màn hình và khi đang tải gợi ý món ăn.
* [ ] **Allergy Warning UI**: Thiết kế giao diện cảnh báo độ cay và thành phần gây dị ứng nổi bật trước khi chuyển tiếp vào trang thực đơn quán ăn.

### 💻 Frontend Developer
* [ ] **Framework Setup**: Khởi tạo dự án ứng dụng di động thực tế bằng React Native hoặc Flutter.
* [ ] **Dynamic Theme Engine**: Hiện thực hóa việc thay đổi giao diện tự động theo phân khúc người dùng nhận diện bởi AI.
* [ ] **AI Assistant Interface**: Lập trình giao diện chatbot tìm món ăn với hiệu ứng bong bóng trò chuyện và thẻ món ăn đề xuất liên kết trực tiếp sang trang quán.

### ⚙️ Backend & AI Engineer
* [ ] **Feature Store Database**: Xây dựng cơ sở dữ liệu (PostgreSQL/MongoDB + Redis) để lưu trữ hồ sơ người dùng, thói quen ăn uống, và lịch sử vị trí đặt đơn.
* [ ] **AI Classifier Service**: Triển khai API phân loại nhóm người dùng (Học sinh/Sinh viên/Văn phòng) chạy trên backend thời gian thực.
* [ ] **Personalized Recommendation Engine**: Xây dựng thuật toán lọc cộng tác (Collaborative Filtering) kết hợp với các bộ lọc cứng về ngân sách và khẩu vị cá nhân.
* [ ] **GenAI LLM Integration**: Tích hợp API Gemini Flash để tự động biên soạn tiêu đề banner động và phản hồi chatbot theo Tone of Voice phù hợp.
* [ ] **CTR & Feedback Pipeline**: Thiết lập pipeline thu thập phản hồi click-through rate (CTR) để gửi ngược về hệ thống huấn luyện trực tuyến (Online Learning).

### 🧪 QA/Tester
* [ ] **Functional & Integration Testing**: Thực hiện viết và chạy các bộ test case kiểm thử chức năng chatbot, gợi ý món ăn, và chuyển hướng liên kết quán.
* [ ] **Fail-safe Path Verification**: Kiểm thử Failure Mode xem hệ thống có đưa ra cảnh báo chính xác khi dữ liệu khẩu vị/dị ứng của người dùng không chắc chắn.
