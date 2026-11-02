import React, { useEffect, useState } from "react";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { toDraftItemPatch } from "../../features/importPrescription/mapping";
import { issuesForRow } from "../../features/importPrescription/validation";
import type { MedicationDraftItem, PrescriptionDraft } from "../../features/importPrescription/types";
import {
  ConflictAlert,
  FieldReviewRow,
  ImportSummaryCard,
  MedicationMatchCard,
  PrescriptionDiffCard,
} from "../../components/importPrescription/ImportComponents";

export const ReviewStep: React.FC = () => {
  const w = useImportWizard();
  const session = w.session;
  const review = session?.review_payload;
  const [rx, setRx] = useState<PrescriptionDraft>({});
  const [items, setItems] = useState<MedicationDraftItem[]>([]);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setRx({ ...(review?.prescription || {}) });
    setItems((review?.items || []).map((i) => ({ ...i })));
    setDirty(false);
  }, [review]);

  if (!session) return null;

  const headerIssues = session.validation_issues.filter((i) => !i.field_path.startsWith("items["));
  const memberMismatch = session.validation_issues.some((i) => i.code === "MEMBER_MISMATCH");
  const dup = session.validation_issues.some((i) => i.code === "DUPLICATE_FILE");
  const conf = rx.field_confidences || {};

  const setRxField = (k: keyof PrescriptionDraft, v: string) => {
    setRx((p) => ({ ...p, [k]: v }));
    setDirty(true);
  };

  const save = async () => {
    const s = await w.patch({
      prescription: {
        title: rx.title ?? null,
        doctor_name: rx.doctor_name ?? null,
        facility_name: rx.facility_name ?? null,
        issued_at: rx.issued_at || null,
        start_date: rx.start_date || null,
        end_date: rx.end_date || null,
      },
      items: items.map(toDraftItemPatch),
    });
    return s;
  };

  const next = async () => {
    const s = dirty ? await save() : session;
    if (s) w.setStep(3);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <ImportSummaryCard session={session} />
      <ConflictAlert issues={headerIssues} />

      {(memberMismatch || dup) && (
        <div className="card" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {memberMismatch && (
            <button type="button" className="btn btn-outline" disabled={w.busy} onClick={() => w.patch({ confirm_member_match: true })}>
              Tôi xác nhận đơn thuốc này thuộc về thành viên đã chọn
            </button>
          )}
          {dup && (
            <button type="button" className="btn btn-outline" disabled={w.busy} onClick={() => w.patch({ confirm_duplicate_override: true })}>
              Tôi biết đây là tài liệu đã nhập, vẫn tiếp tục
            </button>
          )}
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: 10 }}>Bước 3 · Rà soát thông tin đơn thuốc</h3>
        <div className="grid-2">
          <FieldReviewRow label="Tiêu đề đơn" value={rx.title || ""} onChange={(v) => setRxField("title", v)} />
          <FieldReviewRow label="Tên người bệnh (trong tài liệu)" value={rx.member_name || ""} disabled confidence={conf.member_name} onChange={() => undefined} />
          <FieldReviewRow label="Bác sĩ" value={rx.doctor_name || ""} confidence={conf.doctor_name} onChange={(v) => setRxField("doctor_name", v)} />
          <FieldReviewRow label="Cơ sở khám" value={rx.facility_name || ""} confidence={conf.facility_name} onChange={(v) => setRxField("facility_name", v)} />
        </div>
        <div className="grid-3">
          <FieldReviewRow label="Ngày kê" type="date" value={rx.issued_at || ""} confidence={conf.issued_at} onChange={(v) => setRxField("issued_at", v)} />
          <FieldReviewRow label="Ngày bắt đầu" type="date" value={rx.start_date || ""} onChange={(v) => setRxField("start_date", v)} />
          <FieldReviewRow label="Ngày kết thúc" type="date" value={rx.end_date || ""} onChange={(v) => setRxField("end_date", v)} />
        </div>
      </div>

      {review?.prescription_diff && <PrescriptionDiffCard diff={review.prescription_diff} />}

      {items.map((it, idx) => (
        <MedicationMatchCard
          key={it.row_index}
          item={it}
          issues={issuesForRow(session.validation_issues, it.row_index).filter((i) => !i.field_path.includes(".schedule"))}
          onChange={(nextItem) => {
            setItems((prev) => prev.map((p, i) => (i === idx ? nextItem : p)));
            setDirty(true);
          }}
        />
      ))}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-secondary" onClick={() => w.setStep(1)}>Quay lại</button>
        <button type="button" className="btn btn-outline" disabled={!dirty || w.busy} onClick={save}>
          Lưu bản nháp & kiểm tra lại
        </button>
        <button type="button" className="btn btn-primary" disabled={w.busy} onClick={next}>
          Tiếp tục: Lịch uống
        </button>
      </div>
    </div>
  );
};

