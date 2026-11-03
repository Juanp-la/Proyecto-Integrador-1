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

// Local YYYY-MM-DD (toISOString() is UTC: after 7 pm in Colombia it returns tomorrow).
function localIsoDate(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function todayLabel() {
  const d = new Date();
  const weekdays = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
  const semester = d.getMonth() < 6 ? "1" : "2";
  return `${weekdays[d.getDay()]}, ${d.getDate()} de ${MONTH_LABELS[d.getMonth()]} de ${d.getFullYear()} · Semestre ${d.getFullYear()}-${semester}`;
}

// A reservation is "active" until its end time has passed (one active reservation at a time).
function isActiveReservation(r: { date: string; time: string }) {
  const today = localIsoDate(new Date());
  if (r.date > today) return true;
  if (r.date < today) return false;
  const end = r.time.split(" – ")[1] || "00:00";
  const now = new Date();
  const nowHHMM = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  return end > nowHHMM;
}

function buildDays() {
  const days = [];
  const today = new Date();
  for (let i = 0; i < 6; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const iso = localIsoDate(d); // YYYY-MM-DD
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

function Navbar({ onNavigate, active, userName, onLogout, notificationCount }: {
  onNavigate: (s: Screen) => void;
  active: Screen;
  userName: string;
  onLogout: () => void;
  notificationCount: number;
}) {
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
        <div className="relative">
          {link("waitlist-notification", "Notificaciones")}
          {notificationCount > 0 && (
            <span className="absolute -top-2 -right-4 min-w-[18px] h-[18px] px-1 rounded-full bg-[#C0392B] text-white text-[10px] font-bold flex items-center justify-center">
              {notificationCount}
            </span>
          )}
        </div>
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-sm"
          style={{ background: A }}
          title={userName}
        >
          {initials || "?"}
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white/70 border border-white/20 hover:text-white hover:border-white/50 transition-colors cursor-pointer"
          title="Cerrar sesión"
        >
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
            <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M10.5 11.5L14 8l-3.5-3.5M14 8H6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Salir
        </button>
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

// ─── AI widgets (weather + recommendations) ───────────────────────────────────

function AiBadge({ source }: { source: api.AiSource }) {
  return source === "ai" ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ background: ABG, color: ATXT }}>
      ✨ Generado con IA
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#F4F6FA] text-[#6B7A99]">
      Calculado con datos de uso
    </span>
  );
}

function formatShortDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return `${WEEKDAY_LABELS[date.getDay()]} ${d} de ${MONTH_LABELS[m - 1]}`;
}

function WidgetMessage({ text }: { text: string }) {
  return (
    <div className="bg-white rounded-2xl border border-[#E8ECF4] p-6 text-center">
      <p className="text-sm text-[#6B7A99]">{text}</p>
    </div>
  );
}

function WeatherCard({ report, loading }: { report: api.WeatherReport | null; loading: boolean }) {
  if (loading) return <WidgetMessage text="Consultando el clima de hoy…" />;
  if (!report || !report.available) return <WidgetMessage text="No se pudo consultar el clima en este momento." />;

  return (
    <div className="bg-white rounded-2xl border border-[#E8ECF4] shadow-sm p-5">
      <div className="flex items-start gap-4">
        <div className="text-5xl leading-none">{report.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-base font-bold text-[#111B30]">{report.condition}</p>
            <AiBadge source={report.source} />
          </div>
          <p className="text-xs text-[#6B7A99] mt-0.5">
            {report.temp_min}°C – {report.temp_max}°C · Lluvia hasta {report.precipitation_probability_max}%
          </p>
          <p className="text-sm text-[#111B30] mt-3 leading-relaxed">{report.summary}</p>
          {report.advice && <p className="text-xs text-[#6B7A99] mt-2">💡 {report.advice}</p>}
          {report.best_hours && report.best_hours.length > 0 && (
            <p className="text-xs mt-2" style={{ color: ATXT }}>
              Mejores horas para jugar afuera: <strong>{report.best_hours.join(", ")}</strong>
            </p>
          )}
        </div>
      </div>
      {report.hourly && report.hourly.length > 0 && (
        <div className="flex gap-1.5 mt-4 overflow-x-auto pb-1">
          {report.hourly.map(h => (
            <div
              key={h.hour}
              className="flex-shrink-0 w-14 rounded-xl py-2 flex flex-col items-center"
              style={{ background: h.bad ? "#FDEDEC" : "#F4F6FA" }}
            >
              <span className="text-[10px] font-semibold text-[#6B7A99]">{h.hour.slice(0, 2)}h</span>
              <span className="text-lg">{h.icon}</span>
              <span className="text-[11px] font-semibold text-[#111B30]">{Math.round(h.temperature)}°</span>
              <span className={`text-[10px] ${h.bad ? "text-[#C0392B] font-semibold" : "text-[#6B7A99]"}`}>💧{h.precipitation_probability}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PopularCourtsSection({ data, loading, onNavigate }: {
  data: api.Recommendations<api.PopularCourtItem> | null;
  loading: boolean;
  onNavigate: (s: Screen) => void;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-bold text-[#111B30]">🔥 Canchas más populares</h2>
        {data && <AiBadge source={data.source} />}
      </div>
      {data?.summary && <p className="text-xs text-[#6B7A99] mb-4">{data.summary}</p>}
      {loading ? (
        <WidgetMessage text="Analizando qué canchas se usan más…" />
      ) : !data || data.items.length === 0 ? (
        <WidgetMessage text={data?.summary || "Todavía no hay datos de uso suficientes."} />
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {data.items.map((item, i) => (
            <button
              key={item.court_id}
              onClick={() => onNavigate("book")}
              className="bg-white rounded-2xl border border-[#E8ECF4] p-4 text-left hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-[#FEF0DC] text-[#D4720A]">#{i + 1}</span>
                <span className="text-[11px] text-[#6B7A99] text-right">
                  {item.reservations} reservas{item.waitlist_joins > 0 && ` · ${item.waitlist_joins} en espera`}
                </span>
              </div>
              <p className="text-sm font-semibold text-[#111B30] leading-snug">{item.name}</p>
              <p className="text-xs text-[#6B7A99] mt-0.5">{sportMeta(item.sport_code).icon} {sportMeta(item.sport_code).label} · {item.location}</p>
              <p className="text-xs text-[#111B30] mt-2 leading-relaxed">{item.reason}</p>
              {item.peak_times.length > 0 && (
                <p className="text-[11px] mt-2 font-medium text-[#D4720A]">Horas pico: {item.peak_times.join(", ")}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function QuietSlotsSection({ data, loading, onPick }: {
  data: api.Recommendations<api.QuietSlotItem> | null;
  loading: boolean;
  onPick: (date: string, slot: string) => void;
}) {
  return (
    <div className="mb-10">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-bold text-[#111B30]">🍃 Canchas y horarios tranquilos</h2>
        {data && <AiBadge source={data.source} />}
      </div>
      <p className="text-xs text-[#6B7A99] mb-4">{data?.summary || "Horarios libres con poca gente en los próximos días."}</p>
      {loading ? (
        <WidgetMessage text="Buscando horarios poco usados…" />
      ) : !data || data.items.length === 0 ? (
        <WidgetMessage text="No encontramos horarios libres en los próximos días." />
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {data.items.map(item => (
            <div key={`${item.court_id}-${item.date}-${item.start_time}`} className="bg-white rounded-2xl border border-[#E8ECF4] p-4 flex flex-col">
              <p className="text-sm font-semibold text-[#111B30]">{sportMeta(item.sport_code).icon} {item.court_name}</p>
              <p className="text-xs text-[#6B7A99] mt-0.5">
                {formatShortDate(item.date)} · {item.start_time} – {item.end_time}
                {item.rain_probability !== null && ` · 💧${item.rain_probability}%`}
              </p>
              <p className="text-xs text-[#111B30] mt-2 leading-relaxed flex-1">{item.reason}</p>
              <button
                onClick={() => onPick(item.date, `${item.start_time} – ${item.end_time}`)}
                className="mt-3 self-start px-3 py-1.5 text-white text-xs font-semibold rounded-lg transition-colors"
                style={{ background: A }}
                onMouseEnter={e => (e.currentTarget.style.background = AH)}
                onMouseLeave={e => (e.currentTarget.style.background = A)}
              >
                Ver este horario
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Loads one AI endpoint when the component mounts.
function useAiData<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let alive = true;
    loader()
      .then(d => { if (alive) setData(d); })
      .catch(() => { if (alive) setData(null); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return { data, loading };
}

// ─── Home Screen ──────────────────────────────────────────────────────────────

function HomeScreen({ onNavigate, reservations, userName, onPickSlot }: {
  onNavigate: (s: Screen) => void;
  reservations: Reservation[];
  userName: string;
  onPickSlot: (date: string, slot: string) => void;
}) {
  const weather = useAiData(api.weatherToday);
  const popular = useAiData(api.popularCourts);
  const quiet = useAiData(api.quietSlots);
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
            {todayLabel()}
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

        {/* Weather (AI) */}
        <div className="mb-8">
          <h2 className="text-lg font-bold text-[#111B30] mb-4">🌦️ Clima de hoy en el campus</h2>
          <WeatherCard report={weather.data} loading={weather.loading} />
        </div>

        {/* AI recommendations */}
        <PopularCourtsSection data={popular.data} loading={popular.loading} onNavigate={onNavigate} />
        <QuietSlotsSection data={quiet.data} loading={quiet.loading} onPick={onPickSlot} />
      </div>
    </div>
  );
}

// ─── My Reservations ──────────────────────────────────────────────────────────

function MyReservationsScreen({ onNavigate, reservations, onCancel, loading, waitlist, onLeaveWaitlist }: {
  onNavigate: (s: Screen) => void;
  reservations: Reservation[];
  onCancel: (r: Reservation) => void;
  loading: boolean;
  waitlist: ApiWaitlistEntry[];
  onLeaveWaitlist: (entry: ApiWaitlistEntry) => Promise<void>;
}) {
  const [leavingId, setLeavingId] = useState<number | null>(null);
  const [leaveError, setLeaveError] = useState<string | null>(null);

  const leave = async (entry: ApiWaitlistEntry) => {
    setLeavingId(entry.id);
    setLeaveError(null);
    try {
      await onLeaveWaitlist(entry);
    } catch (err) {
      setLeaveError(err instanceof api.ApiError ? err.message : "No se pudo salir de la lista de espera.");
    } finally {
      setLeavingId(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Universidad EAFIT</p>
          <h1 className="text-3xl font-bold text-[#111B30]">Mis reservas</h1>
          <p className="text-sm text-[#6B7A99] mt-1">{reservations.length} reserva{reservations.length !== 1 ? "s" : ""} activa{reservations.length !== 1 ? "s" : ""}</p>
          <p className="text-xs text-[#6B7A99] mt-1">Recuerda: solo puedes tener una reserva activa a la vez.</p>
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

        {/* Waiting lists */}
        <div className="mt-10">
          <h2 className="text-lg font-bold text-[#111B30] mb-1">Mis listas de espera</h2>
          <p className="text-sm text-[#6B7A99] mb-4">
            {waitlist.length === 0 ? "No estás en ninguna lista de espera." : "Te avisaremos en Notificaciones si se libera un cupo."}
          </p>
          {leaveError && <p className="text-xs text-[#C0392B] mb-3">{leaveError}</p>}
          <div className="flex flex-col gap-3">
            {waitlist.map(w => {
              const meta = sportMeta(w.court_detail.sport);
              return (
                <div key={w.id} className="bg-white rounded-2xl shadow-sm border border-[#E8ECF4] p-4 flex items-center gap-4">
                  <div className="w-11 h-11 rounded-full bg-[#1B2A4A] flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-bold text-sm">#{w.queue_position}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      {w.status === "notified" ? (
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: ABG, color: ATXT }}>¡Cupo disponible!</span>
                      ) : (
                        <StatusBadge type="waitlist" />
                      )}
                      <span className="text-xs text-[#6B7A99]">{meta.icon} {meta.label}</span>
                    </div>
                    <p className="text-sm font-semibold text-[#111B30] truncate">{w.court_detail.name}</p>
                    <p className="text-xs text-[#6B7A99] mt-0.5">
                      {w.reservation_date} · {w.start_time.slice(0, 5)} – {w.end_time.slice(0, 5)}
                    </p>
                  </div>
                  <button
                    onClick={() => leave(w)}
                    disabled={leavingId === w.id}
                    className="flex-shrink-0 px-4 py-2 border border-[#D0D6E8] text-[#111B30] text-sm font-medium rounded-xl hover:bg-[#F4F6FA] transition-colors disabled:opacity-50"
                  >
                    {leavingId === w.id ? "Saliendo…" : "Salir de la lista"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
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

function BookScreen({ courts, onNavigate, onBooked, activeReservation, initialDay, initialSlot }: {
  courts: Court[];
  onNavigate: (s: Screen) => void;
  onBooked: (r: Reservation) => void;
  activeReservation: Reservation | null;
  initialDay?: string;
  initialSlot?: string;
}) {
  const [selectedDay, setSelectedDay] = useState(
    initialDay && DAYS.some(d => d.key === initialDay) ? initialDay : DAYS[0].key
  );
  const [selectedSlot, setSelectedSlot] = useState<string | null>(
    initialSlot && SLOTS.includes(initialSlot) ? initialSlot : null
  );
  const [waitlistError, setWaitlistError] = useState<string | null>(null);
  const [slotTaken, setSlotTaken] = useState(false); // confirm failed because someone else booked it
  const blocked = !!activeReservation;
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
    if (statusByCourt[court.id] === "reserved" || blocked) return;
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
      setSlotTaken(false);
      if (err instanceof api.ApiError && err.code === "active_reservation_exists") {
        setConfirmError(err.message);
      } else if (err instanceof api.ApiError && err.status === 409) {
        setSlotTaken(true);
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
      setWaitlistError(null);
    } catch (err) {
      setWaitlistError(err instanceof api.ApiError ? err.message : "No se pudo unir a la lista de espera.");
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
                  {slotTaken && (
                    <button
                      onClick={() => handleJoinWaitlist(selectedCourt)}
                      className="text-xs font-semibold underline"
                      style={{ color: ATXT }}
                    >
                      Unirme a la lista de espera
                    </button>
                  )}
                  {waitlistError && <p className="text-xs text-[#C0392B] mt-2">{waitlistError}</p>}
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

        {activeReservation && (
          <div className="flex items-start gap-3 bg-[#FEF0DC] rounded-2xl p-4 mb-5">
            <span className="text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-[#8A5A0A]">Ya tienes una reserva activa</p>
              <p className="text-xs text-[#8A5A0A] mt-0.5">
                {activeReservation.court} · {activeReservation.date} · {activeReservation.time}. Solo puedes reservar una cancha a la vez:
                cancélala o espera a que termine para hacer otra.
              </p>
            </div>
            <button
              onClick={() => onNavigate("my-reservations")}
              className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold rounded-lg border border-[#D4720A]/40 text-[#8A5A0A] hover:bg-white/50"
            >
              Ver mi reserva
            </button>
          </div>
        )}

        {waitlistError && (
          <div className="bg-[#FDEDEC] rounded-xl p-3 mb-5">
            <p className="text-xs text-[#C0392B] font-medium">{waitlistError}</p>
          </div>
        )}

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
                            disabled={blocked}
                            title={blocked ? "Ya tienes una reserva activa" : undefined}
                            className="mt-3 px-4 py-2 text-white text-sm font-semibold rounded-xl transition-colors disabled:cursor-not-allowed"
                            style={{ background: blocked ? "#A0AABF" : A }}
                            onMouseEnter={e => { if (!blocked) e.currentTarget.style.background = AH; }}
                            onMouseLeave={e => { if (!blocked) e.currentTarget.style.background = A; }}
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
                              disabled={blocked}
                              className="mt-3 px-4 py-2 text-sm font-semibold rounded-xl border transition-colors border-[#D0D6E8] text-[#111B30] hover:bg-[#F4F6FA] disabled:opacity-40 disabled:cursor-not-allowed"
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

function WaitlistOfferCard({ offer, onNavigate, onConfirmed, onDeclined }: {
  offer: ApiWaitlistEntry;
  onNavigate: (s: Screen) => void;
  onConfirmed: (r: Reservation) => void;
  onDeclined: () => Promise<void>;
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
    } catch (err) {
      setError(
        err instanceof api.ApiError && err.status === 409
          ? err.message
          : "No se pudo confirmar la reserva. Puede que la oferta ya haya expirado."
      );
    } finally {
      setConfirming(false);
    }
  };

  const handleDecline = async () => {
    // Declining = leaving the waiting list: the spot goes right away to the
    // next student in the queue (instead of waiting for the offer to expire).
    try {
      await onDeclined();
      setConfirmed(false);
    } catch (err) {
      setError(err instanceof api.ApiError ? err.message : "No se pudo declinar el cupo.");
    }
  };

  const meta = sportMeta(offer.court_detail.sport);

  return (
    <div className="mb-8">

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
    </div>
  );
}

function WeatherAlertCard({ alert, onCancel, onKeep }: {
  alert: api.ApiNotification;
  onCancel: (n: api.ApiNotification) => Promise<void>;
  onKeep: (n: api.ApiNotification) => Promise<void>;
}) {
  const [busy, setBusy] = useState<"cancel" | "keep" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const r = alert.reservation_detail;

  const run = async (kind: "cancel" | "keep") => {
    setBusy(kind);
    setError(null);
    try {
      await (kind === "cancel" ? onCancel(alert) : onKeep(alert));
    } catch (err) {
      setError(err instanceof api.ApiError ? err.message : "Algo salió mal. Intenta de nuevo.");
      setBusy(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border-2 border-[#F5C6C0] overflow-hidden mb-4">
      <div className="bg-[#FDEDEC] px-5 py-3 flex items-center gap-3">
        <span className="text-2xl">{alert.data.icon || "⛈️"}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-[#8B1E14]">Alerta de mal clima</p>
          <p className="text-xs text-[#8B1E14]/80 truncate">{alert.title.replace(/^\S+\s/, "")}</p>
        </div>
        {alert.data.source && <AiBadge source={alert.data.source} />}
      </div>
      <div className="p-5">
        <p className="text-sm text-[#111B30] leading-relaxed mb-4">{alert.message}</p>
        {r && (
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              { label: "Cancha", value: r.court_detail.name },
              { label: "Fecha", value: r.reservation_date },
              { label: "Horario", value: `${r.start_time.slice(0, 5)} – ${r.end_time.slice(0, 5)}` },
            ].map(i => (
              <div key={i.label} className="bg-[#F4F6FA] rounded-xl p-2.5">
                <p className="text-[11px] text-[#6B7A99]">{i.label}</p>
                <p className="text-xs font-semibold text-[#111B30] truncate">{i.value}</p>
              </div>
            ))}
          </div>
        )}
        {error && <p className="text-xs text-[#C0392B] mb-3">{error}</p>}
        <div className="flex gap-3">
          <button
            onClick={() => run("keep")}
            disabled={!!busy}
            className="flex-1 py-2.5 border border-[#D0D6E8] text-[#111B30] text-sm font-semibold rounded-xl hover:bg-[#F4F6FA] transition-colors disabled:opacity-50"
          >
            {busy === "keep" ? "Guardando…" : "Mantener reserva"}
          </button>
          <button
            onClick={() => run("cancel")}
            disabled={!!busy}
            className="flex-1 py-2.5 bg-[#C0392B] text-white text-sm font-semibold rounded-xl hover:bg-[#a82e21] transition-colors disabled:opacity-50"
          >
            {busy === "cancel" ? "Cancelando…" : "Cancelar reserva"}
          </button>
        </div>
      </div>
    </div>
  );
}

function NotificationsScreen({ offer, alerts, onNavigate, onConfirmed, onDeclined, onCancelFromAlert, onDismissAlert }: {
  offer: ApiWaitlistEntry | null;
  alerts: api.ApiNotification[];
  onNavigate: (s: Screen) => void;
  onConfirmed: (r: Reservation) => void;
  onDeclined: (entry: ApiWaitlistEntry) => Promise<void>;
  onCancelFromAlert: (n: api.ApiNotification) => Promise<void>;
  onDismissAlert: (n: api.ApiNotification) => Promise<void>;
}) {
  const weather = useAiData(api.weatherToday);
  // Keep the offer card mounted after confirming/declining so its result message stays visible.
  const [shownOffer, setShownOffer] = useState<ApiWaitlistEntry | null>(offer);
  useEffect(() => { if (offer) setShownOffer(offer); }, [offer]);

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4F6FA]">
      <main className="max-w-2xl mx-auto px-6 py-10">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: A }}>Universidad EAFIT</p>
          <h1 className="text-3xl font-bold text-[#111B30]">Notificaciones</h1>
        </div>

        {alerts.map(a => (
          <WeatherAlertCard key={a.id} alert={a} onCancel={onCancelFromAlert} onKeep={onDismissAlert} />
        ))}

        {shownOffer && (
          <WaitlistOfferCard
            offer={shownOffer}
            onNavigate={onNavigate}
            onConfirmed={onConfirmed}
            onDeclined={() => onDeclined(shownOffer)}
          />
        )}

        {alerts.length === 0 && !shownOffer && (
          <div className="bg-white rounded-2xl border border-[#E8ECF4] p-10 flex flex-col items-center text-center mb-8">
            <div className="text-3xl mb-3">🔔</div>
            <h2 className="text-lg font-bold text-[#111B30] mb-1">No tienes notificaciones</h2>
            <p className="text-sm text-[#6B7A99]">
              Aquí verás cupos liberados de tus listas de espera y alertas de mal clima para tus reservas en canchas al aire libre.
            </p>
          </div>
        )}

        <h2 className="text-lg font-bold text-[#111B30] mb-4">🌦️ Reporte del clima de hoy</h2>
        <WeatherCard report={weather.data} loading={weather.loading} />
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
  const [waitlist, setWaitlist] = useState<ApiWaitlistEntry[]>([]);
  const [alerts, setAlerts] = useState<api.ApiNotification[]>([]);
  // Pre-selected day/slot when coming from a "quiet slot" recommendation.
  const [bookPreset, setBookPreset] = useState<{ day: string; slot: string } | null>(null);

  const waitlistOffer = waitlist.find(w => w.status === "notified") || null;
  const activeReservations = reservations.filter(isActiveReservation);
  const activeReservation = activeReservations[0] || null;

  const refreshWaitlist = () =>
    api.myWaitlist().then(setWaitlist).catch(() => undefined);

  // Weather alerts are generated by the backend when this is called.
  const refreshAlerts = () =>
    api.myNotifications().then(setAlerts).catch(() => undefined);

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
      setWaitlist(myWaitlist);
      refreshAlerts(); // in the background — it may take a moment (forecast + AI)
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

  // While logged in, check waiting lists and weather alerts every 2 minutes.
  useEffect(() => {
    if (screen === "login") return;
    const id = setInterval(() => { refreshWaitlist(); refreshAlerts(); }, 2 * 60 * 1000);
    return () => clearInterval(id);
  }, [screen === "login"]);

  const navigate = (s: Screen) => {
    if (s !== "book") setBookPreset(null);
    if (s === "my-reservations") refreshWaitlist();
    if (s === "waitlist-notification") { refreshWaitlist(); refreshAlerts(); }
    setScreen(s);
  };

  const handleLogin = async () => {
    await loadAppData();
    setScreen("home");
  };

  const handleLogout = () => {
    api.logout();
    setUserName("");
    setCourts([]);
    setReservations([]);
    setWaitlist([]);
    setAlerts([]);
    setBookPreset(null);
    setModal(null);
    setCancelTarget(null);
    setScreen("login");
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
      setAlerts(prev => prev.filter(a => a.reservation !== cancelTarget.id));
      // A cancellation may have triggered a waiting-list notification for
      // someone else, but it could also affect *this* student if they were
      // waiting on a different slot that just opened up — refresh in the background.
      refreshWaitlist();
    } finally {
      setModal(null);
      setCancelTarget(null);
    }
  };

  const handleBooked = (r: Reservation) => {
    setReservations(prev => [...prev, r]);
    refreshWaitlist();
    refreshAlerts();
  };

  const handleLeaveWaitlist = async (entry: ApiWaitlistEntry) => {
    await api.leaveWaitlist(entry.id);
    setWaitlist(prev => prev.filter(w => w.id !== entry.id));
    refreshWaitlist(); // queue positions of my other entries don't change, but stay in sync
  };

  const handleCancelFromAlert = async (n: api.ApiNotification) => {
    await api.cancelReservationFromNotification(n.id);
    setAlerts(prev => prev.filter(a => a.id !== n.id));
    setReservations(prev => prev.filter(r => r.id !== n.reservation));
    refreshWaitlist();
  };

  const handleDismissAlert = async (n: api.ApiNotification) => {
    await api.dismissNotification(n.id);
    setAlerts(prev => prev.filter(a => a.id !== n.id));
  };

  const handlePickSlot = (day: string, slot: string) => {
    setBookPreset({ day, slot });
    setScreen("book");
  };

  if (checkingSession) {
    return <div className="size-full flex items-center justify-center bg-[#F4F6FA] text-sm text-[#6B7A99]">Cargando…</div>;
  }

  if (screen === "login") return <LoginScreen onLogin={handleLogin} />;

  return (
    <div className="size-full flex flex-col" style={{ fontFamily: "Inter, sans-serif" }}>
      <Navbar
        onNavigate={navigate}
        active={screen}
        userName={userName}
        onLogout={handleLogout}
        notificationCount={alerts.length + (waitlistOffer ? 1 : 0)}
      />

      {screen === "home" && (
        <HomeScreen onNavigate={navigate} reservations={activeReservations} userName={userName} onPickSlot={handlePickSlot} />
      )}
      {screen === "my-reservations" && (
        <MyReservationsScreen
          onNavigate={navigate}
          reservations={activeReservations}
          onCancel={handleCancelClick}
          loading={reservationsLoading}
          waitlist={waitlist}
          onLeaveWaitlist={handleLeaveWaitlist}
        />
      )}
      {screen === "book" && (
        <BookScreen
          key={bookPreset ? `${bookPreset.day}-${bookPreset.slot}` : "default"}
          courts={courts}
          onNavigate={navigate}
          onBooked={handleBooked}
          activeReservation={activeReservation}
          initialDay={bookPreset?.day}
          initialSlot={bookPreset?.slot}
        />
      )}
      {screen === "waitlist-notification" && (
        <NotificationsScreen
          offer={waitlistOffer}
          alerts={alerts}
          onNavigate={navigate}
          onConfirmed={handleBooked}
          onDeclined={handleLeaveWaitlist}
          onCancelFromAlert={handleCancelFromAlert}
          onDismissAlert={handleDismissAlert}
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
