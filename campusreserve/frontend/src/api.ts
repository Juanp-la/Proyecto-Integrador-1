// ─── API client for the CampusReserve Django backend ──────────────────────
// Implements HU1–HU8 against the real REST API instead of local mock data.

// - Development (npm run dev): VITE_API_BASE_URL, or the local Django server.
// - Production build (served by Django at "/"): same server, so just "/api".
//   This works on any IP/domain (e.g. the AWS EC2 public IP) without changes.
const API_BASE = import.meta.env.DEV
  ? import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"
  : "/api";

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
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
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
    let code: string | undefined;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
      code = body.code;
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, detail, code);
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
  is_outdoor: boolean;
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
  is_active: boolean; // computed by the backend in Bogotá time
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

export function logout() {
  setToken(null);
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

export async function leaveWaitlist(id: number): Promise<ApiWaitlistEntry> {
  return request<ApiWaitlistEntry>(`/waitlist/${id}/leave/`, { method: "POST" });
}

// ─── AI: recommendations + weather ─────────────────────────────────────────

export type AiSource = "ai" | "fallback";

export interface PopularCourtItem {
  court_id: number;
  name: string;
  sport: string;
  sport_code: string;
  location: string;
  reservations: number;
  waitlist_joins: number;
  peak_times: string[];
  reason: string;
}

export interface QuietSlotItem {
  court_id: number;
  court_name: string;
  sport: string;
  sport_code: string;
  date: string;
  weekday: string;
  start_time: string;
  end_time: string;
  usage_score: number;
  rain_probability: number | null;
  reason: string;
}

export interface Recommendations<T> {
  source: AiSource;
  summary: string;
  items: T[];
}

export interface WeatherReport {
  available: boolean;
  location?: string;
  day_label?: "hoy" | "mañana";
  current?: {
    temperature: number;
    apparent_temperature: number;
    humidity: number;
    condition: string;
    icon: string;
  } | null;
  date: string;
  source: AiSource;
  summary: string;
  condition?: string;
  icon?: string;
  temp_max?: number;
  temp_min?: number;
  precipitation_probability_max?: number;
  best_hours?: string[];
  advice?: string;
  bad_hours?: string[];
  hourly?: { hour: string; temperature: number; precipitation_probability: number; icon: string; condition?: string; bad: boolean }[];
}

export async function popularCourts(): Promise<Recommendations<PopularCourtItem>> {
  return request("/ai/recommendations/popular/");
}

export async function quietSlots(): Promise<Recommendations<QuietSlotItem>> {
  return request("/ai/recommendations/quiet/");
}

export async function weatherToday(): Promise<WeatherReport> {
  return request("/ai/weather/today/");
}

// ─── Notifications (weather alerts) ─────────────────────────────────────────

export interface ApiNotification {
  id: number;
  kind: "weather_alert";
  title: string;
  message: string;
  reservation: number | null;
  reservation_detail: ApiReservation | null;
  data: { label?: string; icon?: string; hour?: string; precipitation_probability?: number; source?: AiSource };
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export async function myNotifications(): Promise<ApiNotification[]> {
  return request<ApiNotification[]>("/notifications/");
}

export async function dismissNotification(id: number): Promise<ApiNotification> {
  return request<ApiNotification>(`/notifications/${id}/dismiss/`, { method: "POST" });
}

export async function cancelReservationFromNotification(id: number): Promise<ApiNotification> {
  return request<ApiNotification>(`/notifications/${id}/cancel-reservation/`, { method: "POST" });
}
