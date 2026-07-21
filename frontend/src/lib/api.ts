export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:18080/api";

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

function headers(token?: string): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function request(url: string, options?: RequestInit): Promise<any> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const body = await res.json(); if (body.detail) detail = body.detail; } catch {}
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export async function createProject(input: string, token?: string, userId?: string) {
  return request(`${API_BASE}/projects`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify({ input, user_id: userId || "" }),
  });
}

export async function getProject(id: string, token?: string) {
  return request(`${API_BASE}/projects/${id}`, {
    headers: headers(token),
  });
}

export async function updateProject(id: string, body: any, token?: string) {
  return request(`${API_BASE}/projects/${id}`, {
    method: "PATCH",
    headers: headers(token),
    body: JSON.stringify(body),
  });
}

export async function regenerateModule(id: string, module: string, token?: string) {
  return request(`${API_BASE}/projects/${id}/regenerate`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify({ module }),
  });
}

export async function listProjects(userId: string, token?: string) {
  return request(`${API_BASE}/projects?user_id=${userId}`, {
    headers: headers(token),
  });
}

export async function renderProject(id: string, token?: string) {
  return request(`${API_BASE}/projects/${id}/render`, {
    method: "POST",
    headers: headers(token),
  });
}
