import { create } from "zustand";
import { apiRequest } from "../services/apiClient";

export interface FamilyItem {
  id: number;
  name: string;
  description?: string | null;
  status: string;
  my_role?: string;
  created_at?: string;
}

export interface FamilyMemberItem {
  id: number;
  family_id: number;
  full_name: string;
  relationship_label?: string | null;
  date_of_birth?: string | null;
  gender?: string;
  phone?: string | null;
  notes?: string | null;
  status: string;
}

interface FamilyState {
  families: FamilyItem[];
  activeFamilyId: number | null;
  members: FamilyMemberItem[];
  isLoadingFamilies: boolean;
  fetchFamilies: () => Promise<FamilyItem[]>;
  setActiveFamilyId: (familyId: number) => Promise<void>;
  fetchMembers: (familyId?: number) => Promise<FamilyMemberItem[]>;
  createFamily: (name: string, description?: string) => Promise<FamilyItem>;
}

const ACTIVE_FAMILY_KEY = "pm_active_family_id";

function getStoredFamilyId(): number | null {
  try {
    const val = localStorage.getItem(ACTIVE_FAMILY_KEY);
    return val ? Number(val) : null;
  } catch {
    return null;
  }
}

export const useFamilyStore = create<FamilyState>((set, get) => ({
  families: [],
  activeFamilyId: getStoredFamilyId(),
  members: [],
  isLoadingFamilies: false,

  fetchFamilies: async () => {
    set({ isLoadingFamilies: true });
    try {
      const res = await apiRequest<{ items: FamilyItem[] }>("/families");
      const items = res.items || [];
      let currentId = get().activeFamilyId;
      if (!currentId || !items.some((f) => f.id === currentId)) {
        currentId = items[0]?.id ?? null;
      }
      if (currentId) {
        try {
          localStorage.setItem(ACTIVE_FAMILY_KEY, String(currentId));
        } catch {
          // ignore
        }
      }
      set({
        families: items,
        activeFamilyId: currentId,
        isLoadingFamilies: false,
      });
      if (currentId) {
        await get().fetchMembers(currentId);
      } else {
        set({ members: [] });
      }
      return items;
    } catch {
      set({ isLoadingFamilies: false });
      return [];
    }
  },

  setActiveFamilyId: async (familyId: number) => {
    try {
      localStorage.setItem(ACTIVE_FAMILY_KEY, String(familyId));
    } catch {
      // ignore
    }
    set({ activeFamilyId: familyId });
    await get().fetchMembers(familyId);
  },

  fetchMembers: async (familyId?: number) => {
    const targetId = familyId ?? get().activeFamilyId;
    if (!targetId) {
      set({ members: [] });
      return [];
    }
    try {
      const res = await apiRequest<{ items: FamilyMemberItem[] }>(
        `/families/${targetId}/members`
      );
      const items = res.items || [];
      set({ members: items });
      return items;
    } catch {
      set({ members: [] });
      return [];
    }
  },

  createFamily: async (name: string, description?: string) => {
    const created = await apiRequest<FamilyItem>("/families", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
    await get().fetchFamilies();
    await get().setActiveFamilyId(created.id);
    return created;
  },
}));

