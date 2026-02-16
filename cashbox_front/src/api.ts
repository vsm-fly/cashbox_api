const TOKEN_KEY = "access_token";

// 1) Базовый URL: либо через Vite proxy (пусто), либо напрямую на backend
// Если у тебя в vite.config.ts есть proxy "/api" -> "http://localhost:8000",
// то BASE_URL можно оставить пустым "" и дергать "/api/v1/..."
const BASE_URL = import.meta.env.VITE_API_BASE ?? "";

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function buildUrl(path: string) {
  // чтобы не было двойных слэшей
  if (!BASE_URL) return path;
  if (path.startsWith("http")) return path;

  const base = BASE_URL.endsWith("/") ? BASE_URL.slice(0, -1) : BASE_URL;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * Низкоуровневый fetch: возвращает Response (как у тебя было),
 * но с нормализованным URL.
 */
export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();

  const headers = new Headers(options.headers);
  // Content-Type ставим только если есть body (иначе ломает download/file endpoints)
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(buildUrl(path), {
    ...options,
    headers,
  });

  if (res.status === 401 || res.status === 403) {
    clearToken();
  }

  return res;
}

/**
 * Высокоуровневый helper: сразу парсит JSON и кидает понятную ошибку.
 */
export async function apiFetchJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, options);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  // если вдруг 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return (await res.json()) as T;
}
