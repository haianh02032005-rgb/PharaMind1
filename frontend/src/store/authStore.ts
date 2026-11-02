import { create } from "zustand";
import { AuthUser, authService } from "../services/authService";
import { getAccessToken } from "../services/apiClient";

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hydrate: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: Boolean(getAccessToken()),
  isLoading: Boolean(getAccessToken()),

  hydrate: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const me = await authService.getMe();
      set({ user: me, isAuthenticated: true, isLoading: false });
    } catch {
      authService.logout();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => {
    set({ user, isAuthenticated: Boolean(user), isLoading: false });
  },

  logout: () => {
    authService.logout();
    set({ user: null, isAuthenticated: false, isLoading: false });
  },
}));

