import { apiRequest, clearTokens, setTokens } from "./apiClient";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  status: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  async register(payload: {
    email: string;
    password: string;
    full_name: string;
  }): Promise<AuthUser> {
    return apiRequest<AuthUser>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login(payload: {
    email: string;
    password: string;
  }): Promise<TokenResponse> {
    const tokens = await apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  async getMe(): Promise<AuthUser> {
    return apiRequest<AuthUser>("/auth/me");
  },

  logout(): void {
    clearTokens();
  },
};

