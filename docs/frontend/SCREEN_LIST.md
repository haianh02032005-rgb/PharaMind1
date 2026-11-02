# PharmaMind AI — Screen List

| STT | Mã màn hình | Đường dẫn (Route) | Mô tả chức năng chính |
|---|---|---|---|
| 1 | `AUTH_LOGIN` | `/login` | Đăng nhập bằng Email & Mật khẩu, hỗ trợ tạo tài khoản demo nhanh |
| 2 | `AUTH_REGISTER` | `/register` | Đăng ký tài khoản người dùng mới |
| 3 | `HOME_DASHBOARD` | `/` | Tổng quan hôm nay: Liều tiếp theo, Lịch uống hôm nay, Trạng thái tủ thuốc, Cảnh báo, Thao tác nhanh |
| 4 | `FAMILY_MEMBERS` | `/family` | Quản lý thông tin hộ gia đình, danh sách thành viên, thêm thành viên mới, chọn thành viên xem hồ sơ |
| 5 | `MEMBER_DETAIL` | `/members/:memberId` | Hồ sơ chi tiết thành viên (5 tab: Tổng quan, Sức khỏe, Thuốc, Đơn thuốc, Lịch dùng) |
| 6 | `MEDICATIONS` | `/medications` | Kho thuốc gia đình, bộ lọc trạng thái, luồng thêm thuốc 3 bước, gán thành viên sử dụng |
| 7 | `PRESCRIPTIONS` | `/prescriptions` | Quản lý đơn thuốc gia đình, thêm thuốc vào đơn, kích hoạt / hoàn thành đơn |
| 8 | `SCHEDULES` | `/schedules` | Lịch uống thuốc theo dòng thời gian (Sáng / Trưa / Chiều / Tối), tạo lịch uống từ đơn thuốc |
| 9 | `SMART_CABINET` | `/cabinet` | Quản lý tủ thuốc thông minh: chuyển đổi mượt giữa **Chế độ đơn giản (2D 3×3)** và **Chế độ 3D (Digital Twin)**, gán thuốc vào ngăn, điều khiển Simulator |
| 10 | `DIGITAL_TWIN_3D` | `/digital-twin` | Màn hình chuyên biệt Digital Twin 3D tương tác toàn diện với tủ thuốc 9 ngăn thời gian thực |
| 11 | `AI_PHARMACIST` | `/ai` | Trợ lý AI Dược sĩ gia đình, câu hỏi gợi ý nhanh, tra cứu cách dùng thuốc & cảnh báo an toàn |
| 12 | `SETTINGS` | `/settings` | Cài đặt giao diện: Chế độ dễ đọc (Elderly Mode), Giảm chuyển động (Reduced Motion), Thông tin tài khoản |

