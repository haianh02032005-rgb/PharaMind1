const configuredEnvironment =
  typeof import.meta !== "undefined"
    ? (import.meta as unknown as { env?: Record<string, string> }).env
    : undefined;

const pageOrigin =
  typeof window !== "undefined" ? window.location.origin : "http://localhost:8000";

function isLoopbackUrl(value: string): boolean {
  try {
    const hostname = new URL(value, pageOrigin).hostname.toLowerCase();
    return ["localhost", "127.0.0.1", "::1", "[::1]"].includes(hostname);
  } catch {
    return false;
  }
}

function resolveServiceBase(configured: string | undefined, fallback: string): string {
  // A localhost URL baked into a Vite build points to each visitor's own device.
  // When the app is opened through a public tunnel/domain, use the public origin
  // so a same-origin tunnel/proxy can forward API and WebSocket traffic.
  const isPublicPage = typeof window !== "undefined" && !isLoopbackUrl(pageOrigin);
  const selected = configured && !(isPublicPage && isLoopbackUrl(configured))
    ? configured
    : fallback;
  return selected.replace(/\/+$/, "");
}

export const API_BASE_URL = resolveServiceBase(
  configuredEnvironment?.VITE_API_BASE_URL,
  pageOrigin,
);

export const WS_BASE_URL = resolveServiceBase(
  configuredEnvironment?.VITE_WS_BASE_URL,
  API_BASE_URL.replace(/^http/, "ws"),
);

const ACCESS_TOKEN_KEY = "pm_access_token";
const REFRESH_TOKEN_KEY = "pm_refresh_token";

export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setTokens(accessToken: string, refreshToken: string): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  } catch {
    // ignore storage errors in test environments
  }
}

export function clearTokens(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // ignore
  }
}

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function attemptTokenRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = await res.json();
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token || refresh);
      return data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  retryOn401 = true
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const isAuthTokenEndpoint =
    path === "/auth/login" ||
    path === "/auth/register" ||
    path === "/auth/refresh";

  if (res.status === 401 && retryOn401 && !isAuthTokenEndpoint) {
    if (!refreshPromise) {
      refreshPromise = attemptTokenRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const newAccessToken = await refreshPromise;
    if (newAccessToken) {
      return apiRequest<T>(path, options, false);
    }
  }

  if (!res.ok) {
    let detail = `Lỗi hệ thống (${res.status})`;
    try {
      const errBody = await res.json();
      if (typeof errBody?.detail === "string") {
        detail = errBody.detail;
      } else if (Array.isArray(errBody?.detail)) {
        detail = errBody.detail
          .map((d: { msg?: string }) => d.msg || JSON.stringify(d))
          .join("; ");
      }
    } catch {
      // ignore json parse failure
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

