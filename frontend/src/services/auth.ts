// Gestão simples do JWT no localStorage.
// O login real é centralizado em /api/usuarios/auth/login (Equipe Usuários).

import { api } from "./api";

const TOKEN_KEY = "sdi.demanda.jwt";
const USER_KEY = "sdi.demanda.user";

export interface AuthUser {
  id: string;
  nome?: string;
  email?: string;
  id_empresa?: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getCurrentUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setCurrentUser(u: AuthUser) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(u));
}

interface LoginResponse {
  token: string;
  usuario?: AuthUser;
  user?: AuthUser;
}

/** POST /api/usuarios/auth/login — salva o token e o usuário. */
export async function login(email: string, senha: string): Promise<AuthUser | null> {
  const data = await api.post<LoginResponse>(
    "/api/usuarios/auth/login",
    { email, senha },
    { anonymous: true },
  );
  if (!data?.token) throw new Error("Resposta de login inválida.");
  setToken(data.token);
  const usuario = data.usuario ?? data.user ?? null;
  if (usuario) setCurrentUser(usuario);
  return usuario;
}

export function logout() {
  clearToken();
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
