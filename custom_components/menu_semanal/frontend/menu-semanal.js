/*
 * Menú Semanal – planificador de comidas y cenas para Home Assistant, enlazado con Despensa y Cesta.
 * Define <menu-semanal-panel> (panel de la barra lateral) y <menu-semanal-card> (tarjeta).
 * Sin dependencias: un único módulo que sirve la integración.
 */
const MS_VERSION = "1.0.0";

/* ------------------------------------------------------------ utilidades */
const P = {
  menu: "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z",
  cog: "M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",
  close: "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",
  search: "M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  minus: "M19,13H5V11H19V13Z",
  check: "M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z",
  left: "M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",
  right: "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",
  chevron: "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
  swap: "M21,9L17,5V8H10V10H17V13M7,11L3,15L7,19V16H14V14H7V11Z",
  wand: "M7.5,5.6L5,7L6.4,4.5L5,2L7.5,3.4L10,2L8.6,4.5L10,7L7.5,5.6M19.5,15.4L22,14L20.6,16.5L22,19L19.5,17.6L17,19L18.4,16.5L17,14L19.5,15.4M22,2L20.6,4.5L22,7L19.5,5.6L17,7L18.4,4.5L17,2L19.5,3.4L22,2M13.34,12.78L15.78,10.34L13.66,8.22L11.22,10.66L13.34,12.78M14.37,7.29L16.71,9.63C17.1,10 17.1,10.65 16.71,11.04L5.04,22.71C4.65,23.1 4,23.1 3.63,22.71L1.29,20.37C0.9,20 0.9,19.35 1.29,18.96L12.96,7.29C13.35,6.9 14,6.9 14.37,7.29Z",
  cartCheck: "M9 20C9 21.1 8.1 22 7 22S5 21.1 5 20 5.9 18 7 18 9 18.9 9 20M17 18C15.9 18 15 18.9 15 20S15.9 22 17 22 19 21.1 19 20 18.1 18 17 18M7.2 14.8V14.7L8.1 13H15.5C16.2 13 16.9 12.6 17.2 12L21.1 5L19.4 4L15.5 11H8.5L4.3 2H1V4H3L6.6 11.6L5.2 14C5.1 14.3 5 14.6 5 15C5 16.1 5.9 17 7 17H19V15H7.4C7.3 15 7.2 14.9 7.2 14.8M18 2.8L16.6 1.4L11.8 6.2L9.2 3.6L7.8 5L11.8 9L18 2.8Z",
  cartPlus: "M11 9H13V6H16V4H13V1H11V4H8V6H11M7 18C5.9 18 5 18.9 5 20S5.9 22 7 22 9 21.1 9 20 8.1 18 7 18M17 18C15.9 18 15 18.9 15 20S15.9 22 17 22 19 21.1 19 20 18.1 18 17 18M7.2 14.8V14.7L8.1 13H15.5C16.2 13 16.9 12.6 17.2 12L21.1 5L19.4 4L15.5 11H8.5L4.3 2H1V4H3L6.6 11.6L5.2 14C5.1 14.3 5 14.6 5 15C5 16.1 5.9 17 7 17H19V15H7.4C7.3 15 7.2 14.9 7.2 14.8Z",
  pin: "M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z",
  pencil: "M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z",
  trash: "M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",
  star: "M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.45,13.97L5.82,21L12,17.27Z",
  list: "M3,4H7V8H3V4M9,5V7H21V5H9M3,10H7V14H3V10M9,11V13H21V11H9M3,16H7V20H3V16M9,17V19H21V17H9",
};
const svg = (p, s = 24) =>
  `<svg viewBox="0 0 24 24" width="${s}" height="${s}" aria-hidden="true" focusable="false"><path d="${p}" fill="currentColor"/></svg>`;

const norm = (s) =>
  String(s ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").trim().toLowerCase().replace(/\s+/g, " ");
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const cap = (s) => {
  s = String(s ?? "").replace(/\s+/g, " ").trim();
  return s ? s[0].toUpperCase() + s.slice(1) : s;
};
const rgb = (hex) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || "");
  const n = parseInt(m ? m[1] : "78909c", 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const onColor = (hex) => {
  const [r, g, b] = rgb(hex).map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.45 ? "#1d1b16" : "#ffffff";
};
/* Variables CSS del color de un tipo de plato (como las baldas de Despensa) */
const tone = (hex) => {
  const [r, g, b] = rgb(hex);
  return `--c:${hex};--on-c:${onColor(hex)};--c1:rgba(${r},${g},${b},.12);--c2:rgba(${r},${g},${b},.34);--c3:rgba(${r},${g},${b},.75)`;
};
const stem = (w) => {
  if (w.length > 3 && w.endsWith("s")) w = w.slice(0, -1);
  if (w.length > 3 && w.endsWith("e")) w = w.slice(0, -1);
  return w;
};
const stems = (t) => norm(t).split(/[^a-z0-9]+/).filter(Boolean).map(stem);
/* Guiones suaves en palabras largas para que no se partan en cualquier letra */
const soft = (s) =>
  esc(s).replace(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{9,}/g, (w) =>
    w.replace(/([aeiouáéíóúü])(?=(?:ch|ll|rr|[bcdfghjklmnñpqrstvwxyz])[aeiouáéíóúü])/gi, "$1­")
  );
const fmt = (n, d = 0) => Number(n || 0).toLocaleString("es-ES", { maximumFractionDigits: d, minimumFractionDigits: 0 });
const plural = (n, one, many) => `${fmt(n)} ${n === 1 ? one : many}`;

/* --- semanas ISO (lunes a domingo) */
const DAY_MS = 86400000;
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"];
const DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const DAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const MEALS = ["lunch", "dinner"];
const MEAL = { lunch: "Comida", dinner: "Cena" };
const parseDay = (iso) => {
  const [y, m, d] = String(iso).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
};
const mondayOf = (key) => {
  const m = /^(\d{4})-W(\d{2})$/.exec(key || "");
  if (!m) return null;
  const jan4 = new Date(Date.UTC(+m[1], 0, 4));
  return new Date(jan4.getTime() + ((+m[2] - 1) * 7 - ((jan4.getUTCDay() + 6) % 7)) * DAY_MS);
};
const weekOf = (date) => {
  const thu = new Date(date.getTime() + (3 - ((date.getUTCDay() + 6) % 7)) * DAY_MS);
  const y = thu.getUTCFullYear();
  const jan4 = new Date(Date.UTC(y, 0, 4));
  const mon1 = jan4.getTime() - ((jan4.getUTCDay() + 6) % 7) * DAY_MS;
  return `${y}-W${String(Math.floor((thu.getTime() - mon1) / (7 * DAY_MS)) + 1).padStart(2, "0")}`;
};
const shiftWeek = (key, n) => weekOf(new Date(mondayOf(key).getTime() + n * 7 * DAY_MS));
const weekNumber = (key) => Number(String(key).slice(6));
const dayOf = (key, d) => new Date(mondayOf(key).getTime() + d * DAY_MS);
const rangeText = (key) => {
  const a = dayOf(key, 0);
  const b = dayOf(key, 6);
  const [ad, am, ay] = [a.getUTCDate(), a.getUTCMonth(), a.getUTCFullYear()];
  const [bd, bm, by] = [b.getUTCDate(), b.getUTCMonth(), b.getUTCFullYear()];
  if (ay !== by) return `${ad} ${MONTHS[am]} ${ay} – ${bd} ${MONTHS[bm]} ${by}`;
  if (am !== bm) return `${ad} ${MONTHS[am]} – ${bd} ${MONTHS[bm]} ${by}`;
  return `${ad}–${bd} ${MONTHS[bm]} ${by}`;
};

const STAR_HINT = {
  1: "Poco favorita: solo de vez en cuando",
  2: "Normalita: sale poco",
  3: "Está bien: sale de vez en cuando",
  4: "Muy rica: sale a menudo",
  5: "De las mejores: puede repetirse con frecuencia",
};
const stars = (n, size = 14) =>
  `<span class="stars" role="img" aria-label="${n} de 5 estrellas">${[1, 2, 3, 4, 5]
    .map((i) => `<span class="${i <= n ? "on" : "off"}">${svg(P.star, size)}</span>`)
    .join("")}</span>`;

const UNITS = [
  ["g", "g"], ["kg", "kg"], ["ml", "ml"], ["l", "l"], ["ud", "ud"], ["cda", "cda"], ["cdta", "cdta"], ["gusto", "al gusto"],
];
const FOOD_DEPTS = new Set(["fruta_verdura", "panaderia", "carne", "pescado", "charcuteria", "lacteos", "despensa", "congelados"]);
const BALANCE = [
  ["ok_protein", "🍗", "Proteína"],
  ["ok_veg", "🥦", "Verdura"],
  ["ok_carbs", "🌾", "Hidratos"],
];
const WEEKLY = {
  legumbre: ["🫘", "Legumbres", "raciones"],
  pescado: ["🐟", "Pescado", "raciones"],
  carne: ["🥩", "Carne", "raciones"],
  huevo: ["🥚", "Huevos", "huevos"],
  verdura: ["🥦", "Platos de verdura", "platos"],
  cereal: ["🍝", "Pasta y arroz", "platos"],
};
const EMOJI =
  "🍲🥘🍝🍜🍛🍚🍙🥗🥙🌯🌮🫔🥪🍔🍕🥧🫕🥟🍳🥚🧆🍗🍖🥩🥓🌭🐟🍣🍤🦐🦑🐙🦪🫘🥦🥬🥒🫑🌽🥕🍆🍅🥔🍠🧅🧄🍄🥑🫛🎃🥣🍞🥖🥐🧀🍋🍎🍊🍌🍓🫐🍒🥥🍰🧁🍮🍽️🍴🥄🔥❄️";

/* -------------------------------------------------------------- estilos */
const STYLE = `
:host{display:block;color:var(--primary-text-color,#1c1b1f);font-family:var(--ha-font-family-body,var(--paper-font-body1_-_font-family,Roboto,system-ui,-apple-system,"Segoe UI",sans-serif));-webkit-tap-highlight-color:transparent;
  --surface:var(--card-background-color,#fff);
  --back:var(--primary-background-color,#f4f5f2);
  --line:var(--divider-color,rgba(0,0,0,.12));
  --muted:var(--secondary-text-color,#6f7472);
  --accent:var(--primary-color,#03a9f4);
  --star:var(--menu-semanal-star,#f5b301);
  --star-off:color-mix(in srgb,var(--secondary-text-color,#888) 30%,transparent);
  --warn:var(--warning-color,#f5a400);
  --bad:var(--error-color,#db4437);
  --good:var(--success-color,#2e7d32)}
:host([mode=panel]){height:100%}
*{box-sizing:border-box}
[hidden]{display:none!important}
button{font:inherit;color:inherit}
.app{position:relative;display:flex;flex-direction:column;height:100%;container-type:inline-size}
:host([mode=panel]) .app{background:var(--back)}
.em,.emoji{font-family:"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif;font-style:normal}

/* barra superior */
.toolbar{flex:none;display:flex;align-items:center;gap:4px;height:var(--header-height,56px);padding:0 4px;background:var(--app-header-background-color,var(--back));color:var(--app-header-text-color,var(--primary-text-color));border-bottom:var(--app-header-border-bottom,none)}
.toolbar h1{flex:1;min-width:0;margin:0 0 0 12px;font-size:20px;font-weight:400;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
:host([mode=card]) .toolbar{height:auto;padding:12px 8px 0 16px;background:none;color:inherit;border:0}
:host([mode=card]) .toolbar h1{margin:0;font-size:var(--ha-card-header-font-size,22px)}
.tabs{display:flex;gap:2px;padding:3px;border-radius:20px;background:color-mix(in srgb,var(--primary-text-color,#000) 7%,transparent)}
.tab{height:32px;padding:0 14px;border:0;border-radius:16px;background:none;cursor:pointer;font-size:14px;font-weight:500;color:var(--muted)}
.tab[aria-pressed=true]{background:var(--surface);color:var(--primary-text-color);box-shadow:0 1px 3px rgba(0,0,0,.14)}
.icon-btn{display:grid;place-items:center;width:40px;height:40px;border-radius:50%;border:0;background:none;cursor:pointer;flex:none}
.icon-btn:hover{background:rgba(127,127,127,.12)}
.icon-btn[disabled]{opacity:.35;cursor:default;background:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

.scroller{flex:1;overflow-y:auto;overscroll-behavior:contain}
:host([mode=card]) .scroller{overflow:visible}
.page{width:100%;max-width:1400px;margin:0 auto;padding:12px 16px 96px}
:host([mode=card]) .page{padding:8px 16px 16px}
@container (min-width:900px){.page{padding:16px 24px 96px}}

/* semana: título arriba a la izquierda, acciones a la derecha */
.weekbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;margin-bottom:14px}
.weeknav{display:flex;align-items:center;gap:2px;margin-right:auto;min-width:0}
.weeknav .icon-btn{width:38px;height:38px;border:1px solid var(--line);background:var(--surface)}
.weeknav .icon-btn:hover{background:color-mix(in srgb,var(--surface) 88%,var(--primary-text-color))}
.weektitle{display:flex;flex-direction:column;min-width:0;padding:0 10px}
.weektitle h2{margin:0;font-size:24px;line-height:1.15;font-weight:600;letter-spacing:-.01em;white-space:nowrap}
.weektitle span{font-size:13.5px;color:var(--muted);white-space:nowrap}
.weektitle .now{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:8px;background:color-mix(in srgb,var(--accent) 16%,transparent);color:var(--accent);font-size:11.5px;font-weight:600;letter-spacing:0;vertical-align:3px}
.chip{flex:none;display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 14px;border-radius:17px;border:1px solid var(--line);background:var(--surface);cursor:pointer;font-size:14px;white-space:nowrap}
.chip .n{opacity:.66;font-variant-numeric:tabular-nums}
.chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--text-primary-color,#fff)}
.chip.cat[aria-pressed=true]{background:var(--c1);border-color:var(--c);color:inherit;box-shadow:inset 0 0 0 1px var(--c)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--c);flex:none}
.actions-row{display:flex;flex-wrap:wrap;gap:8px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:40px;padding:0 18px;border-radius:20px;border:0;font-weight:500;font-size:14px;cursor:pointer;background:var(--accent);color:var(--text-primary-color,#fff);white-space:nowrap}
.btn:hover{filter:brightness(1.06)}
.btn.tonal{background:color-mix(in srgb,var(--accent) 14%,var(--surface));color:var(--primary-text-color)}
.btn.outline{background:var(--surface);color:var(--primary-text-color);border:1px solid var(--line)}
.btn.quiet{background:none;color:var(--accent);padding:0 12px}
.btn.danger{background:none;color:var(--bad);padding:0 12px}
.btn[disabled]{opacity:.55;cursor:default;filter:none}
.spin{display:inline-block;width:16px;height:16px;border-radius:50%;border:2px solid currentColor;border-right-color:transparent;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:0 2px 12px;font-size:12.5px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}

/* la semana: columnas por día, filas comida/cena (subgrid alinea las filas) */
.week{display:grid;grid-template-columns:30px repeat(7,minmax(0,1fr));grid-template-rows:auto auto auto auto;gap:8px}
.col{display:grid;grid-row:span 4;grid-template-rows:subgrid;min-width:0}
.labels .rowlabel{align-self:center;justify-self:center;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);writing-mode:vertical-rl;transform:rotate(180deg)}
.labels .rowlabel.foot{writing-mode:horizontal-tb;transform:none;font-size:11px;letter-spacing:.02em}
.head{display:flex;align-items:baseline;justify-content:center;gap:6px;padding:4px 0 2px;font-size:14px;color:var(--muted)}
.head .dn{font-weight:600;color:var(--primary-text-color)}
.head .full,.head .mon{display:none}
.today .head .dn,.today .head .dd{color:var(--accent)}
.today .head{position:relative}
.today .head::after{content:"";position:absolute;left:50%;bottom:-3px;width:22px;height:3px;border-radius:2px;background:var(--accent);transform:translateX(-50%)}
.past{opacity:.6}
.meal-tag{display:none}

.slot{position:relative;display:flex;flex-direction:column;min-width:0;min-height:158px;border-radius:14px;border:2px solid var(--c);background:color-mix(in srgb,var(--c) 9%,var(--surface));overflow:hidden;transition:box-shadow .14s ease}
.slot:hover{box-shadow:0 4px 14px -6px color-mix(in srgb,var(--c) 70%,transparent)}
.slot-main{flex:1;display:flex;flex-direction:column;align-items:flex-start;gap:4px;width:100%;padding:10px 10px 8px;border:0;background:none;text-align:left;cursor:pointer;min-width:0}
.slot-main .top{display:flex;align-items:flex-start;width:100%;gap:4px}
.slot-main .em{font-size:28px;line-height:1.1;flex:1}
.slot-main .nm{font-size:13.5px;font-weight:600;line-height:1.25;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere;hyphens:manual}
.slot-main .meta{display:flex;flex-wrap:wrap;align-items:center;gap:2px 6px;margin-top:auto;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.slot .link{display:inline-flex;align-items:center;gap:4px;max-width:100%;padding:1px 7px 1px 5px;border-radius:9px;background:var(--surface);border:1px solid var(--c2);font-size:11px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badge{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--surface);color:var(--muted);box-shadow:0 1px 3px rgba(0,0,0,.16);flex:none}
.badge.pin{color:var(--c)}
.badge.cart{background:var(--warn);color:#1d1b16}
.change{display:flex;align-items:center;justify-content:center;gap:5px;width:100%;height:32px;border:0;border-top:1px solid var(--c2);background:color-mix(in srgb,var(--c) 16%,var(--surface));color:var(--primary-text-color);font-size:11.5px;font-weight:700;letter-spacing:.06em;cursor:pointer}
.change:hover{background:color-mix(in srgb,var(--c) 30%,var(--surface))}
.change[disabled]{cursor:default;opacity:.7}
.slot.busy .slot-main{opacity:.45}
.slot.enter{animation:pop .32s cubic-bezier(.2,.9,.3,1.2)}
@keyframes pop{from{transform:scale(.93);opacity:.15}}
.slot.empty,.slot.free{border-style:dashed;border-color:color-mix(in srgb,var(--primary-text-color) 22%,transparent);background:none}
.slot.empty .slot-main,.slot.free .slot-main{align-items:center;justify-content:center;text-align:center;color:var(--muted)}
.slot.empty .plus{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;border:1.5px dashed currentColor}
.slot.empty .nm,.slot.free .nm{font-weight:500;color:var(--muted)}
.slot.empty .meta,.slot.free .meta{margin-top:0}
.slot.free{background:repeating-linear-gradient(135deg,transparent 0 8px,color-mix(in srgb,var(--primary-text-color) 4%,transparent) 8px 16px)}

.foot{display:flex;flex-direction:column;align-items:center;gap:4px;padding:2px 2px 0;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.foot b{font-size:13px;color:var(--primary-text-color)}
.bar{position:relative;display:block;width:100%;max-width:120px;height:5px;border-radius:3px;background:color-mix(in srgb,var(--primary-text-color) 9%,transparent);overflow:hidden}
.bar i{position:absolute;inset:0 auto 0 0;border-radius:3px;background:var(--good)}
.bar.low i{background:var(--warn)}
.bar.high i{background:var(--bad)}
.bal{display:flex;gap:3px;font-size:14px}
.bal span.off{filter:grayscale(1);opacity:.3}

/* debajo de la semana */
.extras{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;margin-top:22px}
@container (min-width:900px){.extras{grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);align-items:start}}
.panel{padding:16px 18px;border-radius:18px;background:var(--surface);border:1px solid var(--line)}
.panel h3{display:flex;align-items:center;gap:8px;margin:0 0 4px;font-size:16px;font-weight:600}
.panel h3 .em{font-size:19px}
.panel .sub{margin:0 0 12px;font-size:13px;line-height:1.45;color:var(--muted)}
.targets{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.target{display:flex;align-items:center;gap:10px;padding:9px 11px;border-radius:12px;background:color-mix(in srgb,var(--good) 8%,transparent);border:1px solid color-mix(in srgb,var(--good) 25%,transparent)}
.target.bad{background:color-mix(in srgb,var(--warn) 12%,transparent);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.target .em{font-size:20px}
.target .txt{display:flex;flex-direction:column;min-width:0;font-size:12px;color:var(--muted);line-height:1.3}
.target .txt b{font-size:13.5px;color:var(--primary-text-color);font-weight:500}
.target .v{margin-left:auto;font-size:16px;font-weight:700;font-variant-numeric:tabular-nums}
.batch{display:grid;gap:10px}
.base{padding:10px 12px;border-radius:14px;border:1px solid var(--line);background:color-mix(in srgb,var(--accent) 4%,var(--surface))}
.base .t{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600}
.base .t .em{font-size:18px}
.base .t small{margin-left:auto;font-size:12.5px;font-weight:500;color:var(--muted)}
.uses{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.use{display:inline-flex;align-items:center;gap:6px;max-width:100%;height:28px;padding:0 10px 0 4px;border-radius:14px;border:1px solid var(--c2);background:var(--c1);font-size:12.5px;cursor:pointer}
.use b{display:grid;place-items:center;height:20px;padding:0 7px;border-radius:10px;background:var(--c);color:var(--on-c);font-size:11px;font-weight:600}
.use span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cook{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:2px 12px;margin-top:4px}
.cook-row{display:flex;align-items:center;gap:10px;padding:6px 4px;border-radius:10px;font-size:13.5px}
.cook-row .em{display:grid;place-items:center;width:34px;height:34px;flex:none;border-radius:10px;border:1.5px solid var(--c);background:var(--c1);font-size:18px}
.cook-row .txt{flex:1;min-width:0}
.cook-row .nm{display:block;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cook-row .when{display:block;font-size:12px;color:var(--muted)}
.cook-row .q{flex:none;font-size:12.5px;font-weight:600;color:var(--muted);font-variant-numeric:tabular-nums}
.freeze{display:flex;gap:8px;margin-top:12px;padding:10px 12px;border-radius:12px;background:color-mix(in srgb,#29b6f6 11%,transparent);font-size:12.5px;line-height:1.45;color:var(--muted)}
h4{margin:16px 0 6px;font-size:12.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}

/* recetas */
.rbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:6px}
.searchbar{flex:1;min-width:220px;display:flex;align-items:center;gap:6px;height:44px;padding:0 6px 0 14px;border-radius:22px;background:var(--surface);border:1px solid var(--line);color:var(--muted)}
.searchbar:focus-within{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.searchbar input{flex:1;min-width:0;height:100%;border:0;background:none;outline:none;font:inherit;font-size:16px;color:var(--primary-text-color)}
.filters{display:flex;gap:8px;overflow-x:auto;padding:10px 0 4px;scrollbar-width:none}
.filters::-webkit-scrollbar{display:none}
.filters .sep{flex:none;width:1px;margin:4px 2px;background:var(--line)}
.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin-top:12px}
.rcard{position:relative;display:flex;flex-direction:column;align-items:stretch;gap:6px;min-height:150px;padding:12px 14px;border-radius:16px;border:2px solid var(--c);background:color-mix(in srgb,var(--c) 8%,var(--surface));text-align:left;cursor:pointer;transition:transform .14s ease,box-shadow .14s ease}
.rcard:hover{box-shadow:0 6px 16px -8px color-mix(in srgb,var(--c) 80%,transparent);transform:translateY(-1px)}
.rcard .top{display:flex;align-items:flex-start;gap:10px}
.rcard .em{font-size:32px;line-height:1}
.rcard .nm{flex:1;font-size:15px;font-weight:600;line-height:1.25;overflow-wrap:anywhere;hyphens:manual}
.rcard .meta{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;margin-top:auto;font-size:12.5px;color:var(--muted)}
.tag{display:inline-flex;align-items:center;height:20px;padding:0 8px;border-radius:10px;background:color-mix(in srgb,var(--primary-text-color) 7%,transparent);font-size:11.5px;font-weight:500;color:var(--primary-text-color)}
.tag.cat{background:var(--c);color:var(--on-c)}
.stars{display:inline-flex;gap:1px;vertical-align:middle}
.stars .on{color:var(--star)}
.stars .off{color:var(--star-off)}
.stars svg{display:block}

/* vacío / error */
.empty{max-width:560px;margin:0 auto;padding:40px 18px 44px;text-align:center;color:var(--muted);font-size:14px;line-height:1.5}
.empty .big{font-size:48px;line-height:1}
.empty strong{display:block;margin:12px 0 4px;color:var(--primary-text-color);font-size:17px;font-weight:600}
.empty .actions-row{justify-content:center;margin-top:16px}
.loading{padding:64px 16px;text-align:center;color:var(--muted)}
.notice{display:flex;align-items:flex-start;gap:10px;margin:0 0 12px;padding:10px 14px;border-radius:12px;background:color-mix(in srgb,var(--warn) 13%,transparent);font-size:13px;line-height:1.45}
.notice.info{background:color-mix(in srgb,var(--accent) 10%,transparent)}

/* aviso inferior */
.snackbar{position:absolute;left:50%;bottom:16px;z-index:6;display:flex;align-items:center;gap:8px;min-width:260px;max-width:calc(100% - 32px);padding:6px 6px 6px 16px;border-radius:12px;background:#2f3133;color:#f2f2f2;font-size:14px;box-shadow:0 6px 24px rgba(0,0,0,.28);transform:translate(-50%,24px);opacity:0;pointer-events:none;transition:transform .2s ease,opacity .2s ease}
.snackbar.show{transform:translate(-50%,0);opacity:1;pointer-events:auto}
.snackbar span{flex:1;padding:8px 0}
.snackbar button{border:0;background:none;color:#8fd0ff;font-weight:600;padding:8px 12px;border-radius:8px;cursor:pointer}
:host([mode=card]) .snackbar{position:sticky;transform:none;left:auto;margin:0 auto 12px;width:fit-content;display:none}
:host([mode=card]) .snackbar.show{display:flex}

/* hojas (diálogos) */
dialog{border:0;padding:0;width:min(560px,calc(100vw - 24px));max-height:min(92vh,880px);border-radius:22px;background:var(--surface);color:var(--primary-text-color,#1c1b1f);box-shadow:0 18px 50px rgba(0,0,0,.3);overflow:hidden}
dialog.wide{width:min(720px,calc(100vw - 24px))}
dialog[open]{display:flex;flex-direction:column}
dialog::backdrop{background:rgba(0,0,0,.5)}
@media (max-width:600px){dialog,dialog.wide{width:100vw;max-width:100vw;margin:auto 0 0;border-radius:22px 22px 0 0;max-height:94vh}}
.sheet-head{display:flex;align-items:center;gap:12px;padding:14px 10px 10px 18px}
.sheet-head .titles{flex:1;min-width:0}
.sheet-head h2{margin:0;font-size:19px;font-weight:600;line-height:1.25}
.sheet-head .titles span{display:flex;align-items:center;gap:6px;margin-top:3px;font-size:13px;color:var(--muted)}
.sheet-body{flex:1;overflow:auto;padding:4px 18px 14px}
.sheet-foot{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px 16px 16px;border-top:1px solid var(--line)}
.sheet-foot .grow{flex:1}
.sheet-foot .err{width:100%;margin:0 2px;font-size:13px;color:var(--bad)}
.big-em{display:grid;place-items:center;width:56px;height:56px;border-radius:16px;border:2px solid var(--c);background:var(--c1);font-size:32px;flex:none}
button.big-em{cursor:pointer}
.kv{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.kv span{display:inline-flex;align-items:center;gap:4px;height:28px;padding:0 10px;border-radius:14px;background:color-mix(in srgb,var(--primary-text-color) 6%,transparent);font-size:13px;font-variant-numeric:tabular-nums}
.kv span b{font-weight:600}
.ings{margin:4px 0 0;padding:0;list-style:none}
.ings li{display:flex;align-items:baseline;gap:12px;padding:7px 2px;border-bottom:1px solid var(--line);font-size:14px}
.ings li:last-child{border-bottom:0}
.ings li span:first-child{flex:1}
.ings li .q{color:var(--muted);font-variant-numeric:tabular-nums;text-align:right}
.notes{white-space:pre-wrap;font-size:14px;line-height:1.5;margin:4px 0 0}
.stack{display:grid;gap:8px;padding:12px 16px 18px;border-top:1px solid var(--line)}
.stack .btn{width:100%;height:46px;border-radius:14px}
.stack .row2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.stack p{margin:2px 4px 2px;font-size:13px;line-height:1.45;color:var(--muted)}
.hint-inline{margin-left:6px;font-size:13px;color:var(--muted);vertical-align:middle}

/* elegir receta */
.pick-list{display:grid;grid-template-columns:minmax(0,1fr);gap:6px;margin-top:10px}
.pick{display:flex;align-items:center;gap:12px;width:100%;padding:8px 10px;border-radius:14px;border:1.5px solid var(--c2);border-left:6px solid var(--c);background:var(--c1);text-align:left;cursor:pointer}
.pick:hover{border-color:var(--c)}
.pick .em{font-size:26px}
.pick .txt{flex:1;min-width:0}
.pick .nm{display:block;font-size:14.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pick .sub{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted)}
.pick.current{outline:2px solid var(--accent)}

/* comprobar ingredientes */
.check-list{display:grid;grid-template-columns:minmax(0,1fr);gap:6px}
.crow{display:flex;align-items:center;gap:12px;padding:8px 10px;border-radius:14px;border:1px solid var(--line);background:var(--surface)}
.crow.missing{border-color:color-mix(in srgb,var(--warn) 55%,transparent);background:color-mix(in srgb,var(--warn) 7%,var(--surface))}
.crow.off{opacity:.55}
.crow input[type=checkbox]{width:20px;height:20px;margin:0;accent-color:var(--accent);flex:none;cursor:pointer}
.crow .em{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:color-mix(in srgb,var(--primary-text-color) 6%,transparent);font-size:21px;flex:none}
.crow .txt{flex:1;min-width:0}
.crow .nm{display:block;font-size:14.5px;font-weight:600}
.crow .sub{display:block;font-size:12.5px;line-height:1.4;color:var(--muted)}
.crow .for{display:block;font-size:11.5px;color:var(--muted);opacity:.85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.qty{flex:none;padding:4px 10px;border-radius:12px;background:color-mix(in srgb,var(--warn) 22%,transparent);font-size:13px;font-weight:700;white-space:nowrap}
.qty.ok{background:color-mix(in srgb,var(--good) 16%,transparent);color:var(--good)}
.qty.cesta{background:color-mix(in srgb,var(--accent) 14%,transparent);color:var(--accent)}
.eq{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:6px;font-size:12.5px;color:var(--muted)}
.eq input{width:76px;height:32px;padding:0 8px;border-radius:9px;border:1px solid var(--line);background:none;color:inherit;font:inherit;font-size:14px}
.eq .btn{height:32px;padding:0 12px;font-size:13px}
.allgood{padding:26px 10px 18px;text-align:center}
.allgood .big{display:inline-grid;place-items:center;width:64px;height:64px;border-radius:50%;background:color-mix(in srgb,var(--good) 15%,transparent);color:var(--good)}
.allgood strong{display:block;margin:12px 0 4px;font-size:17px}
.allgood p{margin:0;color:var(--muted);font-size:13.5px}
details{margin-top:14px;border-top:1px solid var(--line)}
summary{display:flex;align-items:center;gap:8px;padding:12px 2px;cursor:pointer;list-style:none;font-size:14px;font-weight:500}
summary::-webkit-details-marker{display:none}
summary svg{margin-left:auto;color:var(--muted);transition:transform .15s}
details[open] summary svg{transform:rotate(180deg)}

/* editor de recetas */
.edit-head{display:flex;align-items:center;gap:12px;padding:16px 10px 8px 18px}
.name-input{flex:1;min-width:0;height:48px;padding:0 12px;border-radius:12px;border:1px solid var(--line);background:none;color:inherit;font:inherit;font-size:18px;font-weight:600;outline:none}
.name-input:focus,.input:focus,select:focus,textarea:focus{border-color:var(--accent)}
.field{display:block;margin:16px 0 0}
.field>.lbl{display:flex;align-items:baseline;gap:8px;margin:0 0 8px;font-size:13px;font-weight:600;color:var(--muted)}
.field>.lbl small{font-weight:400}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip .auto{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;opacity:.7}
.rate{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.rate .stars button{display:grid;place-items:center;width:40px;height:40px;border:0;background:none;padding:0;cursor:pointer;border-radius:50%}
.rate .stars button:hover{background:rgba(127,127,127,.1)}
.rate .hint{font-size:13px;color:var(--muted)}
.mini{display:flex;align-items:center;gap:4px;flex:none}
.mini .icon-btn{width:34px;height:34px;border:1px solid var(--line)}
.mini output{min-width:34px;text-align:center;font-size:17px;font-weight:600;font-variant-numeric:tabular-nums}
.ing-list{display:grid;gap:6px}
.ing{display:grid;grid-template-columns:minmax(0,1fr) 78px 108px 36px;gap:6px;align-items:center}
.input,select,textarea{width:100%;height:40px;padding:0 10px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:inherit;font:inherit;font-size:15px;outline:none}
input.input[type=number]{text-align:right;font-variant-numeric:tabular-nums}
textarea{height:auto;min-height:90px;padding:10px;line-height:1.45;resize:vertical}
.ing .icon-btn{width:36px;height:36px}
.add-ing{justify-self:start;margin-top:4px}
.estimate{margin-top:14px;padding:12px 14px;border-radius:14px;background:color-mix(in srgb,var(--primary-text-color) 5%,transparent);font-size:13px;line-height:1.5;color:var(--muted)}
.estimate b{color:var(--primary-text-color)}
.estimate .row{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px}
.estimate .kcal{font-size:20px;font-weight:700;color:var(--primary-text-color)}
.estimate .manual{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:8px}
.estimate .manual .input{width:96px;height:34px}
.help{margin:6px 2px 0;font-size:12.5px;line-height:1.45;color:var(--muted)}
.emoji-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(42px,1fr));gap:2px;margin:4px 18px 4px;padding:8px;border-radius:14px;background:color-mix(in srgb,var(--primary-text-color) 5%,transparent);max-height:180px;overflow:auto}
.emoji-grid button{height:42px;border:0;background:none;border-radius:10px;font-size:24px;cursor:pointer}
.emoji-grid button:hover{background:rgba(127,127,127,.16)}

/* ajustes */
.setting{display:flex;align-items:center;gap:12px;padding:14px 0;border-top:1px solid var(--line)}
.setting:first-child{border-top:0}
.setting .txt{flex:1;min-width:0}
.setting .t{display:block;font-size:14.5px}
.setting .s{display:block;font-size:12.5px;color:var(--muted);margin-top:2px;line-height:1.4}
.setting .input{width:110px;flex:none}
.setting input[type=color]{width:44px;height:34px;padding:2px;border-radius:8px;border:1px solid var(--line);background:none;cursor:pointer;flex:none}
.switch{position:relative;flex:none;width:44px;height:26px}
.switch input{position:absolute;inset:0;margin:0;opacity:0;cursor:pointer}
.switch span{position:absolute;inset:0;border-radius:13px;background:var(--line);transition:background .15s;pointer-events:none}
.switch span::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.3);transition:transform .15s}
.switch input:checked+span{background:var(--accent)}
.switch input:checked+span::after{transform:translateX(18px)}
.switch input:disabled+span{opacity:.4}
.settings h3{margin:22px 0 4px;font-size:14.5px;font-weight:600}
.settings p{margin:0 0 6px;font-size:13px;line-height:1.45;color:var(--muted)}

/* móvil y columnas estrechas: un bloque por día */
@container (max-width:899px){
  .week{display:flex;flex-direction:column;gap:12px}
  .col.labels{display:none}
  .col.day{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto auto auto;gap:8px;padding:10px;border-radius:18px;background:var(--surface);border:1px solid var(--line)}
  .col.day.today{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
  .col.day .head{grid-column:1/-1;justify-content:flex-start;padding:2px 4px;font-size:15px}
  .head .short,.head .dd{display:none}
  .head .full,.head .mon{display:inline}
  .today .head::after{display:none}
  .col.day .foot{grid-column:1/-1;flex-direction:row;justify-content:flex-start;gap:12px;padding:0 4px}
  .foot .bar{max-width:none;flex:1}
  .meal-tag{display:block;font-size:10.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
  .slot{min-height:150px}
  .weektitle h2{font-size:21px}
  .weekbar .actions-row{width:100%}
  .weekbar .actions-row .btn{flex:1 1 auto}
}
/* tableta: dos días por fila */
@container (min-width:620px) and (max-width:899px){
  .week{display:grid;grid-template-columns:1fr 1fr;align-items:start}
}
@container (max-width:460px){
  .weekbar .actions-row{flex-direction:column}
  .weekbar .actions-row .btn{flex:none;width:100%;height:44px}
  .ing{grid-template-columns:minmax(0,1fr) 60px 96px 32px}
  .toolbar h1{font-size:18px;margin-left:4px}
  .tab{padding:0 10px}
}
@media (prefers-reduced-motion:reduce){.slot,.rcard,.snackbar,.switch span,.switch span::after{transition:none}.slot.enter{animation:none}.spin{animation-duration:2s}}
`;

/* ------------------------------------------------------- componente base */
class MenuSemanalBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null;
    this._config = {};
    this._view = "menu";
    this._week = null; // semana que se ve ("2026-W41")
    this._recipeQuery = "";
    this._recipeFilter = null; // null | "lunch" | "dinner" | id de tipo de plato
    this._busy = {}; // generate, check, cesta, save, slot:<n>
    this._missing = null; // {week, slots:Set} tras comprobar la despensa
    this._entered = new Set();
    this._narrow = false;
  }

  get mode() {
    return "panel";
  }

  /* ---- ciclo de vida */
  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._build();
    if (!this._unsub && !this._connecting && this.isConnected) this._connect();
    this._updateMenuButton();
  }
  get hass() {
    return this._hass;
  }
  set narrow(v) {
    this._narrow = v;
    this._updateMenuButton();
  }
  connectedCallback() {
    if (this._hass && !this._unsub && !this._connecting) this._connect();
  }
  disconnectedCallback() {
    if (this._unsub) {
      this._unsub();
      this._unsub = null;
    }
    clearTimeout(this._snackTimer);
  }

  async _connect() {
    this._connecting = true;
    try {
      if (!this._catalog) {
        const res = await this._hass.callWS({ type: "menu_semanal/catalog" });
        this._catalog = res.catalog || [];
        this._foods = res.foods || [];
        this._catIndex = new Map(this._catalog.map((e) => [stems(e.name).join(" "), e]));
      }
      const unsub = await this._hass.connection.subscribeMessage((state) => this._onState(state), {
        type: "menu_semanal/subscribe",
      });
      if (!this.isConnected) unsub();
      else this._unsub = unsub;
    } catch (err) {
      this._error = err && err.code === "not_loaded" ? "not_loaded" : (err && err.message) || String(err);
      this._render();
    } finally {
      this._connecting = false;
    }
  }

  _onState(state) {
    const first = !this._state;
    this._state = state;
    this._error = null;
    if (first || !this._week) this._week = state.current_week;
    this._render();
  }

  /* ---- esqueleto */
  _build() {
    const card = this.mode === "card";
    this.setAttribute("mode", this.mode);
    if (card && this._config.view === "recipes") this._view = "recipes";
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      ${card ? "<ha-card>" : ""}
      <div class="app" lang="es">
        <header class="toolbar">
          ${card ? "" : `<button class="icon-btn menu" data-action="menu" aria-label="Menú" hidden>${svg(P.menu)}</button>`}
          <h1 class="title">${esc(this._config.title || "Menú Semanal")}</h1>
          <div class="tabs" role="tablist" aria-label="Vista">
            <button class="tab" role="tab" data-action="view" data-id="menu">Menú</button>
            <button class="tab" role="tab" data-action="view" data-id="recipes">Recetas</button>
          </div>
          <button class="icon-btn" data-action="settings" aria-label="Ajustes de Menú Semanal" title="Ajustes">${svg(P.cog)}</button>
        </header>
        <div class="scroller"><div class="page"><div class="loading">Abriendo el recetario…</div></div></div>
        <div class="snackbar" role="status" aria-live="polite"><span></span><button type="button" data-action="snack" hidden></button></div>
        <dialog></dialog>
      </div>
      ${card ? "</ha-card>" : ""}`;
    const $ = (s) => this.shadowRoot.querySelector(s);
    this.$ = { page: $(".page"), scroller: $(".scroller"), menu: $(".menu"), snack: $(".snackbar"), dialog: $("dialog"), tabs: $(".tabs") };
    const root = this.shadowRoot;
    root.addEventListener("click", (e) => this._onClick(e));
    root.addEventListener("input", (e) => this._onInput(e));
    root.addEventListener("change", (e) => this._onInput(e));
    root.addEventListener("keydown", (e) => this._onKey(e));
    this.$.dialog.addEventListener("close", () => {
      this._sheet = null;
      this._draft = null;
      this.$.dialog.className = "";
    });
    this.$.dialog.addEventListener("click", (e) => {
      if (e.target === this.$.dialog) this.$.dialog.close(); // clic en el fondo
    });
    this._updateMenuButton();
  }

  _updateMenuButton() {
    if (!this.$ || !this.$.menu) return;
    const hidden = this._hass && this._hass.dockedSidebar === "always_hidden";
    this.$.menu.hidden = !(this._narrow || hidden);
  }

  /* ---- datos auxiliares */
  _recipe(id) {
    return this._state && this._state.recipes.find((r) => r.id === id);
  }
  _cat(id) {
    const cats = this._state ? this._state.categories : [];
    return cats.find((c) => c.id === id) || cats.find((c) => c.id === "otros") || { id: "otros", name: "Otros", color: "#78909C", icon: "🍽️" };
  }
  get _people() {
    return (this._state && this._state.settings.people) || 2;
  }
  _weekData(key = this._week) {
    const w = this._state && this._state.weeks[key];
    if (w) return w;
    return { key, slots: Array.from({ length: 14 }, () => ({ recipe_id: null, free: false, locked: false })), summary: null };
  }
  /* Día de hoy dentro de la semana (0 = lunes; <0 semana futura; >6 semana pasada) */
  _todayIndex(key) {
    return Math.round((parseDay(this._state.today) - mondayOf(key)) / DAY_MS);
  }
  _kcal(r) {
    const k = r && r.info && r.info.kcal;
    return k ? `≈ ${fmt(k)} kcal` : "kcal ?";
  }
  _iconFor(name) {
    const e = this._catIndex && this._catIndex.get(stems(name).join(" "));
    return (e && e.icon) || "🍲";
  }
  /* Bases (batch cooking) que un plato comparte con otros de la semana */
  _sharedBases(week, index) {
    const sum = week.summary;
    if (!sum) return [];
    const d = index >> 1;
    const meal = MEALS[index % 2];
    return sum.batch.filter((g) => g.slots.some((s) => s[0] === d && s[1] === meal));
  }

  /* ------------------------------------------------------------ pintado */
  _render() {
    if (!this.$) return;
    for (const t of this.$.tabs.querySelectorAll(".tab")) t.setAttribute("aria-pressed", String(t.dataset.id === this._view));
    if (this._error) {
      const msg =
        this._error === "not_loaded"
          ? "Menú Semanal no está configurado. Añádelo en Ajustes → Dispositivos y servicios → Añadir integración."
          : `No se pudo cargar: ${this._error}`;
      this.$.page.innerHTML = `<div class="empty"><div class="big emoji">🗓️</div><strong>Sin conexión con el menú</strong>${esc(msg)}</div>`;
      return;
    }
    if (!this._state) return;
    if (this._view === "recipes") this._renderRecipes();
    else this._renderMenu();
    if (this._sheet === "slot") this._renderSlotSheet();
    if (this._sheet === "settings") this._renderSettings();
    if (this._sheet === "picker") this._renderPicker(true);
  }

  /* ---------- vista semanal */
  _renderMenu() {
    const st = this._state;
    const key = this._week;
    const week = this._weekData(key);
    const current = key === st.current_week;
    const ti = this._todayIndex(key);
    const planned = week.slots.filter((s) => s.recipe_id && !s.free).length;
    const busyGen = !!this._busy.generate;
    const busyCheck = !!this._busy.check;
    const missing = this._missing && this._missing.week === key ? this._missing.slots : null;

    const head = `
      <div class="weekbar">
        <div class="weeknav">
          <button class="icon-btn" data-action="week" data-id="-1" aria-label="Semana anterior" title="Semana anterior">${svg(P.left)}</button>
          <div class="weektitle">
            <h2>Semana ${weekNumber(key)}${current ? `<span class="now">esta semana</span>` : ""}</h2>
            <span>${rangeText(key)}</span>
          </div>
          <button class="icon-btn" data-action="week" data-id="1" aria-label="Semana siguiente" title="Semana siguiente">${svg(P.right)}</button>
          ${current ? "" : `<button class="chip" data-action="week" data-id="0" style="margin-left:8px">Hoy</button>`}
        </div>
        <div class="actions-row">
          <button class="btn" data-action="generate" ${busyGen ? "disabled" : ""}>${busyGen ? `<span class="spin"></span>Generando…` : `${svg(P.wand, 18)}Generar`}</button>
          <button class="btn tonal" data-action="check" ${busyCheck || !planned ? "disabled" : ""} ${planned ? "" : `title="Primero genera o elige algún plato"`}>${busyCheck ? `<span class="spin"></span>Comprobando…` : `${svg(P.cartCheck, 18)}Comprobar disponibilidad de ingredientes`}</button>
        </div>
      </div>`;

    if (!st.recipes.length) {
      this.$.page.innerHTML = `${head}
        <div class="empty"><div class="big emoji">📖</div><strong>Aún no hay recetas</strong>
          El menú se genera con tus recetas. Crea las tuyas (para comida, cena o las dos) o empieza con unas de ejemplo.
          <div class="actions-row"><button class="btn" data-action="new-recipe">${svg(P.plus, 18)}Crear receta</button><button class="btn outline" data-action="examples">Añadir recetas de ejemplo</button></div></div>`;
      return;
    }

    const legend = `<div class="legend" aria-label="Colores por componente principal">${st.categories
      .map((c) => `<span style="${tone(c.color)}"><i class="dot"></i>${esc(c.name)}</span>`)
      .join("")}</div>`;

    const labels = `<div class="col labels" aria-hidden="true"><div class="head"></div><div class="rowlabel">Comida</div><div class="rowlabel">Cena</div><div class="rowlabel foot">kcal</div></div>`;
    const days = [];
    for (let d = 0; d < 7; d++) {
      const date = dayOf(key, d);
      const cls = ["col", "day", d === ti ? "today" : "", ti > d ? "past" : ""].join(" ");
      const dayName = `<span class="dn"><span class="short">${DAYS_SHORT[d]}</span><span class="full">${DAYS[d]}</span></span>
        <span class="dd">${date.getUTCDate()}</span><span class="mon">${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}</span>`;
      days.push(`<div class="${cls}" role="group" aria-label="${DAYS[d]} ${date.getUTCDate()}">
        <div class="head">${dayName}</div>
        ${this._slotHTML(week, 2 * d, missing)}
        ${this._slotHTML(week, 2 * d + 1, missing)}
        <div class="foot">${this._dayFoot(week, d)}</div>
      </div>`);
    }
    this.$.page.innerHTML = `${head}${legend}<div class="week">${labels}${days.join("")}</div>${this._extras(week)}`;
    this._entered.clear();
  }

  _slotHTML(week, i, missing) {
    const slot = week.slots[i];
    const meal = MEALS[i % 2];
    const tag = `<span class="meal-tag">${MEAL[meal]}</span>`;
    const busy = !!this._busy[`slot:${i}`];
    const enter = this._entered.has(i) ? " enter" : "";
    if (slot.free) {
      return `<div class="slot free"><button class="slot-main" data-action="open-slot" data-slot="${i}" aria-label="${MEAL[meal]}: libre">${tag}<span class="em emoji">🍴</span><span class="nm">Libre</span><span class="meta">Comer fuera</span></button></div>`;
    }
    const r = slot.recipe_id && this._recipe(slot.recipe_id);
    if (!r) {
      return `<div class="slot empty${busy ? " busy" : ""}"><button class="slot-main" data-action="open-slot" data-slot="${i}" aria-label="${MEAL[meal]}: sin plato">${tag}<span class="plus">${busy ? `<span class="spin"></span>` : svg(P.plus, 20)}</span><span class="nm">${slot.recipe_id ? "Receta borrada" : "Elegir plato"}</span></button></div>`;
    }
    const cat = this._cat(r.category);
    const shared = this._sharedBases(week, i);
    const miss = missing && missing.has(i);
    return `<div class="slot${busy ? " busy" : ""}${enter}" style="${tone(cat.color)}">
      <button class="slot-main" data-action="open-slot" data-slot="${i}" aria-label="${esc(`${MEAL[meal]}: ${r.name}. ${cat.name}. ${r.rating} estrellas.`)}">
        ${tag}
        <span class="top"><span class="em">${esc(r.icon)}</span>
          ${miss ? `<span class="badge cart" title="Falta algún ingrediente">${svg(P.cartPlus, 13)}</span>` : ""}
          ${slot.locked ? `<span class="badge pin" title="Fijado: se mantiene al generar">${svg(P.pin, 13)}</span>` : ""}</span>
        <span class="nm">${soft(r.name)}</span>
        <span class="meta">${stars(r.rating, 11)}<span>${this._kcal(r)}</span></span>
        ${shared.length ? `<span class="link" title="Se cocina junto con otro plato de la semana">🔗 ${esc(shared[0].name)}</span>` : ""}
      </button>
      <button class="change" data-action="change" data-slot="${i}" ${busy ? "disabled" : ""} title="Cambiar por otra receta parecida">${busy ? `<span class="spin"></span>` : svg(P.swap, 15)}CAMBIO</button>
    </div>`;
  }

  _dayFoot(week, d) {
    const sum = week.summary && week.summary.days[d];
    if (!sum || !sum.meals) return `<span>—</span>`;
    const pct = Math.min(100, Math.round((sum.kcal / sum.target) * 100));
    const cls = pct < 75 ? "low" : sum.kcal > sum.target * 1.15 ? "high" : "";
    const bal = BALANCE.map(([k, e, name]) => {
      const v = sum[k];
      if (v === null || v === undefined) return "";
      return `<span class="emoji ${v ? "" : "off"}" title="${name}: ${v ? "bien" : "poca"}">${e}</span>`;
    }).join("");
    const title = `Comida + cena: ≈ ${fmt(sum.kcal)} kcal por persona (objetivo ${fmt(sum.target)}). Proteína ${fmt(sum.protein)} g, verdura ${fmt(sum.veg)} g, hidratos ${fmt(sum.carbs)} g.`;
    return `<span title="${esc(title)}"><b>${fmt(sum.kcal)}</b> kcal</span>
      <span class="bar ${cls}" title="${esc(title)}"><i style="width:${pct}%"></i></span>
      ${bal ? `<span class="bal">${bal}</span>` : ""}`;
  }

  _extras(week) {
    const sum = week.summary;
    if (!sum || !sum.planned) return "";
    const st = this._state;
    const kcal = st.settings.kcal_day;
    const targets = sum.weekly
      .map((t) => {
        const [e, name, unit] = WEEKLY[t.id];
        const goal = t.min !== null && t.min !== undefined ? `mín. ${fmt(t.min)} ${unit}` : `máx. ${fmt(t.max)} ${unit}`;
        return `<div class="target ${t.ok ? "" : "bad"}"><span class="em">${e}</span><span class="txt"><b>${name}</b>${goal}</span><span class="v">${fmt(t.count, 1)}</span></div>`;
      })
      .join("");
    const balance = `<section class="panel">
      <h3><span class="em">⚖️</span>Equilibrio de la semana</h3>
      <p class="sub">Raciones por persona según las recomendaciones de la AESAN. Comida y cena suman ≈ ${fmt(sum.targets.lunch + sum.targets.dinner)} kcal al día (el 65 % de ${fmt(kcal)}); el resto, desayuno y meriendas.</p>
      <div class="targets">${targets}</div>
    </section>`;

    const people = this._people;
    const recipes = new Map(st.recipes.map((r) => [r.id, r]));
    const useChip = (d, meal, rid) => {
      const r = recipes.get(rid);
      if (!r) return "";
      const c = this._cat(r.category);
      return `<button class="use" style="${tone(c.color)}" data-action="open-slot" data-slot="${2 * d + MEALS.indexOf(meal)}"><b>${DAYS_SHORT[d]}${meal === "dinner" ? " · cena" : ""}</b><span>${esc(r.name)}</span></button>`;
    };
    const bases = sum.batch
      .map((g) => {
        const grams = g.amount && g.amount.grams;
        const amount = grams ? (grams >= 1000 ? `${fmt(grams / 1000, 1)} kg` : `${fmt(grams)} g`) : "";
        return `<div class="base"><div class="t"><span class="em">${this._iconFor(g.name)}</span>${esc(g.name)}${amount ? `<small>≈ ${amount} para ${plural(people, "persona", "personas")}</small>` : ""}</div>
          <div class="uses">${g.slots.map((s) => useChip(s[0], s[1], s[2])).join("")}</div></div>`;
      })
      .join("");
    const cook = sum.cook
      .map((c) => {
        const r = recipes.get(c.recipe_id);
        if (!r) return "";
        const cat = this._cat(r.category);
        const when = c.slots.map(([d, m]) => `${DAYS_SHORT[d]}${m === "dinner" ? " (cena)" : ""}${d >= 3 ? " ❄️" : ""}`).join(", ");
        const portions = c.slots.length * people;
        return `<div class="cook-row" style="${tone(cat.color)}"><span class="em">${esc(r.icon)}</span><span class="txt"><span class="nm">${esc(r.name)}</span><span class="when">${when}</span></span><span class="q">${plural(portions, "ración", "raciones")}</span></div>`;
      })
      .join("");
    const batchOn = st.settings.batch;
    const batch = `<section class="panel">
      <h3><span class="em">🧑‍🍳</span>Batch cooking del fin de semana</h3>
      <p class="sub">${sum.batch.length ? "Estos platos comparten elaboración: cocínala una vez y repártela." : batchOn ? "Esta semana no hay platos que compartan elaboración." : "La agrupación de platos está desactivada en ⚙️ Ajustes."}</p>
      ${bases ? `<div class="batch">${bases}</div>` : ""}
      <h4>Qué cocinar</h4>
      <div class="cook">${cook}</div>
      <div class="freeze"><span class="emoji">❄️</span><span>Lo cocinado aguanta 3–4 días en la nevera: lo que se come de jueves en adelante, mejor congelarlo y pasarlo a la nevera la víspera.</span></div>
    </section>`;
    return `<div class="extras">${balance}${batch}</div>`;
  }

  /* ---------- recetas */
  _renderRecipes() {
    const st = this._state;
    const q = norm(this._recipeQuery);
    const f = this._recipeFilter;
    const all = [...st.recipes].sort((a, b) => b.rating - a.rating || a.name.localeCompare(b.name, "es"));
    const list = all.filter((r) => {
      if (q && !norm(r.name).includes(q) && !r.ingredients.some((i) => norm(i.name).includes(q))) return false;
      if (f === "lunch" || f === "dinner") return r.meals.includes(f);
      if (f) return r.category === f;
      return true;
    });
    const count = (fn) => all.filter(fn).length;
    const chip = (id, label, n, style = "", cls = "") =>
      `<button class="chip ${cls}" style="${style}" data-action="rfilter" data-id="${id || ""}" aria-pressed="${String((f || "") === (id || ""))}">${label}<span class="n">${n}</span></button>`;
    const filters = [
      chip(null, "Todas", all.length),
      chip("lunch", "☀️ Comidas", count((r) => r.meals.includes("lunch"))),
      chip("dinner", "🌙 Cenas", count((r) => r.meals.includes("dinner"))),
      `<span class="sep"></span>`,
      ...st.categories.map((c) => chip(c.id, `<span class="dot"></span>${esc(c.name)}`, count((r) => r.category === c.id), tone(c.color), "cat")),
    ].join("");
    const cards = list
      .map((r) => {
        const cat = this._cat(r.category);
        return `<button class="rcard" style="${tone(cat.color)}" data-action="edit-recipe" data-id="${esc(r.id)}" aria-label="${esc(`${r.name}. ${cat.name}. ${r.rating} estrellas`)}">
          <span class="top"><span class="em">${esc(r.icon)}</span><span class="nm">${soft(r.name)}</span></span>
          ${stars(r.rating, 16)}
          <span class="meta"><span class="tag cat">${esc(cat.name)}</span>${r.meals.map((m) => `<span class="tag">${MEAL[m]}</span>`).join("")}<span>${this._kcal(r)}</span><span>${plural(r.ingredients.length, "ingrediente", "ingredientes")}</span></span>
        </button>`;
      })
      .join("");
    const active = this.shadowRoot.activeElement;
    const searchHasFocus = active && active.dataset && active.dataset.field === "rquery";
    this.$.page.innerHTML = `
      <div class="rbar">
        <label class="searchbar">${svg(P.search, 20)}<input data-field="rquery" type="search" placeholder="Buscar receta o ingrediente…" aria-label="Buscar receta" value="${esc(this._recipeQuery)}"></label>
        <button class="btn" data-action="new-recipe">${svg(P.plus, 18)}Nueva receta</button>
      </div>
      ${all.length ? `<div class="filters" role="toolbar" aria-label="Filtrar recetas">${filters}</div>` : ""}
      ${
        !all.length
          ? `<div class="empty"><div class="big emoji">📖</div><strong>Tu recetario está vacío</strong>
              Crea una receta con sus ingredientes, di si es para comida o cena, qué la compone sobre todo (marca el color) y cuánto te gusta.
              <div class="actions-row"><button class="btn" data-action="new-recipe">${svg(P.plus, 18)}Crear receta</button><button class="btn outline" data-action="examples">Añadir recetas de ejemplo</button></div></div>`
          : list.length
            ? `<div class="rgrid">${cards}</div>`
            : `<div class="empty"><div class="big emoji">🔎</div><strong>Nada por aquí</strong>Ninguna receta coincide con la búsqueda.</div>`
      }`;
    if (searchHasFocus) {
      const input = this.$.page.querySelector("[data-field=rquery]");
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }

  /* ------------------------------------------------------------- eventos */
  _onClick(e) {
    const el = e.target.closest("[data-action]");
    if (!el || el.disabled) return;
    const { action, id } = el.dataset;
    const slot = el.dataset.slot !== undefined ? Number(el.dataset.slot) : null;
    switch (action) {
      case "menu":
        this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        break;
      case "view":
        this._view = id;
        this._render();
        this.$.scroller.scrollTop = 0;
        break;
      case "settings":
        this._openSettings();
        break;
      case "week":
        this._week = id === "0" ? this._state.current_week : shiftWeek(this._week, Number(id));
        this._render();
        break;
      case "generate":
        this._generate();
        break;
      case "check":
        this._check();
        break;
      case "change":
        this._change(slot);
        break;
      case "open-slot":
        this._openSlot(slot);
        break;
      case "rfilter":
        this._recipeFilter = id || null;
        this._render();
        break;
      case "new-recipe":
        this._openRecipe(null);
        break;
      case "edit-recipe":
        this._openRecipe(id);
        break;
      case "examples":
        this._examples();
        break;
      case "snack":
        clearTimeout(this._snackTimer);
        this.$.snack.classList.remove("show");
        if (this._snackFn) this._snackFn();
        this._snackFn = null;
        break;
      case "close":
        this.$.dialog.close();
        break;
      default:
        if (this._sheet) this._sheetAction(action, el);
    }
  }

  _onKey(e) {
    const t = e.target;
    if (this._sheet === "recipe" && e.key === "Enter" && t.dataset && t.dataset.ing !== undefined && t.tagName === "INPUT") {
      e.preventDefault();
      this._ingEnter(Number(t.dataset.ing));
      return;
    }
    if (this._sheet === "picker" && e.key === "Enter" && t.dataset && t.dataset.field === "pquery") {
      const first = this.$.dialog.querySelector(".pick");
      if (first) first.click();
      return;
    }
    if (!this._sheet && this._view === "menu" && (e.key === "ArrowLeft" || e.key === "ArrowRight") && !/INPUT|TEXTAREA|SELECT/.test(t.tagName)) {
      this._week = shiftWeek(this._week, e.key === "ArrowLeft" ? -1 : 1);
      this._render();
    }
  }

  _onInput(e) {
    const t = e.target;
    const ds = t.dataset || {};
    if (ds.field === "rquery" && e.type === "input") {
      this._recipeQuery = t.value;
      this._renderRecipes();
    } else if (ds.field === "pquery" && e.type === "input") {
      this._pickQuery = t.value;
      this._renderPicker(true);
    } else if (this._sheet === "check" && ds.check !== undefined && e.type === "change") {
      if (t.checked) this._selected.add(ds.check);
      else this._selected.delete(ds.check);
      this._renderCheck();
    } else if (this._sheet === "recipe") this._draftInput(t, e.type);
    else if (this._sheet === "settings") this._settingInput(t, e.type);
  }

  /* -------------------------------------------------------- acciones */
  async _ws(msg, quiet = false) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      if (!quiet) this._toast((err && err.message) || String(err));
      throw err;
    }
  }

  _restoreSlot(key, i, previous) {
    const slots = this._weekData(key).slots.map((s) => ({ ...s }));
    slots[i] = previous;
    return this._ws({ type: "menu_semanal/week/restore", week: key, slots }).catch(() => {});
  }

  async _generate() {
    if (!this._state.recipes.length) {
      this._toast("Primero crea algunas recetas");
      return;
    }
    const key = this._week;
    this._busy.generate = true;
    this._render();
    try {
      const res = await this._ws({ type: "menu_semanal/week/generate", week: key });
      for (let i = 0; i < 14; i++) this._entered.add(i);
      if (this._missing && this._missing.week === key) this._missing = null;
      const had = res.previous.some((s) => s.recipe_id || s.free);
      this._toast(
        `Menú de la semana ${weekNumber(key)} generado`,
        had ? "Deshacer" : null,
        had ? () => this._ws({ type: "menu_semanal/week/restore", week: key, slots: res.previous }).catch(() => {}) : null
      );
    } catch (err) {
      if (err && err.code === "no_recipes") this._view = "recipes";
    } finally {
      this._busy.generate = false;
      this._render();
    }
  }

  async _change(i) {
    const key = this._week;
    if (this._busy[`slot:${i}`]) return;
    this._busy[`slot:${i}`] = true;
    this._render();
    try {
      const res = await this._ws({ type: "menu_semanal/slot/change", week: key, slot: i });
      this._entered.add(i);
      const before = this._recipe(res.previous.recipe_id);
      const after = this._recipe(res.slot.recipe_id);
      if (after) {
        this._toast(before ? `${before.name} → ${after.name}` : `Propuesto: ${after.name}`, "Deshacer", () =>
          this._restoreSlot(key, i, res.previous)
        );
      }
    } catch (err) {
      /* el aviso ya se ha mostrado */
    } finally {
      delete this._busy[`slot:${i}`];
      this._render();
    }
  }

  async _check() {
    const key = this._week;
    this._busy.check = true;
    this._render();
    try {
      const res = await this._ws({ type: "menu_semanal/check", week: key });
      const slots = new Set();
      for (const item of res.items) {
        if (item.status !== "missing") continue;
        for (const r of item.recipes) slots.add(2 * r.day + MEALS.indexOf(r.meal));
      }
      this._missing = { week: key, slots };
      this._checkResult = res;
      this._selected = new Set(res.items.filter((i) => i.status === "missing").map((i) => i.key));
      this._openSheet("check", "", true);
      this._renderCheck();
    } catch (err) {
      /* aviso mostrado */
    } finally {
      this._busy.check = false;
      this._render();
    }
  }

  async _examples() {
    const res = await this._ws({ type: "menu_semanal/recipes/examples" }).catch(() => null);
    if (!res) return;
    this._toast(res.added ? plural(res.added, "receta de ejemplo añadida", "recetas de ejemplo añadidas") : "Ya tenías todas las recetas de ejemplo");
  }

  _toast(text, label, fn) {
    const s = this.$.snack;
    s.querySelector("span").textContent = text;
    const b = s.querySelector("button");
    b.hidden = !label;
    b.textContent = label || "";
    this._snackFn = fn || null;
    s.classList.add("show");
    clearTimeout(this._snackTimer);
    this._snackTimer = setTimeout(() => {
      s.classList.remove("show");
      this._snackFn = null;
    }, 6000);
  }

  /* -------------------------------------------------------------- hojas */
  _openSheet(kind, html, wide = false) {
    const d = this.$.dialog;
    this._sheet = kind;
    d.className = wide ? "wide" : "";
    d.innerHTML = html;
    if (!d.open) d.showModal();
  }

  /* ---------- plato de la semana */
  _openSlot(i) {
    this._slotIndex = i;
    this._slotWeek = this._week;
    this._openSheet("slot", "");
    this._renderSlotSheet();
  }

  _renderSlotSheet() {
    const i = this._slotIndex;
    const key = this._slotWeek;
    const week = this._weekData(key);
    const slot = week.slots[i];
    const d = i >> 1;
    const meal = MEALS[i % 2];
    const date = dayOf(key, d);
    const when = `${DAYS[d]} ${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} · ${MEAL[meal]}`;
    const r = slot.recipe_id && !slot.free ? this._recipe(slot.recipe_id) : null;
    const busy = !!this._busy[`slot:${i}`];
    const dlg = this.$.dialog;
    if (!r) {
      dlg.innerHTML = `
        <div class="sheet-head"><span class="big-em emoji" style="${tone("#9e9e9e")}">${slot.free ? "🍴" : "🍽️"}</span>
          <div class="titles"><h2>${slot.free ? "Libre" : "Sin plato"}</h2><span>${when}</span></div>
          <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
        <div class="stack" style="border-top:0">
          <p>${slot.free ? "Este hueco queda libre (comer fuera, sobras…). Al pulsar «Generar» no se rellena." : "Elige una receta o deja que se proponga una que encaje con el resto de la semana."}</p>
          <button class="btn" data-action="change" data-slot="${i}" ${busy ? "disabled" : ""}>${busy ? `<span class="spin"></span>` : svg(P.wand, 18)}Proponer una receta</button>
          <button class="btn tonal" data-action="pick">${svg(P.list, 18)}Elegir receta</button>
          ${slot.free ? `<button class="btn outline" data-action="unfree">Quitar «libre»</button>` : `<button class="btn outline" data-action="free">🍴 Dejar libre (comer fuera)</button>`}
        </div>`;
      return;
    }
    const cat = this._cat(r.category);
    const info = r.info || {};
    const factor = this._people / Math.max(1, r.servings || 1);
    const ings = r.ingredients
      .map((g) => {
        const q = g.unit === "gusto" || g.qty === null || g.qty === undefined ? "al gusto" : `${fmt(g.qty * factor, 1)} ${g.unit}`;
        return `<li><span>${esc(g.name)}</span><span class="q">${q}</span></li>`;
      })
      .join("");
    const shared = this._sharedBases(week, i)
      .map((g) => {
        const others = g.slots
          .filter((s) => !(s[0] === d && s[1] === meal))
          .map((s) => {
            const o = this._recipe(s[2]);
            return `${DAYS[s[0]].toLowerCase()}${s[1] === "dinner" ? " (cena)" : ""}: ${o ? o.name : "?"}`;
          });
        return `<div class="notice info"><span class="emoji">🔗</span><span><b>${esc(g.name)}</b>: se cocina una vez para este plato y para ${esc(others.join(" y "))}.</span></div>`;
      })
      .join("");
    const macros =
      info.protein !== null && info.protein !== undefined
        ? `<span>Proteína <b>${fmt(info.protein)} g</b></span><span>Hidratos <b>${fmt(info.carbs)} g</b></span><span>Grasa <b>${fmt(info.fat)} g</b></span><span>Verdura <b>${fmt(info.veg_g)} g</b></span>`
        : "";
    dlg.innerHTML = `
      <div class="sheet-head" style="${tone(cat.color)}"><span class="big-em emoji">${esc(r.icon)}</span>
        <div class="titles"><h2>${esc(r.name)}</h2><span><i class="dot"></i>${esc(cat.name)} · ${when}</span></div>
        <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
      <div class="sheet-body">
        <div>${stars(r.rating, 20)}<span class="hint-inline">${STAR_HINT[r.rating]}</span></div>
        <div class="kv"><span><b>${info.kcal ? `≈ ${fmt(info.kcal)}` : "?"}</b> kcal/ración</span>${macros}</div>
        ${shared}
        <h4>Ingredientes para ${plural(this._people, "persona", "personas")}</h4>
        <ul class="ings">${ings || `<li><span class="help">Sin ingredientes</span></li>`}</ul>
        ${r.notes ? `<h4>Preparación</h4><p class="notes">${esc(r.notes)}</p>` : ""}
      </div>
      <div class="stack">
        <button class="btn" data-action="change" data-slot="${i}" ${busy ? "disabled" : ""}>${busy ? `<span class="spin"></span>` : svg(P.swap, 18)}CAMBIO · otra receta parecida</button>
        <div class="row2">
          <button class="btn tonal" data-action="pick">${svg(P.list, 18)}Elegir otra</button>
          <button class="btn tonal" data-action="lock" aria-pressed="${slot.locked}">${svg(P.pin, 18)}${slot.locked ? "Quitar fijado" : "Fijar"}</button>
        </div>
        <div class="row2">
          <button class="btn outline" data-action="free">🍴 Dejar libre</button>
          <button class="btn outline" data-action="edit-recipe" data-id="${esc(r.id)}">${svg(P.pencil, 18)}Editar receta</button>
        </div>
        ${slot.locked ? `<p>📌 Fijado: se mantiene al pulsar «Generar».</p>` : ""}
      </div>`;
  }

  /* ---------- elegir receta para un hueco */
  _openPicker() {
    this._pickQuery = "";
    this._openSheet("picker", "");
    this._renderPicker(false);
  }

  _renderPicker(listOnly) {
    const i = this._slotIndex;
    const meal = MEALS[i % 2];
    const week = this._weekData(this._slotWeek);
    const current = week.slots[i].recipe_id;
    const q = norm(this._pickQuery || "");
    const recipes = this._state.recipes
      .filter((r) => r.meals.includes(meal))
      .filter((r) => !q || norm(r.name).includes(q))
      .sort((a, b) => b.rating - a.rating || a.name.localeCompare(b.name, "es"));
    const list = recipes
      .map((r) => {
        const c = this._cat(r.category);
        return `<button class="pick${r.id === current ? " current" : ""}" style="${tone(c.color)}" data-action="pick-recipe" data-id="${esc(r.id)}">
          <span class="em">${esc(r.icon)}</span><span class="txt"><span class="nm">${esc(r.name)}</span><span class="sub">${stars(r.rating, 12)}<span>${esc(c.name)}</span><span>${this._kcal(r)}</span></span></span></button>`;
      })
      .join("");
    const body = list || `<p class="help">No hay recetas para la ${MEAL[meal].toLowerCase()}${q ? " con ese nombre" : ""}.</p>`;
    const box = this.$.dialog.querySelector(".pick-list");
    if (listOnly && box) {
      box.innerHTML = body;
      return;
    }
    this.$.dialog.innerHTML = `
      <div class="sheet-head"><div class="titles"><h2>Elegir ${MEAL[meal].toLowerCase()}</h2><span>${DAYS[i >> 1]} · queda fijada al generar</span></div>
        <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
      <div class="sheet-body">
        <label class="searchbar">${svg(P.search, 20)}<input data-field="pquery" type="search" placeholder="Buscar…" aria-label="Buscar receta" value="${esc(this._pickQuery || "")}"></label>
        <div class="pick-list">${body}</div>
      </div>`;
    if (matchMedia("(hover:hover)").matches) this.$.dialog.querySelector("[data-field=pquery]").focus();
  }

  /* ---------- comprobar la despensa */
  _renderCheck() {
    const res = this._checkResult;
    const items = res.items;
    const missing = items.filter((i) => i.status === "missing");
    const inCesta = items.filter((i) => i.status === "in_cesta");
    const unsure = items.filter((i) => i.status === "unsure");
    const fine = items.filter((i) => i.status === "ok" || i.status === "untracked");
    const sel = this._selected;
    const n = missing.filter((i) => sel.has(i.key)).length;
    const forText = (item) => {
      const seen = new Set();
      return item.recipes
        .filter((r) => {
          const k = `${r.day}:${r.meal}`;
          if (seen.has(k)) return false;
          seen.add(k);
          return true;
        })
        .map((r) => `${DAYS_SHORT[r.day]}${r.meal === "dinner" ? " (cena)" : ""}: ${r.recipe}`)
        .join(" · ");
    };
    const row = (item, kind) => {
      const have =
        item.stock === 0 ? "; no queda en la Despensa" : item.have_text !== null && item.have_text !== undefined ? `; tienes ${item.have_text}` : "";
      let lead = "";
      let right = "";
      if (kind === "missing") {
        lead = `<input type="checkbox" data-check="${esc(item.key)}" ${sel.has(item.key) ? "checked" : ""} aria-label="Añadir ${esc(item.name)}">`;
        right = item.note ? `<span class="qty" title="Lo que se añade a la Cesta">${esc(item.note)}</span>` : "";
      } else if (kind === "in_cesta") right = `<span class="qty cesta">En la Cesta</span>`;
      else if (kind === "ok") right = `<span class="qty ok">${item.status === "untracked" ? "Básico" : "Hay"}</span>`;
      const eq =
        kind === "unsure"
          ? `<span class="eq">1 ${esc(item.unit_label || "ud")} de ${esc(item.name)} ≈ <input type="number" min="1" step="any" inputmode="decimal" data-eq="${esc(item.name)}" placeholder="g" aria-label="Gramos por unidad"> g <button class="btn tonal" data-action="save-eq" data-name="${esc(item.name)}">Guardar</button></span>`
          : "";
      const sub = item.status === "untracked" ? "No se controla en la Despensa: se da por bueno" : `Necesitas ${item.need_text}${have}`;
      return `<div class="crow ${kind === "missing" ? "missing" : ""} ${kind === "missing" && !sel.has(item.key) ? "off" : ""}">${lead}
        <span class="em emoji">${esc(item.icon || "🛒")}</span>
        <span class="txt"><span class="nm">${esc(item.name)}</span><span class="sub">${esc(sub)}</span><span class="for">${esc(forText(item))}</span>${eq}</span>${right}</div>`;
    };
    const subtitle = [
      `Semana ${weekNumber(res.week)}`,
      `para ${plural(res.people, "persona", "personas")}`,
      res.from_day > 0 && res.from_day < 7 ? `desde hoy (${DAYS[res.from_day].toLowerCase()})` : "",
    ]
      .filter(Boolean)
      .join(" · ");
    const notices = [
      !res.despensa
        ? `<div class="notice"><span class="emoji">🗄️</span><span>Despensa no está instalada: no se sabe qué tienes, así que aparece todo lo que pide el menú (salvo lo básico).</span></div>`
        : "",
      !res.cesta ? `<div class="notice"><span class="emoji">🧺</span><span>Cesta no está instalada: puedes ver la lista, pero no añadirla.</span></div>` : "",
      res.from_day >= 7 ? `<div class="notice info"><span class="emoji">🗓️</span><span>Esta semana ya ha pasado.</span></div>` : "",
    ].join("");
    let body;
    if (!missing.length) {
      body = `<div class="allgood"><span class="big">${svg(P.check, 36)}</span><strong>Tienes todo lo necesario</strong>
        <p>${inCesta.length ? `${plural(inCesta.length, "ingrediente ya está", "ingredientes ya están")} en la Cesta.` : "No hace falta añadir nada a la Cesta."}</p></div>`;
    } else {
      body = `<div class="check-list">${missing.map((i) => row(i, "missing")).join("")}</div>`;
    }
    if (inCesta.length) body += `<h4>Ya en la Cesta</h4><div class="check-list">${inCesta.map((i) => row(i, "in_cesta")).join("")}</div>`;
    if (unsure.length)
      body += `<h4>Sin comprobar la cantidad</h4><p class="help" style="margin:0 2px 8px">Queda alguno en la Despensa, pero no se sabe cuánto pesa una unidad. Dilo una vez y se tendrá en cuenta siempre.</p><div class="check-list">${unsure.map((i) => row(i, "unsure")).join("")}</div>`;
    if (fine.length)
      body += `<details><summary>Hay suficiente (${fine.length})${svg(P.chevron, 20)}</summary><div class="check-list">${fine.map((i) => row(i, "ok")).join("")}</div></details>`;
    const open = this.$.dialog.querySelector("details[open]");
    this.$.dialog.innerHTML = `
      <div class="sheet-head"><span class="big-em emoji" style="${tone("#f5a400")}">🧺</span>
        <div class="titles"><h2>Ingredientes que deben agregarse a la cesta</h2><span>${subtitle}</span></div>
        <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
      <div class="sheet-body">${notices}${body}</div>
      <div class="sheet-foot">
        ${missing.length > 1 ? `<button class="btn quiet" data-action="check-all">${n === missing.length ? "Quitar todos" : "Marcar todos"}</button>` : ""}
        <span class="grow"></span>
        <button class="btn quiet" data-action="close">${missing.length ? "Cancelar" : "Cerrar"}</button>
        ${missing.length ? `<button class="btn" data-action="add-cesta" ${!n || !res.cesta || this._busy.cesta ? "disabled" : ""}>${this._busy.cesta ? `<span class="spin"></span>` : svg(P.cartPlus, 18)}Añadir${n ? ` (${n})` : ""}</button>` : ""}
      </div>`;
    if (open) {
      const d = this.$.dialog.querySelector("details");
      if (d) d.open = true;
    }
  }

  async _addToCesta() {
    const res = this._checkResult;
    const items = res.items
      .filter((i) => i.status === "missing" && this._selected.has(i.key))
      .map((i) => ({ name: i.name, note: i.note || "", icon: i.icon || "", department: i.department || "" }));
    if (!items.length) return;
    this._busy.cesta = true;
    this._renderCheck();
    try {
      const out = await this._ws({ type: "menu_semanal/cesta/add", items });
      const n = out.added.length;
      this._busy.cesta = false;
      this.$.dialog.close();
      this._toast(n ? `${plural(n, "ingrediente añadido", "ingredientes añadidos")} a la Cesta` : "Ya estaba todo en la Cesta");
      if (this._missing && this._missing.week === res.week) this._missing = null;
      this._render();
    } catch (err) {
      this._busy.cesta = false;
      if (this._sheet === "check") this._renderCheck();
    }
  }

  async _saveEquivalence(name) {
    const input = [...this.$.dialog.querySelectorAll("[data-eq]")].find((i) => i.dataset.eq === name);
    const grams = Number(String((input && input.value) || "").replace(",", "."));
    if (!grams || grams <= 0) {
      if (input) input.focus();
      return;
    }
    try {
      await this._ws({ type: "menu_semanal/equivalence/set", name, grams });
      const res = await this._ws({ type: "menu_semanal/check", week: this._checkResult.week });
      const before = new Set(this._checkResult.items.filter((i) => i.status === "missing").map((i) => i.key));
      this._checkResult = res;
      for (const i of res.items) if (i.status === "missing" && !before.has(i.key)) this._selected.add(i.key);
      this._renderCheck();
    } catch (err) {
      /* aviso mostrado */
    }
  }

  /* ---------- editor de recetas */
  _openRecipe(id) {
    const r = id ? this._recipe(id) : null;
    this._draft = r
      ? {
          id: r.id,
          name: r.name,
          icon: r.icon,
          meals: [...r.meals],
          category: r.category,
          categoryTouched: true,
          rating: r.rating,
          servings: r.servings,
          ingredients: r.ingredients.map((g) => ({ name: g.name, qty: g.qty ?? "", unit: g.unit })),
          base: r.base || "",
          kcal: r.kcal || "",
          notes: r.notes || "",
          info: r.info,
          confirmDelete: false,
          error: "",
        }
      : {
          id: null,
          name: "",
          icon: "",
          meals: ["lunch"],
          category: null,
          categoryTouched: false,
          rating: 3,
          servings: 4,
          ingredients: [{ name: "", qty: "", unit: "g" }],
          base: "",
          kcal: "",
          notes: "",
          info: null,
          confirmDelete: false,
          error: "",
        };
    this._openSheet("recipe", this._recipeHTML(), true);
    this._renderDraftParts();
    if (!r && matchMedia("(hover:hover)").matches) this.$.dialog.querySelector(".name-input").focus();
    this._estimate();
  }

  _ingredientNames() {
    if (this._namesFor === this._state) return this._names;
    const names = new Map();
    const add = (n) => {
      const k = norm(n);
      if (k && !names.has(k)) names.set(k, cap(n));
    };
    for (const i of this._state.despensa.items || []) add(i.name);
    for (const e of this._catalog || []) if (FOOD_DEPTS.has(e.department)) add(e.name);
    for (const f of this._foods || []) add(f.name);
    this._names = [...names.values()].sort((a, b) => a.localeCompare(b, "es"));
    this._namesFor = this._state;
    return this._names;
  }

  _recipeHTML() {
    const dr = this._draft;
    const emojis = [...new Set(EMOJI.match(/\p{Extended_Pictographic}️?/gu))];
    const bases = new Set();
    for (const r of this._state.recipes) {
      if (r.base) bases.add(r.base);
      for (const b of (r.info && r.info.bases) || []) bases.add(b.name);
    }
    return `
      <div class="edit-head">
        <button class="big-em emoji" data-action="emojis" aria-label="Cambiar icono" title="Cambiar icono"></button>
        <input class="name-input" data-draft="name" maxlength="80" placeholder="Nombre de la receta" aria-label="Nombre de la receta" value="${esc(dr.name)}" enterkeyhint="next">
        <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button>
      </div>
      <div class="emoji-grid" hidden>${emojis.map((e) => `<button type="button" data-action="pick-emoji" data-emoji="${e}">${e}</button>`).join("")}</div>
      <div class="sheet-body">
        <div class="field"><div class="lbl">Para</div><div class="chips meals"></div></div>
        <div class="field"><div class="lbl">Componente principal <small>· marca el color de la receta</small></div><div class="chips cats"></div></div>
        <div class="field"><div class="lbl">Valoración</div><div class="rate"></div></div>
        <div class="field"><div class="lbl">Raciones que salen</div>
          <div class="mini"><button class="icon-btn" data-action="serv-dec" aria-label="Menos raciones">${svg(P.minus, 18)}</button><output class="serv"></output><button class="icon-btn" data-action="serv-inc" aria-label="Más raciones">${svg(P.plus, 18)}</button></div>
          <p class="help">Las cantidades de los ingredientes son para estas raciones; al comprobar la despensa se ajustan a ${plural(this._people, "persona", "personas")}.</p></div>
        <div class="field"><div class="lbl">Ingredientes</div>
          <div class="ing-list"></div>
          <button class="btn quiet add-ing" data-action="add-ing">${svg(P.plus, 18)}Añadir ingrediente</button>
          <div class="estimate"></div>
        </div>
        <div class="field"><div class="lbl">Elaboración compartida <small>· batch cooking</small></div>
          <input class="input" data-draft="base" list="ms-bases" maxlength="40" placeholder="Por ejemplo: Sofrito de tomate" value="${esc(dr.base)}">
          <p class="help bases-help"></p>
        </div>
        <div class="field"><div class="lbl">Preparación <small>· opcional</small></div>
          <textarea data-draft="notes" maxlength="4000" placeholder="Pasos, trucos, tiempo de horno…">${esc(dr.notes)}</textarea></div>
        <datalist id="ms-ingredients">${this._ingredientNames().map((n) => `<option value="${esc(n)}"></option>`).join("")}</datalist>
        <datalist id="ms-bases">${[...bases].map((n) => `<option value="${esc(n)}"></option>`).join("")}</datalist>
      </div>
      <div class="sheet-foot"></div>`;
  }

  _renderDraftParts(parts = ["icon", "meals", "cats", "rate", "serv", "ings", "foot", "estimate"]) {
    const dr = this._draft;
    const d = this.$.dialog;
    if (!dr || this._sheet !== "recipe") return;
    const suggested = dr.info && dr.info.suggested_category;
    const cat = this._cat(dr.categoryTouched ? dr.category : suggested || "otros");
    if (parts.includes("icon")) {
      const b = d.querySelector(".edit-head .big-em");
      b.textContent = dr.icon || cat.icon;
      b.setAttribute("style", tone(cat.color));
    }
    if (parts.includes("meals")) {
      d.querySelector(".meals").innerHTML = MEALS.map(
        (m) => `<button class="chip" data-action="toggle-meal" data-id="${m}" aria-pressed="${dr.meals.includes(m)}">${m === "lunch" ? "☀️" : "🌙"} ${MEAL[m]}s</button>`
      ).join("");
    }
    if (parts.includes("cats")) {
      const chosen = dr.categoryTouched ? dr.category : suggested;
      d.querySelector(".cats").innerHTML = this._state.categories
        .map(
          (c) =>
            `<button class="chip cat" style="${tone(c.color)}" data-action="pick-cat" data-id="${c.id}" aria-pressed="${c.id === chosen}"><span class="dot"></span>${esc(c.name)}${!dr.categoryTouched && c.id === suggested ? ` <span class="auto">auto</span>` : ""}</button>`
        )
        .join("");
    }
    if (parts.includes("rate")) {
      d.querySelector(".rate").innerHTML = `<span class="stars" role="radiogroup" aria-label="Valoración">${[1, 2, 3, 4, 5]
        .map(
          (n) =>
            `<button type="button" class="${n <= dr.rating ? "on" : "off"}" data-action="rate" data-id="${n}" role="radio" aria-checked="${n === dr.rating}" aria-label="${n} estrella${n === 1 ? "" : "s"}">${svg(P.star, 30)}</button>`
        )
        .join("")}</span><span class="hint">${STAR_HINT[dr.rating]}</span>`;
    }
    if (parts.includes("serv")) d.querySelector(".serv").textContent = dr.servings;
    if (parts.includes("ings")) {
      d.querySelector(".ing-list").innerHTML = dr.ingredients
        .map(
          (g, n) => `<div class="ing">
            <input class="input" data-ing="${n}" data-f="name" list="ms-ingredients" placeholder="Ingrediente" aria-label="Ingrediente" value="${esc(g.name)}" enterkeyhint="next" autocomplete="off">
            <input class="input" data-ing="${n}" data-f="qty" type="number" min="0" step="any" inputmode="decimal" placeholder="${g.unit === "gusto" ? "" : "Cant."}" aria-label="Cantidad" value="${g.unit === "gusto" ? "" : esc(g.qty)}" ${g.unit === "gusto" ? "disabled" : ""}>
            <select data-ing="${n}" data-f="unit" aria-label="Unidad">${UNITS.map(([v, l]) => `<option value="${v}" ${v === g.unit ? "selected" : ""}>${l}</option>`).join("")}</select>
            <button class="icon-btn" data-action="del-ing" data-id="${n}" aria-label="Quitar ingrediente">${svg(P.close, 18)}</button>
          </div>`
        )
        .join("");
    }
    if (parts.includes("estimate")) this._renderEstimate();
    if (parts.includes("foot")) {
      const foot = d.querySelector(".sheet-foot");
      if (dr.confirmDelete) {
        foot.innerHTML = `<span style="font-size:14px">¿Borrar «${esc(dr.name)}»? Se quitará del menú de esta semana y las siguientes.</span><span class="grow"></span>
          <button class="btn quiet" data-action="cancel-delete">No</button><button class="btn" style="background:var(--bad)" data-action="delete-recipe">Borrar</button>`;
      } else {
        foot.innerHTML = `${dr.error ? `<span class="err">${esc(dr.error)}</span>` : ""}
          ${dr.id ? `<button class="btn danger" data-action="ask-delete">${svg(P.trash, 18)}Borrar</button>` : ""}
          <span class="grow"></span><button class="btn quiet" data-action="close">Cancelar</button>
          <button class="btn" data-action="save-recipe" ${this._busy.save ? "disabled" : ""}>${svg(P.check, 18)}Guardar</button>`;
      }
    }
  }

  _renderEstimate() {
    const dr = this._draft;
    const box = this.$.dialog.querySelector(".estimate");
    const help = this.$.dialog.querySelector(".bases-help");
    if (!box) return;
    const info = dr.info;
    const kcal = dr.kcal ? Number(dr.kcal) : info && info.kcal_estimated;
    const target = this._state.settings.kcal_day;
    const main = kcal
      ? `<span class="kcal">≈ ${fmt(kcal)} kcal</span><span>por ración${dr.kcal ? " (puesto a mano)" : ""}</span>`
      : `<span>Añade ingredientes con su cantidad para estimar las calorías.</span>`;
    const macros =
      info && info.protein !== null && info.protein !== undefined
        ? `<span>Proteína <b>${fmt(info.protein)} g</b></span><span>Hidratos <b>${fmt(info.carbs)} g</b></span><span>Grasa <b>${fmt(info.fat)} g</b></span><span>Verdura <b>${fmt(info.veg_g)} g</b></span>`
        : "";
    const unknown = info && info.unknown && info.unknown.length ? `<div>Sin datos (no cuentan): ${esc(info.unknown.join(", "))}.</div>` : "";
    const focused = this.shadowRoot.activeElement && this.shadowRoot.activeElement.dataset && this.shadowRoot.activeElement.dataset.draft === "kcal";
    if (focused) {
      box.querySelector(".row").innerHTML = main;
      return;
    }
    box.innerHTML = `<div class="row">${main}</div>${macros ? `<div class="row">${macros}</div>` : ""}${unknown}
      <div class="manual"><span>Ajustar kcal por ración a mano</span><input class="input" data-draft="kcal" type="number" min="0" max="3000" inputmode="numeric" placeholder="auto" value="${esc(dr.kcal)}" aria-label="kcal por ración"></div>
      <div style="margin-top:6px">Referencia por persona: comida ≈ ${fmt(target * 0.35)} kcal, cena ≈ ${fmt(target * 0.3)} kcal.</div>`;
    if (help) {
      const auto = ((info && info.bases) || []).filter((b) => norm(b.name) !== norm(dr.base));
      help.innerHTML = `Recetas con la misma elaboración se cocinan juntas el fin de semana.${
        auto.length
          ? ` Además, esta se agrupa sola con otras que lleven <b>${esc(auto.map((b) => b.name.toLowerCase()).join(", "))}</b>.`
          : " Si la dejas vacía, se detecta por los ingredientes (carne picada, pollo, garbanzos, arroz…)."
      }`;
    }
  }

  _estimate() {
    clearTimeout(this._estTimer);
    this._estTimer = setTimeout(async () => {
      const dr = this._draft;
      if (!dr) return;
      try {
        const info = await this._ws(
          {
            type: "menu_semanal/recipe/estimate",
            servings: dr.servings,
            ingredients: dr.ingredients
              .filter((g) => g.name.trim())
              .map((g) => ({ name: g.name, qty: g.qty === "" || g.unit === "gusto" ? null : Number(g.qty), unit: g.unit })),
            base: dr.base,
            kcal: dr.kcal === "" ? null : Number(dr.kcal),
          },
          true
        );
        if (this._draft !== dr) return;
        dr.info = info;
        this._renderDraftParts(["estimate", "cats", "icon"]);
      } catch (err) {
        /* sin estimación */
      }
    }, 280);
  }

  _draftInput(t, type) {
    const dr = this._draft;
    if (!dr) return;
    if (t.dataset.draft) {
      dr[t.dataset.draft] = t.value;
      if (t.dataset.draft === "name" && dr.error) {
        dr.error = "";
        this._renderDraftParts(["foot"]);
      }
      if (t.dataset.draft === "kcal" || t.dataset.draft === "base") this._estimate();
      return;
    }
    if (t.dataset.ing !== undefined) {
      const g = dr.ingredients[Number(t.dataset.ing)];
      if (!g) return;
      g[t.dataset.f] = t.value;
      if (t.dataset.f === "unit" && type === "change") {
        if (t.value === "gusto") g.qty = "";
        this._renderDraftParts(["ings"]);
      }
      this._estimate();
    }
  }

  _ingEnter(n) {
    const dr = this._draft;
    if (n === dr.ingredients.length - 1) dr.ingredients.push({ name: "", qty: "", unit: "g" });
    this._renderDraftParts(["ings"]);
    const next = this.$.dialog.querySelector(`[data-ing="${n + 1}"][data-f=name]`);
    if (next) next.focus();
  }

  async _saveRecipe() {
    const dr = this._draft;
    const name = cap(dr.name);
    if (!name) {
      dr.error = "Ponle un nombre a la receta";
      this._renderDraftParts(["foot"]);
      this.$.dialog.querySelector(".name-input").focus();
      return;
    }
    if (!dr.meals.length) {
      dr.error = "Elige si es para comidas, para cenas o para las dos";
      this._renderDraftParts(["foot"]);
      return;
    }
    const msg = {
      type: "menu_semanal/recipe/save",
      name,
      icon: dr.icon || "",
      meals: dr.meals,
      category: dr.categoryTouched ? dr.category : (dr.info && dr.info.suggested_category) || null,
      rating: dr.rating,
      servings: dr.servings,
      ingredients: dr.ingredients
        .filter((g) => g.name.trim())
        .map((g) => ({ name: g.name.trim(), qty: g.unit === "gusto" || g.qty === "" ? null : Number(g.qty), unit: g.unit })),
      base: dr.base || "",
      kcal: dr.kcal === "" ? null : Number(dr.kcal),
      notes: dr.notes || "",
    };
    if (dr.id) msg.recipe_id = dr.id;
    this._busy.save = true;
    this._renderDraftParts(["foot"]);
    try {
      await this._ws(msg, true);
      this._busy.save = false;
      this.$.dialog.close();
      this._toast(dr.id ? "Receta guardada" : `Receta creada: ${name}`);
    } catch (err) {
      this._busy.save = false;
      dr.error = (err && err.message) || String(err);
      if (this._sheet === "recipe") this._renderDraftParts(["foot"]);
    }
  }

  /* ---------- ajustes */
  _openSettings() {
    this._openSheet("settings", "");
    this._renderSettings();
  }

  _renderSettings() {
    const st = this._state;
    if (!st) return;
    const s = st.settings;
    const d = this.$.dialog;
    const active = this.shadowRoot.activeElement;
    if (active && active.dataset && (active.dataset.setting === "kcal_day" || active.dataset.color) && d.querySelector(".settings")) return;
    const scroll = d.querySelector(".sheet-body") ? d.querySelector(".sheet-body").scrollTop : 0;
    const sw = (key, on, disabled = false) =>
      `<label class="switch"><input type="checkbox" data-setting="${key}" ${on ? "checked" : ""} ${disabled ? "disabled" : ""}><span></span></label>`;
    const eqs = st.equivalences
      .map(
        (e) =>
          `<div class="setting"><span class="txt"><span class="t">${esc(e.name)}</span><span class="s">1 ud ≈ ${fmt(e.grams, 1)} ${e.volume ? "ml" : "g"}</span></span><button class="icon-btn" data-action="del-eq" data-name="${esc(e.name)}" aria-label="Quitar equivalencia">${svg(P.close, 18)}</button></div>`
      )
      .join("");
    d.innerHTML = `
      <div class="sheet-head"><div class="titles"><h2>Ajustes</h2><span>Menú Semanal ${MS_VERSION}</span></div>
        <button class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
      <div class="sheet-body settings">
        <div class="setting"><span class="txt"><span class="t">Comensales</span><span class="s">Las cantidades de las recetas se ajustan a este número al comprobar la despensa.</span></span>
          <div class="mini"><button class="icon-btn" data-action="people-dec" aria-label="Menos comensales" ${s.people <= 1 ? "disabled" : ""}>${svg(P.minus, 18)}</button><output>${s.people}</output><button class="icon-btn" data-action="people-inc" aria-label="Más comensales" ${s.people >= 12 ? "disabled" : ""}>${svg(P.plus, 18)}</button></div></div>
        <div class="setting"><span class="txt"><span class="t">Calorías diarias de referencia</span><span class="s">Por persona; un adulto medio ronda las 2000 kcal. La comida busca el 35 % (≈ ${fmt(s.kcal_day * 0.35)} kcal) y la cena el 30 % (≈ ${fmt(s.kcal_day * 0.3)} kcal).</span></span>
          <input class="input" type="number" min="1000" max="4500" step="50" inputmode="numeric" data-setting="kcal_day" value="${s.kcal_day}" aria-label="kcal al día"></div>
        <div class="setting"><span class="txt"><span class="t">Batch cooking</span><span class="s">Al generar, junta en la semana platos que comparten elaboración (carne picada, pollo, legumbre cocida…) para cocinarla una vez el fin de semana.</span></span>${sw("batch", s.batch)}</div>
        <div class="setting"><span class="txt"><span class="t">Aprovechar lo que hay en la Despensa</span><span class="s">${st.despensa.available ? "Da un poco de preferencia a las recetas cuyos ingredientes ya tienes." : "Necesita la integración Despensa."}</span></span>${sw("prefer_pantry", s.prefer_pantry, !st.despensa.available)}</div>
        <h3>Colores por componente principal</h3>
        <p>El borde de cada receta y de cada plato de la semana usa el color de su tipo.</p>
        ${st.categories
          .map(
            (c) =>
              `<div class="setting"><span class="dot" style="${tone(c.color)};width:14px;height:14px"></span><span class="txt"><span class="t"><span class="emoji">${c.icon}</span> ${esc(c.name)}</span></span><input type="color" data-color="${c.id}" value="${c.color}" aria-label="Color de ${esc(c.name)}"></div>`
          )
          .join("")}
        <h3>Equivalencias</h3>
        <p>Cuánto pesa una unidad de un producto de la Despensa (un paquete, una bandeja…). Las de pasta, arroz, leche, latas y botes vienen de serie; las tuyas se añaden al comprobar la disponibilidad.</p>
        ${eqs || `<p><i>Aún no has añadido ninguna.</i></p>`}
        <h3>Recetas de ejemplo</h3>
        <p>Una treintena de recetas caseras (legumbres, pescado, carne, huevos, verdura, pasta y arroz) para probar el planificador. Las que ya tengas no se duplican; puedes cambiarlas o borrarlas.</p>
        <button class="btn outline" data-action="examples">Añadir recetas de ejemplo</button>
        <p style="margin-top:18px">Las kcal son estimaciones hechas con tablas de composición de alimentos; el equilibrio sigue las recomendaciones de la AESAN para adultos sanos.</p>
      </div>`;
    d.querySelector(".sheet-body").scrollTop = scroll;
  }

  _setting(key, value) {
    this._ws({ type: "menu_semanal/settings/set", [key]: value }).catch(() => this._renderSettings());
  }

  _settingInput(t, type) {
    if (type !== "change") return;
    if (t.dataset.setting && t.type === "checkbox") this._setting(t.dataset.setting, t.checked);
    else if (t.dataset.setting === "kcal_day") {
      const v = Math.max(1000, Math.min(4500, Math.round(Number(t.value) || 2000)));
      t.value = v;
      t.blur();
      this._setting("kcal_day", v);
    } else if (t.dataset.color) {
      t.blur();
      this._ws({ type: "menu_semanal/category/color", category: t.dataset.color, color: t.value }).catch(() => {});
    }
  }

  /* ---------- acciones dentro de las hojas */
  async _sheetAction(action, el) {
    const dr = this._draft;
    const key = this._slotWeek;
    const i = this._slotIndex;
    switch (action) {
      /* plato */
      case "pick":
        this._openPicker();
        break;
      case "pick-recipe": {
        const rid = el.dataset.id;
        const prev = this._weekData(key).slots[i];
        this.$.dialog.close();
        try {
          await this._ws({ type: "menu_semanal/slot/set", week: key, slot: i, recipe_id: rid });
          this._entered.add(i);
          this._render();
          const r = this._recipe(rid);
          this._toast(`${r ? r.name : "Receta"}: ${DAYS[i >> 1].toLowerCase()} (fijada)`, "Deshacer", () => this._restoreSlot(key, i, prev));
        } catch (err) {
          /* aviso mostrado */
        }
        break;
      }
      case "lock": {
        const s = this._weekData(key).slots[i];
        this._ws({ type: "menu_semanal/slot/lock", week: key, slot: i, locked: !s.locked }).catch(() => {});
        break;
      }
      case "free":
      case "unfree": {
        const prev = this._weekData(key).slots[i];
        this.$.dialog.close();
        this._ws({ type: "menu_semanal/slot/set", week: key, slot: i, free: action === "free" })
          .then(() => {
            if (action === "free")
              this._toast(`${DAYS[i >> 1]}: ${MEAL[MEALS[i % 2]].toLowerCase()} libre`, "Deshacer", () => this._restoreSlot(key, i, prev));
          })
          .catch(() => {});
        break;
      }
      /* comprobar */
      case "check-all": {
        const missing = this._checkResult.items.filter((x) => x.status === "missing");
        const all = missing.every((x) => this._selected.has(x.key));
        this._selected = new Set(all ? [] : missing.map((x) => x.key));
        this._renderCheck();
        break;
      }
      case "add-cesta":
        this._addToCesta();
        break;
      case "save-eq":
        this._saveEquivalence(el.dataset.name);
        break;
      /* receta */
      case "emojis": {
        const grid = this.$.dialog.querySelector(".emoji-grid");
        grid.hidden = !grid.hidden;
        break;
      }
      case "pick-emoji":
        dr.icon = el.dataset.emoji;
        this.$.dialog.querySelector(".emoji-grid").hidden = true;
        this._renderDraftParts(["icon"]);
        break;
      case "toggle-meal":
        dr.meals = dr.meals.includes(el.dataset.id)
          ? dr.meals.filter((m) => m !== el.dataset.id)
          : MEALS.filter((m) => m === el.dataset.id || dr.meals.includes(m));
        dr.error = "";
        this._renderDraftParts(["meals", "foot"]);
        break;
      case "pick-cat":
        dr.category = el.dataset.id;
        dr.categoryTouched = true;
        this._renderDraftParts(["cats", "icon"]);
        break;
      case "rate":
        dr.rating = Number(el.dataset.id);
        this._renderDraftParts(["rate"]);
        break;
      case "serv-dec":
      case "serv-inc":
        dr.servings = Math.max(1, Math.min(20, dr.servings + (action === "serv-inc" ? 1 : -1)));
        this._renderDraftParts(["serv"]);
        this._estimate();
        break;
      case "add-ing":
        dr.ingredients.push({ name: "", qty: "", unit: "g" });
        this._renderDraftParts(["ings"]);
        this.$.dialog.querySelector(`[data-ing="${dr.ingredients.length - 1}"][data-f=name]`).focus();
        break;
      case "del-ing":
        dr.ingredients.splice(Number(el.dataset.id), 1);
        if (!dr.ingredients.length) dr.ingredients.push({ name: "", qty: "", unit: "g" });
        this._renderDraftParts(["ings"]);
        this._estimate();
        break;
      case "save-recipe":
        this._saveRecipe();
        break;
      case "ask-delete":
        dr.confirmDelete = true;
        this._renderDraftParts(["foot"]);
        break;
      case "cancel-delete":
        dr.confirmDelete = false;
        this._renderDraftParts(["foot"]);
        break;
      case "delete-recipe": {
        const id = dr.id;
        const name = dr.name;
        this.$.dialog.close();
        this._ws({ type: "menu_semanal/recipe/delete", recipe_id: id })
          .then(() =>
            this._toast(`Receta borrada: ${name}`, "Deshacer", () => this._ws({ type: "menu_semanal/recipe/restore", recipe_id: id }).catch(() => {}))
          )
          .catch(() => {});
        break;
      }
      /* ajustes */
      case "people-dec":
      case "people-inc":
        this._setting("people", Math.max(1, Math.min(12, this._state.settings.people + (action === "people-inc" ? 1 : -1))));
        break;
      case "del-eq":
        this._ws({ type: "menu_semanal/equivalence/set", name: el.dataset.name, grams: null }).catch(() => {});
        break;
      default:
        break;
    }
  }
}

/* --------------------------------------------------------- panel lateral */
class MenuSemanalPanel extends MenuSemanalBase {
  get mode() {
    return "panel";
  }
  set panel(p) {
    this._panel = p;
  }
  set route(r) {
    this._route = r;
  }
}

/* --------------------------------------------------------------- tarjeta */
class MenuSemanalCard extends MenuSemanalBase {
  get mode() {
    return "card";
  }
  setConfig(config) {
    this._config = { ...(config || {}) };
    if (this._config.view === "recipes") this._view = "recipes";
    if (this.$) {
      this.shadowRoot.querySelector(".title").textContent = this._config.title || "Menú Semanal";
      this._render();
    }
  }
  getCardSize() {
    return 10;
  }
  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }
  static getStubConfig() {
    return {};
  }
}

if (!customElements.get("menu-semanal-panel")) customElements.define("menu-semanal-panel", MenuSemanalPanel);
if (!customElements.get("menu-semanal-card")) {
  customElements.define("menu-semanal-card", MenuSemanalCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "menu-semanal-card",
    name: "Menú Semanal",
    description: "Comidas y cenas de la semana con tus recetas, equilibradas y con batch cooking; comprueba la Despensa y añade lo que falta a la Cesta.",
  });
  console.info(
    `%c MENÚ SEMANAL %c ${MS_VERSION} `,
    "background:#43a047;color:#fff;border-radius:4px 0 0 4px;padding:2px 4px",
    "background:#555;color:#fff;border-radius:0 4px 4px 0;padding:2px 4px"
  );
}
