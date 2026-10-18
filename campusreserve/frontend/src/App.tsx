import { useEffect, useState } from "react";
import * as api from "./api";
import type { ApiCourt, ApiReservation, ApiWaitlistEntry } from "./api";

// ─── Accent color: sky blue that contrasts with navy #1B2A4A ─────────────────
const A = "#4A9EE8";      // primary accent
const AH = "#3A8ED8";     // hover
const ABG = "#EAF4FD";    // light tint bg
const ATXT = "#1A5FA0";   // text on tint

// ─── Types ────────────────────────────────────────────────────────────────────

type Screen = "login" | "home" | "my-reservations" | "book" | "waitlist-notification";
type ModalType = "cancel" | null;

interface Reservation {
  id: number;
  sport: string;
  sportIcon: string;
  court: string;
  date: string;
  time: string;
  status: "Confirmed";
}

// ─── Sport display metadata (backend stores machine-readable sport codes) ────

const SPORT_META: Record<string, { icon: string; label: string }> = {
  soccer: { icon: "⚽", label: "Fútbol" },
  basketball_volleyball: { icon: "🏀", label: "Básquetbol / Vóley" },
  basketball: { icon: "🏀", label: "Básquetbol" },
  volleyball: { icon: "🏐", label: "Vóley" },
};

function sportMeta(sport: string) {
  return SPORT_META[sport] || { icon: "🏟️", label: sport };
}

// ─── Schedule data ─────────────────────────────────────────────────────────────
// DAYS is generated from the real current date (today .. today+5) so the
// dates sent to the backend are real calendar dates, not a fixed demo week.

const WEEKDAY_LABELS = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
const MONTH_LABELS = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

function buildDays() {
  const days = [];
  const today = new Date();
  for (let i = 0; i < 6; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const iso = d.toISOString().slice(0, 10); // YYYY-MM-DD
    const weekdayLabel = WEEKDAY_LABELS[d.getDay()];
    days.push({
      key: iso,
      label: weekdayLabel,
      full: `${weekdayLabel}, ${d.getDate()} de ${MONTH_LABELS[d.getMonth()]}`,
    });
  }
  return days;
}

const DAYS = buildDays();

const SLOTS = [
  "06:00 – 07:00",
  "07:00 – 08:00",
  "08:00 – 09:00",
  "09:00 – 10:00",
  "10:00 – 11:00",
  "11:00 – 12:00",
  "14:00 – 15:00",
  "15:00 – 16:00",
  "16:00 – 17:00",
  "17:00 – 18:00",
  "18:00 – 19:00",
];

function slotToTimes(slot: string): { start: string; end: string } {
  const [start, end] = slot.split(" – ");
  return { start, end };
}

interface Court {
  id: number;
  icon: string;
  name: string;
  sport: string;
  location: string;
  capacity: string;
  surface: string;
  img: string;
}

function toUiCourt(c: ApiCourt): Court {
  const meta = sportMeta(c.sport);
  return {
    id: c.id,
    icon: meta.icon,
    name: c.name,
    sport: meta.label,
    location: c.location,
    capacity: c.capacity,
    surface: c.surface,
    img: c.image_ref,
  };
}

function toUiReservation(r: ApiReservation): Reservation {
  const meta = sportMeta(r.court_detail.sport);
  return {
    id: r.id,
    sport: meta.label,
    sportIcon: meta.icon,
    court: r.court_detail.name,
    date: r.reservation_date,
    time: `${r.start_time.slice(0, 5)} – ${r.end_time.slice(0, 5)}`,
    status: "Confirmed",
  };
}

// ─── Shared Components ────────────────────────────────────────────────────────

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: A }}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="2" y="2" width="6" height="6" rx="1.5" fill="white" />
          <rect x="10" y="2" width="6" height="6" rx="1.5" fill="white" opacity="0.6" />
          <rect x="2" y="10" width="6" height="6" rx="1.5" fill="white" opacity="0.6" />
          <rect x="10" y="10" width="6" height="6" rx="1.5" fill="white" />
        </svg>
      </div>
      <span className="text-white font-bold text-lg tracking-tight">
        Campus<span style={{ color: A }}>Reserve</span>
      </span>
    </div>
  );
}

function Navbar({ onNavigate, active, userName }: { onNavigate: (s: Screen) => void; active: Screen; userName: string }) {
  const initials = userName.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const link = (s: Screen, label: string) => (
    <button
      onClick={() => onNavigate(s)}
      className="text-sm font-medium transition-colors cursor-pointer"
      style={{ color: active === s ? A : undefined }}
      onMouseEnter={e => { if (active !== s) (e.target as HTMLElement).style.color = "white"; }}
      onMouseLeave={e => { if (active !== s) (e.target as HTMLElement).style.color = "rgba(255,255,255,0.7)"; }}
    >
      <span style={{ color: active === s ? A : "rgba(255,255,255,0.7)" }}>{label}</span>
    </button>
  );

  return (
    <nav className="bg-[#1B2A4A] h-16 flex items-center px-6 shadow-lg flex-shrink-0">
      <button onClick={() => onNavigate("home")} className="cursor-pointer">
        <Logo />
      </button>
      <div className="ml-auto flex items-center gap-6">
        {link("home", "Inicio")}
        {link("my-reservations", "Mis reservas")}
        {link("book", "Reservar")}
        {link("waitlist-notification", "Notificaciones")}
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-sm cursor-pointer transition-colors"
          style={{ background: A }}
          onMouseEnter={e => (e.currentTarget.style.background = AH)}
          onMouseLeave={e => (e.currentTarget.style.background = A)}
        >
          {initials || "?"}
        </div>
      </div>
    </nav>
  );
}

function StatusBadge({ type }: { type: "confirmed" | "reserved" | "waitlist" }) {
  if (type === "confirmed")
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#E8F6EE] text-[#1A8A4A]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#1A8A4A]" />Confirmada
      </span>
    );
  if (type === "reserved")
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#FEF0DC] text-[#D4720A]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#D4720A]" />Reservada
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#E8F6EE] text-[#1A8A4A]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#1A8A4A]" />En espera
    </span>
  );
}

// ─── Login Screen ─────────────────────────────────────────────────────────────

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const canSubmit =
    email.trim() && password.trim() && (mode === "login" || (firstName.trim() && lastName.trim()));

  const submit = async () => {
    if (!canSubmit || loading) return;
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await api.register({
          email: email.trim(),
          password,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
        });
      }
      await api.login(email.trim(), password);
      onLogin();
    } catch (err) {
      setError(err instanceof api.ApiError ? err.message : "No se pudo iniciar sesión. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="size-full flex flex-col items-center justify-center bg-[#F4F6FA]" style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Card */}
      <div className="bg-white rounded-3xl shadow-xl border border-[#E8ECF4] w-full max-w-sm px-8 py-10">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: A }}>
              <svg width="22" height="22" viewBox="0 0 18 18" fill="none">
                <rect x="2" y="2" width="6" height="6" rx="1.5" fill="white" />
                <rect x="10" y="2" width="6" height="6" rx="1.5" fill="white" opacity="0.6" />
                <rect x="2" y="10" width="6" height="6" rx="1.5" fill="white" opacity="0.6" />
                <rect x="10" y="10" width="6" height="6" rx="1.5" fill="white" />
              </svg>
            </div>
            <span className="text-[#1B2A4A] font-bold text-xl tracking-tight">
              Campus<span style={{ color: A }}>Reserve</span>
            </span>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-[#111B30] text-center mb-1">
          {mode === "login" ? "Bienvenido" : "Crear cuenta"}
        </h1>
        <p className="text-sm text-[#6B7A99] text-center mb-8">
          Universidad EAFIT · Sistema de reservas deportivas
        </p>

        {mode === "register" && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs font-semibold text-[#111B30] mb-1.5">Nombre</label>
              <input
                type="text" value={firstName} onChange={e => setFirstName(e.target.value)}
                className="w-full border border-[#D0D6E8] rounded-xl px-3 py-3 text-sm text-[#111B30] outline-none focus:border-[#4A9EE8]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#111B30] mb-1.5">Apellido</label>
              <input
                type="text" value={lastName} onChange={e => setLastName(e.target.value)}
                className="w-full border border-[#D0D6E8] rounded-xl px-3 py-3 text-sm text-[#111B30] outline-none focus:border-[#4A9EE8]"
              />
            </div>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-xs font-semibold text-[#111B30] mb-1.5">Correo institucional</label>
          <input
            type="email"
            placeholder="tu.nombre@eafit.edu.co"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full border border-[#D0D6E8] rounded-xl px-4 py-3 text-sm text-[#111B30] placeholder:text-[#A0AABF] outline-none transition-all focus:border-[#4A9EE8]"
            autoFocus
          />
        </div>

        <div className="mb-2">
          <label className="block text-xs font-semibold text-[#111B30] mb-1.5">Contraseña</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === "Enter" && submit()}
            className="w-full border border-[#D0D6E8] rounded-xl px-4 py-3 text-sm text-[#111B30] placeholder:text-[#A0AABF] outline-none transition-all focus:border-[#4A9EE8]"
          />
        </div>

        {error && <p className="text-xs text-[#C0392B] mt-2">{error}</p>}

        <button
          onClick={submit}
          disabled={!canSubmit || loading}
          className="w-full py-3 text-white font-semibold text-sm rounded-xl transition-all mt-4 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ background: canSubmit ? A : "#A0AABF" }}
          onMouseEnter={e => { if (canSubmit) (e.currentTarget.style.background = AH); }}
          onMouseLeave={e => { if (canSubmit) (e.currentTarget.style.background = A); }}
        >
          {loading ? "Cargando…" : mode === "login" ? "Ingresar" : "Crear cuenta"}
        </button>

        <button
          onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
          className="w-full text-xs text-center mt-4 font-medium transition-colors"
          style={{ color: A }}
        >
          {mode === "login" ? "¿No tienes cuenta? Regístrate" : "¿Ya tienes cuenta? Inicia sesión"}
        </button>

        <p className="text-xs text-[#A0AABF] text-center mt-5">
          Solo para estudiantes y docentes EAFIT (@eafit.edu.co)
        </p>
      </div>
    </div>
  );
}

// ─── Home Screen ──────────────────────────────────────────────────────────────

function HomeScreen({ onNavigate, reservations, userName }: { onNavigate: (s: Screen) => void; reservations: Reservation[]; userName: string }) {
  const firstName = userName.split(" ")[0];

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      {/* Hero */}
      <div className="bg-[#1B2A4A] px-6 pt-10 pb-10 relative overflow-hidden">
        <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full" style={{ background: `${A}18` }} />
        <div className="absolute right-20 top-12 w-32 h-32 rounded-full" style={{ background: `${A}10` }} />
        <div className="max-w-3xl mx-auto relative">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: A }}>
            Universidad EAFIT
          </p>
          <h1 className="text-white text-4xl font-bold leading-tight mb-2">
            Bienvenido,<br />
            <span style={{ color: A }}>{firstName}</span>
          </h1>
          <p className="text-white/60 text-sm mt-2 mb-6">
            Martes, 8 de septiembre de 2026 · Semestre 2026-2
          </p>
          <button
            onClick={() => onNavigate("book")}
            className="inline-flex items-center gap-2 px-5 py-3 text-white font-semibold text-sm rounded-xl shadow-lg transition-colors"
            style={{ background: A }}
            onMouseEnter={e => (e.currentTarget.style.background = AH)}
            onMouseLeave={e => (e.currentTarget.style.background = A)}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" stroke="white" strokeWidth="1.5" />
              <path d="M8 5v6M5 8h6" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
            Reservar cancha
          </button>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 pt-8">
        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { value: reservations.length.toString(), label: "Reservas activas", icon: "📅", color: "#1B2A4A" },
            { value: "3", label: "Días hasta el fin de semana", icon: "🗓", color: "#1A8A4A" },
            { value: "12", label: "Reservas este semestre", icon: "🏅", color: A },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-4">
              <div className="text-2xl mb-1">{s.icon}</div>
              <p className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</p>
              <p className="text-xs text-[#6B7A99] mt-0.5 leading-snug">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Sports */}
        <div className="mb-8">
          <h2 className="text-lg font-bold text-[#111B30] mb-4">Deportes disponibles</h2>
          <div className="grid grid-cols-4 gap-3">
            {[
              { icon: "⚽", name: "Fútbol", courts: 2 },
              { icon: "🏀", name: "Básquetbol", courts: 1 },
              { icon: "🏐", name: "Vóley", courts: 1 },
              { icon: "🏊", name: "Natación", courts: 2 },
            ].map((s) => (
              <button
                key={s.name}
                onClick={() => onNavigate("book")}
                className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-4 flex flex-col items-center gap-2 hover:shadow-md transition-all cursor-pointer group"
                onMouseEnter={e => (e.currentTarget.style.borderColor = `${A}66`)}
                onMouseLeave={e => (e.currentTarget.style.borderColor = "#E8ECF4")}
              >
                <div className="text-3xl group-hover:scale-110 transition-transform">{s.icon}</div>
                <p className="text-sm font-semibold text-[#111B30]">{s.name}</p>
                <p className="text-xs text-[#6B7A99]">{s.courts} canchas</p>
              </button>
            ))}
          </div>
        </div>

        {/* Próximas reservas */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-[#111B30]">Próximas reservas</h2>
            <button onClick={() => onNavigate("my-reservations")} className="text-sm font-medium transition-colors" style={{ color: A }}
              onMouseEnter={e => (e.currentTarget.style.color = AH)}
              onMouseLeave={e => (e.currentTarget.style.color = A)}
            >
              Ver todas →
            </button>
          </div>
          {reservations.length === 0 ? (
            <div className="bg-white rounded-2xl border border-[#E8ECF4] p-8 flex flex-col items-center text-center">
              <div className="text-3xl mb-3">📅</div>
              <p className="text-sm font-semibold text-[#111B30]">Sin reservas activas</p>
              <p className="text-xs text-[#6B7A99] mt-1 mb-4">Reserva una cancha para empezar</p>
              <button onClick={() => onNavigate("book")} className="px-4 py-2 text-white text-sm font-semibold rounded-xl transition-colors" style={{ background: A }}
                onMouseEnter={e => (e.currentTarget.style.background = AH)}
                onMouseLeave={e => (e.currentTarget.style.background = A)}
              >
                Reservar ahora
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {reservations.slice(0, 3).map((r) => (
                <div key={r.id} className="bg-white rounded-xl border border-[#E8ECF4] p-4 flex items-center gap-4 hover:shadow-sm transition-shadow">
                  <div className="w-10 h-10 rounded-lg bg-[#F4F6FA] flex items-center justify-center text-xl flex-shrink-0">{r.sportIcon}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[#111B30] truncate">{r.court}</p>
                    <p className="text-xs text-[#6B7A99] mt-0.5">{r.date} · {r.time}</p>
                  </div>
                  <StatusBadge type="confirmed" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available today */}
        <div className="mb-10">
          <h2 className="text-lg font-bold text-[#111B30] mb-4">Canchas disponibles hoy</h2>
          <div className="grid grid-cols-2 gap-4">
            {[
              { icon: "⚽", name: "Cancha de Fútbol 2", sport: "Fútbol 7", slots: 3, img: "photo-1575361204480-aadea25e6e68" },
              { icon: "🏊", name: "Piscina Olímpica", sport: "Natación · Carril libre", slots: 5, img: "photo-1519315901367-f34ff9154487" },
              { icon: "🏐", name: "Cancha Multiuso B", sport: "Vóley", slots: 2, img: "photo-1547347298-4074fc3086f0" },
              { icon: "🏀", name: "Cancha Multiuso A", sport: "Básquetbol", slots: 4, img: "photo-1546519638-68e109498ffc" },
            ].map((c) => (
              <button key={c.name} onClick={() => onNavigate("book")}
                className="bg-white rounded-2xl border border-[#E8ECF4] overflow-hidden hover:shadow-md transition-shadow text-left cursor-pointer group"
              >
                <div className="relative h-28 bg-[#1B2A4A]">
                  <img src={`https://images.unsplash.com/${c.img}?w=400&h=200&fit=crop&auto=format`} alt={c.name}
                    className="w-full h-full object-cover opacity-60 group-hover:opacity-70 transition-opacity" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#111B30]/60 to-transparent" />
                  <div className="absolute top-2.5 right-2.5">
                    <span className="bg-[#E8F6EE] text-[#1A8A4A] text-xs font-semibold px-2 py-0.5 rounded-full">{c.slots} horarios</span>
                  </div>
                </div>
                <div className="p-3.5">
                  <p className="text-sm font-semibold text-[#111B30] truncate">{c.name}</p>
                  <p className="text-xs text-[#6B7A99] mt-0.5">{c.sport}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── My Reservations ──────────────────────────────────────────────────────────

function MyReservationsScreen({ onNavigate, reservations, onCancel, loading }: {
  onNavigate: (s: Screen) => void;
  reservations: Reservation[];
  onCancel: (r: Reservation) => void;
  loading: boolean;
}) {
  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Universidad EAFIT</p>
          <h1 className="text-3xl font-bold text-[#111B30]">Mis reservas</h1>
          <p className="text-sm text-[#6B7A99] mt-1">{reservations.length} reserva{reservations.length !== 1 ? "s" : ""} activa{reservations.length !== 1 ? "s" : ""}</p>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-16 flex flex-col items-center text-center">
            <p className="text-sm text-[#6B7A99]">Cargando tus reservas…</p>
          </div>
        ) : reservations.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-16 flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#F4F6FA] flex items-center justify-center text-3xl mb-4">📅</div>
            <h3 className="text-lg font-semibold text-[#111B30] mb-2">No tienes reservas activas</h3>
            <p className="text-sm text-[#6B7A99] mb-6 max-w-xs">Reserva una cancha o carril para comenzar a disfrutar de las instalaciones.</p>
            <button onClick={() => onNavigate("book")} className="px-5 py-2.5 text-white text-sm font-semibold rounded-xl transition-colors" style={{ background: A }}
              onMouseEnter={e => (e.currentTarget.style.background = AH)}
              onMouseLeave={e => (e.currentTarget.style.background = A)}
            >Reservar ahora</button>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {reservations.map((r) => (
              <div key={r.id} className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-5 flex items-center gap-5 hover:shadow-md transition-shadow">
                <div className="w-14 h-14 rounded-xl bg-[#F4F6FA] flex items-center justify-center text-2xl flex-shrink-0">{r.sportIcon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge type="confirmed" />
                    <span className="text-xs text-[#6B7A99]">{r.sport}</span>
                  </div>
                  <h3 className="text-base font-semibold text-[#111B30] truncate">{r.court}</h3>
                  <div className="flex items-center gap-3 mt-1.5 text-sm text-[#6B7A99]">
                    <span>{r.date}</span>
                    <span className="w-1 h-1 rounded-full bg-[#D0D6E8]" />
                    <span>{r.time}</span>
                  </div>
                </div>
                <button
                  onClick={() => onCancel(r)}
                  className="flex-shrink-0 px-4 py-2 border border-[#C0392B]/30 text-[#C0392B] text-sm font-medium rounded-xl hover:bg-[#FDEDEC] transition-colors"
                >
                  Cancelar reserva
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

// ─── Cancel Modal ─────────────────────────────────────────────────────────────

function CancelModal({ reservation, onKeep, onConfirm }: { reservation: Reservation; onKeep: () => void; onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[#111B30]/50 backdrop-blur-sm" onClick={onKeep} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-7">
        <div className="w-12 h-12 rounded-xl bg-[#FDEDEC] flex items-center justify-center mb-5">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M11 2L20 19H2L11 2Z" stroke="#C0392B" strokeWidth="1.8" strokeLinejoin="round" />
            <path d="M11 9v4" stroke="#C0392B" strokeWidth="1.8" strokeLinecap="round" />
            <circle cx="11" cy="15.5" r="0.8" fill="#C0392B" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-[#111B30] mb-1">¿Cancelar esta reserva?</h2>
        <p className="text-sm text-[#6B7A99] mb-5">Esta acción liberará el espacio para otros estudiantes.</p>
        <div className="bg-[#F4F6FA] rounded-xl p-4 mb-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl shadow-sm flex-shrink-0">{reservation.sportIcon}</div>
          <div>
            <p className="text-sm font-semibold text-[#111B30]">{reservation.court}</p>
            <p className="text-xs text-[#6B7A99] mt-0.5">{reservation.date} · {reservation.time}</p>
          </div>
        </div>
        <div className="flex items-start gap-2.5 bg-[#FEF0DC] rounded-xl p-3.5 mb-6">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="mt-0.5 flex-shrink-0">
            <circle cx="8" cy="8" r="7" stroke="#D4720A" strokeWidth="1.4" />
            <path d="M8 5v3" stroke="#D4720A" strokeWidth="1.4" strokeLinecap="round" />
            <circle cx="8" cy="10.5" r="0.6" fill="#D4720A" />
          </svg>
          <p className="text-xs text-[#8A5A0A] font-medium leading-relaxed">
            Esto liberará el espacio para otros estudiantes. No podrás deshacer esta acción.
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={onKeep} className="flex-1 py-2.5 border border-[#D0D6E8] text-[#111B30] text-sm font-semibold rounded-xl hover:bg-[#F4F6FA] transition-colors">
            Mantener reserva
          </button>
          <button onClick={onConfirm} className="flex-1 py-2.5 bg-[#C0392B] text-white text-sm font-semibold rounded-xl hover:bg-[#a82e21] transition-colors">
            Confirmar cancelación
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Booking Screen ───────────────────────────────────────────────────────────

type BookingStep = "filter" | "confirm" | "done";

function BookScreen({ courts, onNavigate, onBooked }: {
  courts: Court[];
  onNavigate: (s: Screen) => void;
  onBooked: (r: Reservation) => void;
}) {
  const [selectedDay, setSelectedDay] = useState(DAYS[0].key);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [selectedCourt, setSelectedCourt] = useState<Court | null>(null);
  const [step, setStep] = useState<BookingStep>("filter");
  const [statusByCourt, setStatusByCourt] = useState<Record<number, "available" | "reserved">>({});
  const [loadingAvailability, setLoadingAvailability] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [waitlistJoined, setWaitlistJoined] = useState<Record<number, number>>({}); // courtId -> queue_position

  const dayInfo = DAYS.find(d => d.key === selectedDay)!;

  // HU1/HU3 — fetch real availability for every court as soon as a slot is chosen.
  useEffect(() => {
    if (!selectedSlot) {
      setStatusByCourt({});
      return;
    }
    const { start, end } = slotToTimes(selectedSlot);
    setLoadingAvailability(true);
    api
      .listCourts({ date: selectedDay, start_time: start, end_time: end })
      .then(list => {
        const map: Record<number, "available" | "reserved"> = {};
        list.forEach(c => { map[c.id] = c.status || "available"; });
        setStatusByCourt(map);
      })
      .catch(() => setStatusByCourt({}))
      .finally(() => setLoadingAvailability(false));
  }, [selectedDay, selectedSlot]);

  const handleSelectSlot = (court: Court) => {
    if (statusByCourt[court.id] === "reserved") return;
    setSelectedCourt(court);
    setConfirmError(null);
    setStep("confirm");
  };

  const handleConfirmBook = async () => {
    if (!selectedCourt || !selectedSlot || submitting) return;
    const { start, end } = slotToTimes(selectedSlot);
    setSubmitting(true);
    setConfirmError(null);
    try {
      const reservation = await api.createReservation({
        court: selectedCourt.id,
        reservation_date: selectedDay,
        start_time: start,
        end_time: end,
      });
      onBooked(toUiReservation(reservation));
      setStep("done");
    } catch (err) {
      if (err instanceof api.ApiError && err.status === 409) {
        setConfirmError("Justo se acaba de reservar por otro estudiante. Puedes unirte a la lista de espera.");
      } else {
        setConfirmError("No se pudo completar la reserva. Intenta de nuevo.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleJoinWaitlist = async (court: Court) => {
    if (!selectedSlot) return;
    const { start, end } = slotToTimes(selectedSlot);
    try {
      const entry = await api.joinWaitlist({
        court: court.id,
        reservation_date: selectedDay,
        start_time: start,
        end_time: end,
      });
      setWaitlistJoined(prev => ({ ...prev, [court.id]: entry.queue_position }));
    } catch {
      // If already queued or another conflict, silently ignore — button will
      // simply not switch to the "joined" state.
    }
  };

  if (step === "done" && selectedCourt && selectedSlot) {
    return (
      <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
        <main className="max-w-2xl mx-auto px-6 py-16 flex flex-col items-center text-center">
          <div className="w-20 h-20 rounded-full bg-[#E8F6EE] flex items-center justify-center mb-6">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <path d="M8 18l6 6 14-14" stroke="#1A8A4A" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[#111B30] mb-2">¡Reserva confirmada!</h1>
          <p className="text-sm text-[#6B7A99] mb-8">{selectedCourt.name} · {dayInfo.full} · {selectedSlot}</p>
          <div className="flex gap-3">
            <button onClick={() => onNavigate("my-reservations")} className="px-5 py-2.5 text-white text-sm font-semibold rounded-xl transition-colors" style={{ background: A }}
              onMouseEnter={e => (e.currentTarget.style.background = AH)}
              onMouseLeave={e => (e.currentTarget.style.background = A)}
            >
              Ver mis reservas
            </button>
            <button onClick={() => { setStep("filter"); setSelectedCourt(null); setSelectedSlot(null); }}
              className="px-5 py-2.5 border border-[#D0D6E8] text-[#111B30] text-sm font-semibold rounded-xl hover:bg-[#F4F6FA] transition-colors"
            >
              Reservar otra
            </button>
          </div>
        </main>
      </div>
    );
  }

  if (step === "confirm" && selectedCourt && selectedSlot) {
    return (
      <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
        <main className="max-w-2xl mx-auto px-6 py-10">
          <button onClick={() => { setStep("filter"); setConfirmError(null); }} className="flex items-center gap-1.5 text-sm text-[#6B7A99] hover:text-[#111B30] mb-6 transition-colors">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
            Volver
          </button>
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Confirmar reserva</p>
          <h1 className="text-3xl font-bold text-[#111B30] mb-8">Resumen</h1>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] overflow-hidden mb-6">
            <div className="relative h-44 bg-[#1B2A4A]">
              <img src={`https://images.unsplash.com/${selectedCourt.img}?w=800&h=400&fit=crop&auto=format`} alt={selectedCourt.name}
                className="w-full h-full object-cover opacity-60" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#111B30]/70 to-transparent" />
              <div className="absolute bottom-4 left-5">
                <h2 className="text-white text-xl font-bold">{selectedCourt.name}</h2>
                <p className="text-white/70 text-xs mt-0.5">{selectedCourt.location}</p>
              </div>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-2 gap-3 mb-5">
                {[
                  { label: "Fecha", value: dayInfo.full, icon: "📅" },
                  { label: "Horario", value: selectedSlot, icon: "🕐" },
                  { label: "Deporte", value: selectedCourt.sport, icon: selectedCourt.icon },
                  { label: "Capacidad", value: selectedCourt.capacity, icon: "👥" },
                ].map(item => (
                  <div key={item.label} className="bg-[#F4F6FA] rounded-xl p-3">
                    <p className="text-xs text-[#6B7A99] font-medium mb-0.5">{item.label}</p>
                    <p className="text-sm font-semibold text-[#111B30]">{item.icon} {item.value}</p>
                  </div>
                ))}
              </div>

              {confirmError && (
                <div className="bg-[#FEF0DC] rounded-xl p-3.5 mb-4">
                  <p className="text-xs text-[#8A5A0A] font-medium mb-2">{confirmError}</p>
                  <button
                    onClick={() => handleJoinWaitlist(selectedCourt)}
                    className="text-xs font-semibold underline"
                    style={{ color: ATXT }}
                  >
                    Unirme a la lista de espera
                  </button>
                </div>
              )}

              <div className="flex gap-3">
                <button onClick={() => { setStep("filter"); setConfirmError(null); }} className="flex-1 py-3 border border-[#D0D6E8] text-[#111B30] font-semibold text-sm rounded-xl hover:bg-[#F4F6FA] transition-colors">
                  Cancelar
                </button>
                <button onClick={handleConfirmBook} disabled={submitting} className="flex-1 py-3 text-white font-semibold text-sm rounded-xl transition-colors disabled:opacity-50" style={{ background: A }}
                  onMouseEnter={e => { if (!submitting) e.currentTarget.style.background = AH; }}
                  onMouseLeave={e => { if (!submitting) e.currentTarget.style.background = A; }}
                >
                  {submitting ? "Reservando…" : "Confirmar reserva"}
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Step: filter
  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Universidad EAFIT</p>
          <h1 className="text-3xl font-bold text-[#111B30]">Reservar cancha</h1>
          <p className="text-sm text-[#6B7A99] mt-1">Selecciona el día y horario que prefieras</p>
        </div>

        {/* Day selector */}
        <div className="bg-white rounded-2xl border border-[#E8ECF4] shadow-sm p-4 mb-5">
          <p className="text-xs font-semibold text-[#6B7A99] uppercase tracking-wider mb-3">Día</p>
          <div className="flex gap-2">
            {DAYS.map(d => (
              <button
                key={d.key}
                onClick={() => setSelectedDay(d.key)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all border"
                style={selectedDay === d.key
                  ? { background: A, color: "white", borderColor: A }
                  : { background: "#F4F6FA", color: "#6B7A99", borderColor: "#E8ECF4" }}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Time slot selector */}
        <div className="bg-white rounded-2xl border border-[#E8ECF4] shadow-sm p-4 mb-6">
          <p className="text-xs font-semibold text-[#6B7A99] uppercase tracking-wider mb-3">Horario</p>
          <div className="grid grid-cols-4 gap-2">
            {SLOTS.map(slot => (
              <button
                key={slot}
                onClick={() => setSelectedSlot(selectedSlot === slot ? null : slot)}
                className="py-2 rounded-xl text-xs font-semibold transition-all border"
                style={selectedSlot === slot
                  ? { background: A, color: "white", borderColor: A }
                  : { background: "#F4F6FA", color: "#6B7A99", borderColor: "#E8ECF4" }}
              >
                {slot.split(" – ")[0]}
              </button>
            ))}
          </div>
          {selectedSlot && (
            <p className="text-xs mt-3" style={{ color: A }}>
              Mostrando canchas para <strong>{selectedSlot}</strong> el {dayInfo.full}
            </p>
          )}
        </div>

        {/* Courts list */}
        <div>
          <p className="text-xs font-semibold text-[#6B7A99] uppercase tracking-wider mb-3">
            {selectedSlot ? "Disponibilidad para el horario seleccionado" : "Selecciona un horario para ver disponibilidad"}
          </p>

          {!selectedSlot ? (
            <div className="bg-white rounded-2xl border border-[#E8ECF4] p-10 flex flex-col items-center text-center">
              <p className="text-sm text-[#6B7A99]">Elige un horario arriba para ver qué canchas están disponibles.</p>
            </div>
          ) : loadingAvailability ? (
            <div className="bg-white rounded-2xl border border-[#E8ECF4] p-10 flex flex-col items-center text-center">
              <p className="text-sm text-[#6B7A99]">Consultando disponibilidad…</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {courts.map(court => {
                const status = statusByCourt[court.id];
                const queuePosition = waitlistJoined[court.id];

                return (
                  <div key={court.id} className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] overflow-hidden">
                    <div className="flex">
                      <div className="relative w-40 flex-shrink-0 bg-[#1B2A4A]">
                        <img src={`https://images.unsplash.com/${court.img}?w=300&h=200&fit=crop&auto=format`} alt={court.name}
                          className="w-full h-full object-cover opacity-60" />
                      </div>
                      <div className="flex-1 p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="text-lg">{court.icon}</span>
                              <h3 className="text-base font-bold text-[#111B30]">{court.name}</h3>
                            </div>
                            <p className="text-xs text-[#6B7A99]">{court.location} · {court.surface} · {court.capacity}</p>
                          </div>
                          {status === "reserved" && <StatusBadge type="reserved" />}
                          {status === "available" && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#EAF4FD]" style={{ color: ATXT }}>
                              <span className="w-1.5 h-1.5 rounded-full" style={{ background: A }} />Disponible
                            </span>
                          )}
                        </div>

                        {status === "available" ? (
                          <button onClick={() => handleSelectSlot(court)}
                            className="mt-3 px-4 py-2 text-white text-sm font-semibold rounded-xl transition-colors"
                            style={{ background: A }}
                            onMouseEnter={e => (e.currentTarget.style.background = AH)}
                            onMouseLeave={e => (e.currentTarget.style.background = A)}
                          >
                            Reservar este horario
                          </button>
                        ) : status === "reserved" ? (
                          queuePosition ? (
                            <div className="mt-3 inline-flex items-center gap-2 bg-[#E8F6EE] px-3 py-1.5 rounded-xl">
                              <div className="w-5 h-5 rounded-full bg-[#1A8A4A] flex items-center justify-center flex-shrink-0">
                                <span className="text-white font-bold text-xs">#{queuePosition}</span>
                              </div>
                              <p className="text-xs font-semibold text-[#1A8A4A]">En lista de espera · Posición #{queuePosition}</p>
                            </div>
                          ) : (
                            <button onClick={() => handleJoinWaitlist(court)}
                              className="mt-3 px-4 py-2 text-sm font-semibold rounded-xl border transition-colors border-[#D0D6E8] text-[#111B30] hover:bg-[#F4F6FA]"
                            >
                              Unirse a lista de espera
                            </button>
                          )
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ─── Waitlist Notification ────────────────────────────────────────────────────

function WaitlistNotificationScreen({ offer, onNavigate, onConfirmed, onDeclined }: {
  offer: ApiWaitlistEntry | null;
  onNavigate: (s: Screen) => void;
  onConfirmed: (r: Reservation) => void;
  onDeclined: () => void;
}) {
  const [confirmed, setConfirmed] = useState<boolean | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (!offer || confirming) return;
    setConfirming(true);
    setError(null);
    try {
      const reservation = await api.confirmWaitlistOffer(offer.id);
      onConfirmed(toUiReservation(reservation));
      setConfirmed(true);
    } catch {
      setError("No se pudo confirmar la reserva. Puede que la oferta ya haya expirado.");
    } finally {
      setConfirming(false);
    }
  };

  const handleDecline = () => {
    // There is no explicit "decline" endpoint: simply not confirming means
    // the offer will expire on its own and the system will automatically
    // notify the next student in the queue (HU8).
    setConfirmed(false);
    onDeclined();
  };

  if (!offer) {
    return (
      <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
        <main className="max-w-2xl mx-auto px-6 py-16 flex flex-col items-center text-center">
          <div className="text-3xl mb-3">🔔</div>
          <h1 className="text-xl font-bold text-[#111B30] mb-2">No tienes notificaciones</h1>
          <p className="text-sm text-[#6B7A99]">Cuando un cupo se libere en una lista de espera a la que te uniste, aparecerá aquí.</p>
        </main>
      </div>
    );
  }

  const meta = sportMeta(offer.court_detail.sport);

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      <main className="max-w-2xl mx-auto px-6 py-10">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Universidad EAFIT</p>
          <h1 className="text-3xl font-bold text-[#111B30]">Notificaciones</h1>
        </div>

        {confirmed === null ? (
          <div className="rounded-2xl p-4 flex items-center gap-4 mb-6 shadow-lg" style={{ background: "#1B2A4A" }}>
            <div className="relative flex-shrink-0">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: `${A}30` }}>
                <div className="w-4 h-4 rounded-full animate-pulse" style={{ background: A }} />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold text-sm">¡Un cupo disponible!</p>
              <p className="text-white/70 text-xs mt-0.5 truncate">{offer.court_detail.name} está disponible para ti ahora</p>
            </div>
          </div>
        ) : (
          <div className={`rounded-2xl p-4 flex items-center gap-4 mb-6 shadow-sm ${confirmed ? "bg-[#E8F6EE]" : "bg-white border border-[#E8ECF4]"}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${confirmed ? "bg-[#1A8A4A]" : "bg-[#D0D6E8]"}`}>
              {confirmed ? (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M4 9l3.5 3.5 6.5-7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M5 5l8 8M13 5l-8 8" stroke="white" strokeWidth="2" strokeLinecap="round" /></svg>
              )}
            </div>
            <div>
              <p className={`font-semibold text-sm ${confirmed ? "text-[#1A8A4A]" : "text-[#111B30]"}`}>
                {confirmed ? "¡Reserva confirmada!" : "Cupo declinado"}
              </p>
              <p className={`text-xs mt-0.5 ${confirmed ? "text-[#1A8A4A]/80" : "text-[#6B7A99]"}`}>
                {confirmed ? `Tu reserva en ${offer.court_detail.name} está activa` : "El cupo pasará al siguiente estudiante en la lista"}
              </p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] overflow-hidden">
          <div className="relative h-44 bg-[#1B2A4A]">
            <img src={`https://images.unsplash.com/${offer.court_detail.image_ref}?w=800&h=400&fit=crop&auto=format`} alt={offer.court_detail.name}
              className="w-full h-full object-cover opacity-60" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#111B30]/70 to-transparent" />
            <div className="absolute bottom-4 left-5 right-5">
              <p className="text-white/70 text-xs font-medium mb-1">Cupo disponible</p>
              <h2 className="text-white text-xl font-bold">{offer.court_detail.name}</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-3 mb-6">
              {[
                { label: "Fecha", value: offer.reservation_date, icon: "📅" },
                { label: "Horario", value: `${offer.start_time.slice(0, 5)} – ${offer.end_time.slice(0, 5)}`, icon: "🕐" },
                { label: "Deporte", value: meta.label, icon: meta.icon },
                { label: "Ubicación", value: offer.court_detail.location, icon: "📍" },
              ].map(item => (
                <div key={item.label} className="bg-[#F4F6FA] rounded-xl p-3">
                  <p className="text-xs text-[#6B7A99] font-medium mb-0.5">{item.label}</p>
                  <p className="text-sm font-semibold text-[#111B30]">{item.icon} {item.value}</p>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3 bg-[#F4F6FA] rounded-xl p-3.5 mb-6">
              <div className="w-9 h-9 rounded-full bg-[#1B2A4A] flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">#{offer.queue_position}</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-[#111B30]">Eras #{offer.queue_position} en la lista de espera</p>
                <p className="text-xs text-[#6B7A99] mt-0.5">El cupo es tuyo — confirma antes de que expire</p>
              </div>
            </div>
            {error && <p className="text-xs text-[#C0392B] mb-4">{error}</p>}
            {confirmed === null ? (
              <div className="flex gap-3">
                <button onClick={handleDecline} className="flex-1 py-3 border border-[#D0D6E8] text-[#111B30] font-semibold text-sm rounded-xl hover:bg-[#F4F6FA] transition-colors">
                  Declinar
                </button>
                <button onClick={handleConfirm} disabled={confirming} className="flex-1 py-3 text-white font-semibold text-sm rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-50" style={{ background: A }}
                  onMouseEnter={e => { if (!confirming) e.currentTarget.style.background = AH; }}
                  onMouseLeave={e => { if (!confirming) e.currentTarget.style.background = A; }}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8l3.5 3.5 6.5-7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  {confirming ? "Confirmando…" : "Confirmar reserva"}
                </button>
              </div>
            ) : (
              <button onClick={() => onNavigate("my-reservations")} className="w-full py-3 bg-[#1B2A4A] text-white font-semibold text-sm rounded-xl hover:bg-[#2a3f6b] transition-colors">
                Ver mis reservas
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState<Screen>("login");
  const [checkingSession, setCheckingSession] = useState(true);
  const [userName, setUserName] = useState("");
  const [modal, setModal] = useState<ModalType>(null);
  const [cancelTarget, setCancelTarget] = useState<Reservation | null>(null);

  const [courts, setCourts] = useState<Court[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [reservationsLoading, setReservationsLoading] = useState(false);
  const [waitlistOffer, setWaitlistOffer] = useState<ApiWaitlistEntry | null>(null);

  const loadAppData = async () => {
    setReservationsLoading(true);
    try {
      const [user, courtList, myReservations, myWaitlist] = await Promise.all([
        api.me(),
        api.listCourts(),
        api.myReservations(),
        api.myWaitlist(),
      ]);
      setUserName(`${user.first_name} ${user.last_name}`.trim() || user.email);
      setCourts(courtList.map(toUiCourt));
      setReservations(
        myReservations.filter(r => r.status === "confirmed").map(toUiReservation)
      );
      const notified = myWaitlist.find(w => w.status === "notified");
      setWaitlistOffer(notified || null);
    } finally {
      setReservationsLoading(false);
    }
  };

  // On first load, if a token is already stored, try to resume the session.
  useEffect(() => {
    if (!api.getToken()) {
      setCheckingSession(false);
      return;
    }
    loadAppData()
      .then(() => setScreen("home"))
      .catch(() => api.setToken(null))
      .finally(() => setCheckingSession(false));
  }, []);

  const handleLogin = async () => {
    await loadAppData();
    setScreen("home");
  };

  const handleCancelClick = (r: Reservation) => {
    setCancelTarget(r);
    setModal("cancel");
  };

  const handleConfirmCancel = async () => {
    if (!cancelTarget) return;
    try {
      await api.cancelReservation(cancelTarget.id);
      setReservations(prev => prev.filter(r => r.id !== cancelTarget.id));
      // A cancellation may have triggered a waiting-list notification for
      // someone else, but it could also affect *this* student if they were
      // waiting on a different slot that just opened up — refresh in the background.
      api.myWaitlist().then(list => {
        const notified = list.find(w => w.status === "notified");
        setWaitlistOffer(notified || null);
      });
    } finally {
      setModal(null);
      setCancelTarget(null);
    }
  };

  const handleBooked = (r: Reservation) => {
    setReservations(prev => [...prev, r]);
    setWaitlistOffer(null);
  };

  const handleWaitlistDeclined = () => {
    setWaitlistOffer(null);
  };

  if (checkingSession) {
    return <div className="size-full flex items-center justify-center bg-[#F4F6FA] text-sm text-[#6B7A99]">Cargando…</div>;
  }

  if (screen === "login") return <LoginScreen onLogin={handleLogin} />;

  return (
    <div className="size-full flex flex-col" style={{ fontFamily: "Inter, sans-serif" }}>
      <Navbar onNavigate={setScreen} active={screen} userName={userName} />

      {screen === "home" && <HomeScreen onNavigate={setScreen} reservations={reservations} userName={userName} />}
      {screen === "my-reservations" && (
        <MyReservationsScreen onNavigate={setScreen} reservations={reservations} onCancel={handleCancelClick} loading={reservationsLoading} />
      )}
      {screen === "book" && <BookScreen courts={courts} onNavigate={setScreen} onBooked={handleBooked} />}
      {screen === "waitlist-notification" && (
        <WaitlistNotificationScreen
          offer={waitlistOffer}
          onNavigate={setScreen}
          onConfirmed={handleBooked}
          onDeclined={handleWaitlistDeclined}
        />
      )}

      {modal === "cancel" && cancelTarget && (
        <CancelModal
          reservation={cancelTarget}
          onKeep={() => { setModal(null); setCancelTarget(null); }}
          onConfirm={handleConfirmCancel}
        />
      )}
    </div>
  );
}
