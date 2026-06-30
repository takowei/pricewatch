// Centralized API client with auth header and auto-refresh

import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  clearTokens,
} from "./auth";
import type {
  AccessTokenResponse,
  AlertResponse,
  PriceHistoryPoint,
  ProductResponse,
  TokenResponse,
  WatchlistCreateRequest,
  WatchlistResponse,
  WatchlistUpdateRequest,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// ── low-level fetch ────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const accessToken = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      return request<T>(path, options, false);
    }
    clearTokens();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = String(body.detail);
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

async function attemptRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as AccessTokenResponse;
    setAccessToken(data.access_token);
    return true;
  } catch {
    return false;
  }
}

// ── auth ──────────────────────────────────────────────────────────────────

export const auth = {
  register(email: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
};

// ── products ──────────────────────────────────────────────────────────────

export const products = {
  list(
    params: {
      brand?: string;
      keyword?: string;
      offset?: number;
      limit?: number;
    } = {},
  ): Promise<ProductResponse[]> {
    const query = new URLSearchParams();
    if (params.brand) query.set("brand", params.brand);
    if (params.keyword) query.set("keyword", params.keyword);
    if (params.offset !== undefined) query.set("offset", String(params.offset));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    const qs = query.toString();
    return request<ProductResponse[]>(`/products${qs ? `?${qs}` : ""}`);
  },

  get(id: number): Promise<ProductResponse> {
    return request<ProductResponse>(`/products/${id}`);
  },

  history(id: number): Promise<PriceHistoryPoint[]> {
    return request<PriceHistoryPoint[]>(`/products/${id}/history`);
  },
};

// ── watchlist ─────────────────────────────────────────────────────────────

export const watchlist = {
  list(): Promise<WatchlistResponse[]> {
    return request<WatchlistResponse[]>("/watchlist");
  },

  create(body: WatchlistCreateRequest): Promise<WatchlistResponse> {
    return request<WatchlistResponse>("/watchlist", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  update(id: number, body: WatchlistUpdateRequest): Promise<WatchlistResponse> {
    return request<WatchlistResponse>(`/watchlist/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  remove(id: number): Promise<void> {
    return request<void>(`/watchlist/${id}`, { method: "DELETE" });
  },
};

// ── alerts ────────────────────────────────────────────────────────────────

export const alerts = {
  list(
    params: { offset?: number; limit?: number } = {},
  ): Promise<AlertResponse[]> {
    const query = new URLSearchParams();
    if (params.offset !== undefined) query.set("offset", String(params.offset));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    const qs = query.toString();
    return request<AlertResponse[]>(`/alerts${qs ? `?${qs}` : ""}`);
  },
};
