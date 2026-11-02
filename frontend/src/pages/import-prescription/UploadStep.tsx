import React, { useRef, useState } from "react";
import { Download, FileSpreadsheet, FileImage, UploadCloud } from "lucide-react";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { downloadExcelTemplate } from "../../features/importPrescription/api";
import { inferSourceType, validateImportFile } from "../../features/importPrescription/validation";
import { useFamilyStore } from "../../store/familyStore";

export const UploadStep: React.FC = () => {
  const w = useImportWizard();
  const members = useFamilyStore((s) => s.members);
  const memberName = members.find((m) => m.id === w.memberId)?.full_name;
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pick = (f: File | null) => {
    if (!f) return;
    const err = validateImportFile(f);
    setLocalError(err);
    setFile(err ? null : f);
  };

  const handleUpload = async () => {
    if (!file) return;
    const s = await w.upload(file);
    if (s) w.setStep(2);
  };

  const srcType = file ? inferSourceType(file.name) : null;

  return (
    <div className="card">
      <h3 style={{ marginBottom: 6 }}>Bước 2 · Tải ảnh đơn thuốc hoặc tệp Excel</h3>
      <p style={{ color: "var(--pm-text-secondary)", marginBottom: 14 }}>
        Thành viên: <strong>{memberName}</strong>. Hệ thống chỉ tạo bản nháp để bạn rà soát — chưa ghi vào hồ sơ.
      </p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          pick(e.dataTransfer.files?.[0] ?? null);
        }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: "2px dashed var(--pm-border)",
          borderRadius: "var(--pm-radius-md)",
          padding: 32,
          textAlign: "center",
          cursor: "pointer",
          background: "var(--pm-bg)",
          marginBottom: 14,
        }}
      >
        <UploadCloud size={36} style={{ color: "var(--pm-primary)" }} />
        <div style={{ fontWeight: 600, marginTop: 8 }}>Kéo thả hoặc bấm để chọn tệp</div>
        <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
          JPG, PNG (≤10MB) · PDF (≤20MB) · XLSX, CSV (≤10MB)
        </div>
        <input
          ref={inputRef}
          type="file"
          hidden
          accept=".jpg,.jpeg,.png,.pdf,.xlsx,.csv"
          onChange={(e) => pick(e.target.files?.[0] ?? null)}
        />
      </div>

      {file && (
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
          {srcType === "EXCEL_XLSX" || srcType === "CSV" ? <FileSpreadsheet size={18} /> : <FileImage size={18} />}
          <strong>{file.name}</strong>
          <span className="badge badge-neutral">{srcType}</span>
          <span style={{ color: "var(--pm-text-secondary)", fontSize: "0.85rem" }}>
            {(file.size / 1024).toFixed(1)} KB
          </span>
        </div>
      )}
      {localError && <div className="alert-banner alert-danger" style={{ marginBottom: 12 }}>{localError}</div>}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-secondary" onClick={() => w.setStep(0)}>Quay lại</button>
        <button
          type="button"
          className="btn btn-outline"
          onClick={() => downloadExcelTemplate().catch((e) => setLocalError(String(e?.detail || e)))}
        >
          <Download size={16} /> Tải mẫu Excel chuẩn
        </button>
        <button type="button" className="btn btn-primary" disabled={!file || w.busy} onClick={handleUpload}>
          {w.busy ? "Đang phân tích tài liệu..." : "Tải lên & phân tích"}
        </button>
      </div>
    </div>
  );
};

