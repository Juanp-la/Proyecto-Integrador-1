// ─── API client for the CampusReserve Django backend ──────────────────────
// Implements HU1–HU8 against the real REST API instead of local mock data.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const TOKEN_KEY = "campusreserve_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // localStorage unavailable — the session simply won't persist on reload.
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Types mirroring the backend serializers ───────────────────────────────

export interface ApiCourt {
  id: number;
  name: string;
  sport: "soccer" | "basketball_volleyball" | "basketball" | "volleyball";
  location: string;
  capacity: string;
  surface: string;
  image_ref: string;
  is_active: boolean;
  status?: "available" | "reserved";
}

export interface ApiReservation {
  id: number;
  court: number;
  court_detail: ApiCourt;
  reservation_date: string;
  start_time: string;
  end_time: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  cancelled_at: string | null;
}

export interface ApiWaitlistEntry {
  id: number;
  court: number;
  court_detail: ApiCourt;
  reservation_date: string;
  start_time: string;
  end_time: string;
  queue_position: number;
  status: "waiting" | "notified" | "expired" | "confirmed" | "cancelled";
  joined_at: string;
  notified_at: string | null;
  expires_at: string | null;
}

export interface ApiUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

// ─── Auth (FR20) ────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<string> {
  const data = await request<{ access: string; refresh: string }>("/token/", {
    method: "POST",
    body: JSON.stringify({ username: email, password }),
  });
  setToken(data.access);
  return data.access;
}

export async function register(input: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}): Promise<void> {
  await request("/accounts/register/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function me(): Promise<ApiUser> {
  return request<ApiUser>("/accounts/me/");
}

// ─── Courts (HU1, HU3, HU5) ─────────────────────────────────────────────────

export async function listCourts(params?: {
  sport?: string;
  date?: string;
  start_time?: string;
  end_time?: string;
}): Promise<ApiCourt[]> {
  const qs = params
    ? "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => !!v) as [string, string][]).toString()
    : "";
  return request<ApiCourt[]>(`/courts/${qs}`);
}

// ─── Reservations (HU2, HU4) ─────────────────────────────────────────────────

export async function myReservations(): Promise<ApiReservation[]> {
  return request<ApiReservation[]>("/reservations/mine/");
}

export async function createReservation(input: {
  court: number;
  reservation_date: string;
  start_time: string;
  end_time: string;
}): Promise<ApiReservation> {
  return request<ApiReservation>("/reservations/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function cancelReservation(id: number): Promise<ApiReservation> {
  return request<ApiReservation>(`/reservations/${id}/cancel/`, { method: "POST" });
}

// ─── Waiting list (HU6, HU7, HU8) ────────────────────────────────────────────

export async function myWaitlist(): Promise<ApiWaitlistEntry[]> {
  return request<ApiWaitlistEntry[]>("/waitlist/mine/");
}

export async function joinWaitlist(input: {
  court: number;
  reservation_date: string;
  start_time: string;
  end_time: string;
}): Promise<ApiWaitlistEntry> {
  return request<ApiWaitlistEntry>("/waitlist/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function confirmWaitlistOffer(id: number): Promise<ApiReservation> {
  return request<ApiReservation>(`/waitlist/${id}/confirm/`, { method: "POST" });
}
