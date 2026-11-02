import {
  API_BASE_URL,
  ApiError,
  apiRequest,
  getAccessToken,
} from "../../services/apiClient";
import type {
  CommitRequest,
  DraftUpdateRequest,
  ImportMode,
  ImportSession,
  ImportSourceType,
} from "./types";

const base = (familyId: number, memberId: number) =>
  `/families/${familyId}/members/${memberId}/imports`;

async function parseError(res: Response): Promise<ApiError> {
  let detail = `Lỗi hệ thống (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") detail = body.detail;
  } catch {
    // ignore
  }
  return new ApiError(res.status, detail);
}

export async function uploadImportFile(params: {
  familyId: number;
  memberId: number;
  file: File;
  sourceType?: ImportSourceType;
  importMode?: ImportMode;
  targetPrescriptionId?: number | null;
}): Promise<ImportSession> {
  const form = new FormData();
  form.append("file", params.file);
  if (params.sourceType) form.append("source_type", params.sourceType);
  if (params.importMode) form.append("import_mode", params.importMode);
  if (params.targetPrescriptionId)
    form.append("target_prescription_id", String(params.targetPrescriptionId));

  const token = getAccessToken();
  const res = await fetch(`${API_BASE_URL}${base(params.familyId, params.memberId)}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as ImportSession;
}

export const listImports = (familyId: number, memberId: number) =>
  apiRequest<{ items: ImportSession[] }>(base(familyId, memberId));

export const getImport = (familyId: number, memberId: number, importId: number) =>
  apiRequest<ImportSession>(`${base(familyId, memberId)}/${importId}`);

export const patchImportDraft = (
  familyId: number,
  memberId: number,
  importId: number,
  payload: DraftUpdateRequest
) =>
  apiRequest<ImportSession>(`${base(familyId, memberId)}/${importId}/draft`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const validateImport = (familyId: number, memberId: number, importId: number) =>
  apiRequest<ImportSession>(`${base(familyId, memberId)}/${importId}/validate`, {
    method: "POST",
  });

export const commitImport = (
  familyId: number,
  memberId: number,
  importId: number,
  payload: CommitRequest
) =>
  apiRequest<ImportSession>(`${base(familyId, memberId)}/${importId}/commit`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const rejectImport = (
  familyId: number,
  memberId: number,
  importId: number,
  reason?: string
) =>
  apiRequest<ImportSession>(`${base(familyId, memberId)}/${importId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason ?? null }),
  });

export async function downloadExcelTemplate(): Promise<void> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE_URL}/imports/templates/prescription.xlsx`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

