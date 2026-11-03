import { useCallback } from "react";
import { useFamilyStore } from "../../store/familyStore";
import {
  commitImport,
  patchImportDraft,
  rejectImport,
  uploadImportFile,
  validateImport,
} from "./api";
import { useImportWizardStore } from "./store";
import type { DraftUpdateRequest, ImportSession } from "./types";
import { inferSourceType } from "./validation";

function errMsg(e: unknown): string {
  if (e && typeof e === "object" && "detail" in e) return String((e as { detail: string }).detail);
  if (e instanceof Error) return e.message;
  return "Đã xảy ra lỗi không xác định.";
}

/** Orchestrates wizard API calls with shared busy/error state. */
export function useImportWizard() {
  const familyId = useFamilyStore((s) => s.activeFamilyId);
  const store = useImportWizardStore();

  const run = useCallback(
    async (fn: () => Promise<ImportSession>): Promise<ImportSession | null> => {
      store.setBusy(true);
      store.setError(null);
      try {
        const s = await fn();
        store.setSession(s);
        return s;
      } catch (e) {
        store.setError(errMsg(e));
        return null;
      } finally {
        store.setBusy(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const upload = useCallback(
    (file: File) => {
      if (!familyId || !store.memberId) return Promise.resolve(null);
      store.setConfirmOcrReview(false);
      return run(() =>
        uploadImportFile({
          familyId,
          memberId: store.memberId as number,
          file,
          sourceType: inferSourceType(file.name) ?? undefined,
          importMode: store.importMode,
          targetPrescriptionId: store.targetPrescriptionId,
        })
      );
    },
    [familyId, store.memberId, store.importMode, store.targetPrescriptionId, run]
  );

  const patch = useCallback(
    (payload: DraftUpdateRequest) => {
      const s = store.session;
      if (!familyId || !s) return Promise.resolve(null);
      return run(() => patchImportDraft(familyId, s.member_id, s.id, payload));
    },
    [familyId, store.session, run]
  );

  const revalidate = useCallback(() => {
    const s = store.session;
    if (!familyId || !s) return Promise.resolve(null);
    return run(() => validateImport(familyId, s.member_id, s.id));
  }, [familyId, store.session, run]);

  const commit = useCallback(() => {
    const s = store.session;
    if (!familyId || !s) return Promise.resolve(null);
    return run(() =>
      commitImport(familyId, s.member_id, s.id, {
        confirm_member_id: s.member_id,
        confirm_import_mode: s.import_mode,
        confirm_schedule_creation: store.confirmSchedules,
        confirm_health_updates: store.confirmHealth,
        confirm_ocr_review: store.confirmOcrReview,
      })
    );
  }, [familyId, store.session, store.confirmSchedules, store.confirmHealth, store.confirmOcrReview, run]);

  const reject = useCallback(
    (reason?: string) => {
      const s = store.session;
      if (!familyId || !s) return Promise.resolve(null);
      return run(() => rejectImport(familyId, s.member_id, s.id, reason));
    },
    [familyId, store.session, run]
  );

  return { familyId, ...store, upload, patch, revalidate, commit, reject };
}

