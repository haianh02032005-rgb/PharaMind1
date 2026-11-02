import React from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { RevealWarningItem } from "../../features/cabinet/reveal/types";

interface DrawerWarningBadgeProps {
  warnings: RevealWarningItem[];
}

export const DrawerWarningBadge: React.FC<DrawerWarningBadgeProps> = ({
  warnings,
}) => {
  if (!warnings || warnings.length === 0) {
    return (
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 14px",
          borderRadius: 12,
          background: "var(--pm-success-bg)",
          color: "var(--pm-success)",
          fontWeight: 600,
          fontSize: "0.9rem",
        }}
      >
        <CheckCircle2 size={17} />
        <span>Không có cảnh báo</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {warnings.map((w, idx) => {
        const isHighRisk =
          w.type === "ALLERGY_WARNING" ||
          w.type === "DRUG_REACTION_WARNING" ||
          w.type === "EXPIRED_WARNING" ||
          w.type === "DEPLETED_WARNING";

        return (
          <div
            key={`${w.type}-${idx}`}
            className={`alert-banner ${
              isHighRisk ? "alert-danger" : "alert-warning"
            }`}
            style={{
              marginBottom: 0,
              padding: "12px 14px",
              borderRadius: 12,
              lineHeight: 1.45,
            }}
          >
            <AlertTriangle
              size={18}
              style={{ flexShrink: 0, marginTop: 2 }}
            />
            <div>
              <div style={{ fontWeight: 700, marginBottom: 2 }}>
                {w.type === "ALLERGY_WARNING" ||
                w.type === "DRUG_REACTION_WARNING"
                  ? "Lưu ý kiểm tra dị ứng / phản ứng thuốc"
                  : "Lưu ý tình trạng thuốc"}
              </div>
              <div>{w.message}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

