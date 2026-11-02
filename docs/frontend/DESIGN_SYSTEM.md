# PharmaMind AI — Design System

## 1. Triết lý thiết kế (Design Philosophy)

1. **Clarity over Complexity**: Thông tin quan trọng (liều tiếp theo, tên thuốc, người dùng, trạng thái ngăn tủ) hiển thị rõ trong vòng 3 giây.
2. **Trustworthy Healthcare Design**: Giao diện sáng, ấm, tạo cảm giác an tâm và chuyên nghiệp cho hộ gia đình Việt Nam.
3. **Human-Friendly for All Ages**: Tối ưu cho cả người trẻ quản lý gia đình lẫn người lớn tuổi (Chế độ dễ đọc / Elderly Mode).
4. **Actionable Information**: Mỗi màn hình đều gắn liền với hành động rõ ràng (Mở ngăn, Xác nhận đã uống, Xem chi tiết).
5. **Non-Diagnostic by Design**: Mọi cảnh báo dị ứng, phản ứng thuốc hay gợi ý AI đều là hỗ trợ thông tin, không thay thế chỉ định y khoa.

---

## 2. Hệ màu (Color System)

| Token | Hex | Ý nghĩa sử dụng |
|---|---|---|
| `--pm-primary` | `#2E9C95` | Màu chủ đạo (Nút chính, ngăn đang chọn, trạng thái kết nối) |
| `--pm-primary-light` | `#DDF4F1` | Nền badge, highlight nhẹ, trạng thái hover |
| `--pm-secondary` | `#6BC5B8` | Điểm nhấn phụ, biểu đồ, icon y tế |
| `--pm-bg` | `#F7FAFA` | Nền trang chính |
| `--pm-surface` | `#FFFFFF` | Nền Card, Drawer, Modal, Sidebar |
| `--pm-text-primary` | `#17343A` | Chữ tiêu đề và nội dung chính |
| `--pm-text-secondary` | `#5B7C83` | Chữ phụ, nhãn trường, mô tả |
| `--pm-border` | `#DCECEC` | Viền thẻ và đường phân cách |
| `--pm-success` | `#2FA66A` | Đã uống, Tủ ONLINE, Thuốc bình thường |
| `--pm-warning` | `#E6A83A` | Sắp đến giờ uống, Sắp hết thuốc (`LOW_STOCK`), Sắp hết hạn (`EXPIRING`), Cảnh báo dị ứng |
| `--pm-danger` | `#D9534F` | Quá hạn (`EXPIRED`), Hết thuốc (`DEPLETED`), Bỏ lỡ liều |
| `--pm-offline` | `#8FA3A8` | Tủ OFFLINE, Ngăn trống (`EMPTY`), Đã lưu trữ |

---

## 3. Typography & Elderly Mode

- **Font chính**: `Inter`, `Be Vietnam Pro`, `Plus Jakarta Sans`, `system-ui`, `sans-serif`.
- **Kích thước chuẩn**:
  - `Page Title`: `24px–28px`, `font-weight: 700`
  - `Section Title`: `18px–20px`, `font-weight: 600`
  - `Card Title`: `16px–18px`, `font-weight: 600`
  - `Body`: `15px–16px`, `font-weight: 400`
  - `Caption / Badge`: `12px–13px`, `font-weight: 500`
- **Chế độ dễ đọc (Elderly Mode)**:
  - Tăng kích thước chữ cơ sở lên `+20%` (`18px–20px`).
  - Nút bấm tối thiểu cao `48px–54px`.
  - Tăng độ tương phản viền và khoảng cách giữa các phần tử.
  - Ưu tiên hiển thị **Chế độ đơn giản (Simple Mode 3×3)** cho tủ thuốc thông minh.

---

## 4. Spacing, Border Radius & Elevation

- **Spacing Scale**: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`.
- **Border Radius**:
  - Card / Panel: `16px–20px`
  - Button / Input: `12px`
  - Status Pill / Badge: `9999px`
- **Shadow**:
  - Card chuẩn: `0 4px 16px rgba(23, 52, 58, 0.05)`
  - Card nổi bật / Active: `0 8px 24px rgba(46, 156, 149, 0.14)`

