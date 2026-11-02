import React, { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { FileUp } from "lucide-react";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { WIZARD_STEPS } from "../../features/importPrescription/types";
import { MemberStep } from "./MemberStep";
import { UploadStep } from "./UploadStep";
import { ReviewStep } from "./ReviewStep";
import { ScheduleStep } from "./ScheduleStep";
import { HealthUpdateStep } from "./HealthUpdateStep";
import { ConfirmStep } from "./ConfirmStep";

export const ImportPrescriptionPage: React.FC = () => {
  const w = useImportWizard();
  const [params] = useSearchParams();

  // Allow deep-linking from MemberDetailPage: /import-prescription?memberId=12
  useEffect(() => {
    const mid = params.get("memberId");
    if (mid && !w.session) {
      w.setMemberId(Number(mid));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const step = w.step;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div>
        <h1 style={{ fontSize: "1.55rem", fontWeight: 700, display: "flex", gap: 10, alignItems: "center" }}>
          <FileUp size={24} style={{ color: "var(--pm-primary)" }} />
          Nhập đơn thuốc từ ảnh / Excel
        </h1>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Tải lên → Rà soát → Xác nhận. Không dữ liệu nào được ghi vào hồ sơ trước khi bạn xác nhận.
        </p>
      </div>

      <div className="tabs-bar" style={{ flexWrap: "wrap" }}>
        {WIZARD_STEPS.map((s) => (
          <button
            key={s.key}
            type="button"
            className={`tab-btn ${step === s.key ? "active" : ""}`}
            disabled={s.key > step || (s.key >= 2 && !w.session) || w.session?.status === "COMMITTED"}
            onClick={() => w.setStep(s.key)}
          >
            {s.key + 1}. {s.label}
          </button>
        ))}
      </div>

      {w.error && (
        <div className="alert-banner alert-danger" role="alert">
          {w.error}
        </div>
      )}

      {step === 0 && <MemberStep />}
      {step === 1 && <UploadStep />}
      {step === 2 && <ReviewStep />}
      {step === 3 && <ScheduleStep />}
      {step === 4 && <HealthUpdateStep />}
      {step === 5 && <ConfirmStep />}
    </div>
  );
};

export default ImportPrescriptionPage;

