import { apiRequest } from "../../../services/apiClient";
import { DrawerRevealData } from "./types";

const revealCache = new Map<
  string,
  { data: DrawerRevealData; timestamp: number }
>();

const CACHE_TTL_MS = 8000;

function makeCacheKey(
  familyId: number,
  cabinetId: number,
  position: number
): string {
  return `${familyId}:${cabinetId}:${position}`;
}

export const drawerRevealApi = {
  async getCompartmentReveal(
    familyId: number,
    cabinetId: number,
    position: number,
    options?: { forceRefresh?: boolean }
  ): Promise<DrawerRevealData> {
    const key = makeCacheKey(familyId, cabinetId, position);
    if (!options?.forceRefresh) {
      const cached = revealCache.get(key);
      if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
        return cached.data;
      }
    }

    const data = await apiRequest<DrawerRevealData>(
      `/families/${familyId}/cabinets/${cabinetId}/compartments/${position}/reveal`
    );
    revealCache.set(key, { data, timestamp: Date.now() });
    return data;
  },

  invalidateCache(familyId?: number, cabinetId?: number): void {
    if (!familyId || !cabinetId) {
      revealCache.clear();
      return;
    }
    const prefix = `${familyId}:${cabinetId}:`;
    for (const k of revealCache.keys()) {
      if (k.startsWith(prefix)) {
        revealCache.delete(k);
      }
    }
  },
};

