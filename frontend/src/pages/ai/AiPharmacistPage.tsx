import React from "react";
import { Bot, ShieldAlert, Sparkles } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";

export const AiPharmacistPage: React.FC = () => {
  const { families, activeFamilyId } = useFamilyStore();
  const activeFamily = families.find((family) => family.id === activeFamilyId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, maxWidth: 760 }}>
      <div>
        <h1 style={{ fontSize: "1.55rem", fontWeight: 700 }}>
          Trợ lý AI Dược sĩ Gia đình
        </h1>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Hỗ trợ tra cứu thông tin và lịch thuốc cho {activeFamily?.name || "gia đình"}.
        </p>
      </div>

      <div className="alert-banner alert-warning" style={{ marginBottom: 0 }}>
        <ShieldAlert size={20} style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong>Không thay thế chuyên gia y tế.</strong> Thông tin về thuốc cần
          được xác nhận với bác sĩ hoặc dược sĩ. Không dùng công cụ AI để chẩn
          đoán hay tự thay đổi liều dùng.
        </div>
      </div>

      <div className="card" style={{ padding: 24, display: "flex", gap: 16, alignItems: "flex-start" }}>
        <div style={{ width: 48, height: 48, borderRadius: 15, background: "var(--pm-primary-light, #e8f4f1)", color: "var(--pm-primary)", display: "grid", placeItems: "center", flexShrink: 0 }}>
          <Bot size={25} />
        </div>
        <div>
          <h2 style={{ margin: "2px 0 8px", fontSize: "1.1rem" }}>Trợ lý chưa được kết nối</h2>
          <p style={{ margin: 0, color: "var(--pm-text-secondary)", lineHeight: 1.6 }}>
            Dịch vụ AI phía máy chủ chưa được triển khai. Khung chat chỉ mở khi
            câu trả lời được tạo từ dịch vụ đã cấu hình và có kiểm soát an toàn;
            trang này hiện không đưa ra hướng dẫn dùng thuốc.
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginTop: 16, color: "var(--pm-text-secondary)", fontSize: ".85rem" }}>
            <Sparkles size={15} />
            <span>{activeFamily ? `Đang chọn ${activeFamily.name}` : "Chọn gia đình để chuẩn bị ngữ cảnh"}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
