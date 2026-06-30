// TypeScript types aligned with backend schemas

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface ProductResponse {
  id: number;
  brand: string;
  name: string;
  category: string;
  product_url: string;
  image_url: string;
  current_sale_price: number | null;
  original_price: number | null;
  discount: number | null;
  last_scraped_at: string;
}

export interface PriceHistoryPoint {
  recorded_date: string;
  sale_price: number | null;
  discount: number | null;
}

export interface WatchlistResponse {
  id: number;
  user_id: number;
  keyword: string;
  max_price: number | null;
  is_active: boolean;
  created_at: string;
}

export interface WatchlistCreateRequest {
  keyword: string;
  max_price: number | null;
}

export interface WatchlistUpdateRequest {
  keyword?: string;
  max_price?: number | null;
  is_active?: boolean;
}

export interface AlertResponse {
  id: number;
  user_id: number;
  watchlist_id: number;
  product_id: number;
  triggered_price: number;
  reason: "at_target" | "price_drop" | string;
  is_notified: boolean;
  created_at: string;
}

export interface ApiError {
  detail: string;
}
