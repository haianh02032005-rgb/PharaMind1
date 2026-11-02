# PharmaMind AI — Component Guide

## 1. Layout & Navigation Components
- **`AppShell`** (`src/components/navigation/AppShell.tsx`):
  - Desktop (`>= 1024px`): Left Sidebar cố định + Top Header (chọn Gia đình, bật/tắt Chế độ dễ đọc, trạng thái tủ thuốc) + Main Content.
  - Mobile (`< 1024px`): Top Bar gọn + Bottom Navigation 5 mục chính (`Trang chủ`, `Thuốc`, `Lịch uống`, `Tủ thuốc`, `Gia đình`).

## 2. Digital Twin 3D Components (`src/pages/digital-twin/`)
- **`DigitalTwinPage.tsx`**: Container kết nối dữ liệu từ REST API + WebSocket realtime và quản lý bộ lọc thành viên.
- **`DigitalTwinLayout.tsx`**: Bố cục 2 cột trên Desktop (Trái: 3D Viewer + Toolbar, Phải: InfoPanel) và xếp dọc trên Mobile.
- **`CabinetCanvas.tsx`**: Môi trường 3D Canvas (ánh sáng studio mềm, điều khiển xoay/zoom chuột & cảm ứng, nút Đặt lại góc nhìn).
- **`CabinetModel.tsx`**: Tải mô hình `.glb` (`pharmamind_cabinet.glb`) chứa `cabinet_body`, `top_screen`, `handle`, `drawer_01`..`drawer_09` kèm cơ chế fallback an toàn nếu lỗi tải file.
- **`CompartmentMesh.tsx`**: Thành phần ngăn kéo 3D tương tác:
  - Hỗ trợ hover, click chọn ngăn, hiệu ứng pulse cho ngăn có liều tiếp theo.
  - Animation trượt mở/đóng mượt theo trục Z (`isOpen`).
  - Hiển thị mô hình thuốc 3D bên trong ngăn theo `dosage_form` (`TABLET`, `CAPSULE`, `SYRUP`, `SACHET`, `OTHER`).
- **`InfoPanel.tsx`**: Hiển thị chi tiết ngăn đang chọn: tên thuốc, số lượng, hạn dùng, danh sách thành viên & lịch uống, cảnh báo dị ứng / phản ứng thuốc, và nút Mở / Đóng ngăn.
- **`StatusBar.tsx`**: Hiển thị trạng thái kết nối tủ (`ONLINE` / `OFFLINE`), chế độ phần cứng (`SIMULATOR`), trạng thái WebSocket và thời điểm đồng bộ gần nhất.

