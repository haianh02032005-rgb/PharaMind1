import React from "react";
import { useNavigate } from "react-router-dom";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { IMPORT_MODE_LABELS, formatDoseVi } from "../../features/importPrescription/mapping";
import { canCommit, getBlockingIssues } from "../../features/importPrescription/validation";
import { useFamilyStore } from "../../store/familyStore";
import {
  CommitSummary,
  ConflictAlert,
  HealthUpdatePreview,
  ImportSummaryCard,
  SchedulePreview,
} from "../../components/importPrescription/ImportComponents";

export const ConfirmStep: React.FC = () => {
  const w = useImportWizard();
  const navigate = useNavigate();
  const members = useFamilyStore((s) => s.members);
  const session = w.session;
  if (!session) return null;

  if (session.status === "COMMITTED") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <CommitSummary summary={session.commit_summary} links={session.entity_links} />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="button" className="btn btn-primary" onClick={() => navigate("/prescriptions")}>Xem Đơn thuốc</button>
          <button type="button" className="btn btn-outline" onClick={() => navigate("/schedules")}>Xem Lịch uống</button>
          <button type="button" className="btn btn-secondary" onClick={() => w.reset()}>Nhập đơn khác</button>
        </div>
      </div>
    );
  }

  const review = session.review_payload || {};
  const items = (review.items || []).filter((i) => i.action !== "SKIP");
  const memberName = members.find((m) => m.id === session.member_id)?.full_name || `#${session.member_id}`;
  const blocking = getBlockingIssues(session.validation_issues);
  const isOcr = session.source_type === "OCR_IMAGE" || session.source_type === "OCR_PDF";
  const ok = canCommit(session) && (!isOcr || w.confirmOcrReview);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <ImportSummaryCard session={session} />
      <div className="card">
        <h3 style={{ marginBottom: 10 }}>Bước 6 · Xác nhận lưu vào hồ sơ</h3>
        <p>Thành viên: <strong>{memberName}</strong></p>
        <p>Chế độ: <strong>{IMPORT_MODE_LABELS[session.import_mode]}</strong></p>
        <p>Đơn thuốc: <strong>{review.prescription?.title || "(không tiêu đề)"}</strong></p>
        <ul style={{ marginTop: 8 }}>
          {items.map((i) => (
            <li key={i.row_index}>
              {i.medication_name} — {formatDoseVi(i)}{" "}
              <em style={{ color: "var(--pm-text-secondary)" }}>
                ({i.action === "LINK_EXISTING" ? "dùng thuốc có sẵn" : "tạo thuốc mới"})
              </em>
            </li>
          ))}
        </ul>
      </div>

      <SchedulePreview items={items} />
      <div className="card">
        <h3 style={{ marginBottom: 8 }}>Cập nhật Hồ sơ sức khỏe</h3>
        <HealthUpdatePreview health={review.health_updates} />
      </div>

      <div className="card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="checkbox" checked={w.confirmSchedules} onChange={(e) => w.setConfirmSchedules(e.target.checked)} />
          Tạo lịch uống thuốc theo cấu hình ở trên
        </label>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="checkbox" checked={w.confirmHealth} onChange={(e) => w.setConfirmHealth(e.target.checked)} />
          Lưu các cập nhật Hồ sơ sức khỏe đã chọn
        </label>
        {isOcr && (
          <label style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <input
              type="checkbox"
              checked={w.confirmOcrReview}
              onChange={(e) => w.setConfirmOcrReview(e.target.checked)}
              style={{ marginTop: 3 }}
            />
            Tôi đã đối chiếu tên thuốc, hàm lượng, liều mỗi lần, đường dùng và tần suất với đơn thuốc gốc.
          </label>
        )}
      </div>

      {blocking.length > 0 && <ConflictAlert issues={blocking} />}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-secondary" onClick={() => w.setStep(4)}>Quay lại</button>
        <button
          type="button"
          className="btn btn-danger"
          disabled={w.busy}
          onClick={async () => {
            if (window.confirm("Hủy phiên nhập này? Không có dữ liệu nào được lưu.")) {
              const s = await w.reject("Người dùng hủy");
              if (s) w.reset();
            }
          }}
        >
          Hủy phiên nhập
        </button>
        <button type="button" className="btn btn-primary" disabled={!ok || w.busy} onClick={() => w.commit()}>
          {w.busy ? "Đang lưu..." : "Xác nhận & Lưu"}
        </button>
      </div>
    </div>
  );
};

