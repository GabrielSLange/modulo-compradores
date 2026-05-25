// Camada genérica de HTTP do front-end Equipe 4 — Demanda.
// - Usa SEMPRE rotas relativas (/api/...) para passar pelo Nginx/Gateway.
// - Anexa automaticamente o JWT salvo via auth.ts.
// - Lança ApiError em respostas não-2xx (consumido pelo fallback de mock).

import { getToken, clearToken } from "./auth";

export class ApiError extends Error {
  status: number;
  payload?: unknown;
  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

type Options = {
  signal?: AbortSignal;
  headers?: Record<string, string>;
  /** Se true, não envia Authorization mesmo com token salvo. */
  anonymous?: boolean;
};

async function request<T>(
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
  opts: Options = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(opts.headers ?? {}),
  };

  if (!opts.anonymous) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: opts.signal,
    });
  } catch (err) {
    // Falha de rede / CORS / Gateway offline — propaga para o fallback.
    throw new ApiError((err as Error).message || "Falha de rede", 0);
  }

  // Sessão expirada — limpa token para forçar novo login.
  if (res.status === 401) {
    clearToken();
  }

  const text = await res.text();
  const data = text ? safeJson(text) : undefined;

  if (!res.ok) {
    const msg =
      (data && typeof data === "object"
        ? String((data as { detail?: unknown; message?: unknown }).detail ?? (data as { message?: unknown }).message ?? "")
        : null) || `HTTP ${res.status}`;
    throw new ApiError(msg, res.status, data);
  }

  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  get: <T>(path: string, opts?: Options) => request<T>("GET", path, undefined, opts),
  post: <T>(path: string, body?: unknown, opts?: Options) => request<T>("POST", path, body, opts),
  patch: <T>(path: string, body?: unknown, opts?: Options) => request<T>("PATCH", path, body, opts),
  put: <T>(path: string, body?: unknown, opts?: Options) => request<T>("PUT", path, body, opts),
  del: <T>(path: string, opts?: Options) => request<T>("DELETE", path, undefined, opts),
  delete: <T>(path: string, opts?: Options) => request<T>("DELETE", path, undefined, opts),
};
