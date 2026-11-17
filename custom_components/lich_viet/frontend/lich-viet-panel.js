/* Lịch Việt - trang lịch âm trên sidebar Home Assistant. Không cần build, không phụ thuộc thư viện. */

const WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const TYPE_LABELS = { sinh_nhat: "Sinh nhật", gio: "Giỗ", ky_niem: "Kỷ niệm", khac: "Khác" };
const TYPE_PLACEHOLDERS = { sinh_nhat: "Sinh nhật con", gio: "Giỗ ông nội", ky_niem: "Kỷ niệm ngày cưới", khac: "Họp lớp" };
// Giỗ thường tính theo âm lịch, các loại khác theo dương lịch.
const TYPE_CALENDAR = { sinh_nhat: "solar", gio: "lunar", ky_niem: "solar", khac: "solar" };
const CATEGORY_LABELS = {
  national: "Lễ quốc gia",
  lunar: "Lễ truyền thống",
  monthly: "Mùng 1, rằm",
  social: "Ngày kỷ niệm",
  international: "Lễ quốc tế",
  family: "Gia đình",
};
const ERRORS = {
  name_required: "Nhập tên sự kiện",
  date_invalid: "Ngày hoặc tháng không hợp lệ",
  year_invalid: "Năm phải trong khoảng 1800–2199",
  year_required: "Sự kiện chỉ một lần cần nhập năm",
  remind_invalid: "Số ngày nhắc trước từ 0 đến 60",
  type_invalid: "Loại sự kiện không hợp lệ",
  calendar_invalid: "Loại lịch không hợp lệ",
  not_found: "Không tìm thấy sự kiện (có thể đã bị xóa)",
};

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const pad = (n) => String(n).padStart(2, "0");
const isoDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const fmtDate = (iso) => {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
};
const fmtDayMonth = (iso) => {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
};

const STYLE = `
:host { display:block; height:100%; position:relative; color:var(--primary-text-color); font-family:var(--paper-font-body1_-_font-family, inherit); }
* { box-sizing:border-box; }
.bg { position:fixed; inset:0; background-size:cover; background-position:center; z-index:0; transition:opacity .6s; }
.page { position:relative; z-index:1; min-height:100%; padding:12px 16px 24px; max-width:1100px; margin:0 auto; }
.glass { background:color-mix(in srgb, var(--card-background-color, #fff) var(--lv-opacity, 100%), transparent);
  border:1px solid var(--divider-color, rgba(0,0,0,.12)); border-radius:var(--ha-card-border-radius, 12px); }
.with-bg .glass { -webkit-backdrop-filter:blur(14px) saturate(1.2); backdrop-filter:blur(14px) saturate(1.2); border-color:rgba(255,255,255,.35); }
.toolbar { display:flex; align-items:center; gap:8px; padding:6px 10px; margin-bottom:12px; flex-wrap:wrap; }
.toolbar .title { font-size:20px; font-weight:500; margin-right:auto; }
.toolbar .month { font-weight:500; min-width:120px; text-align:center; }
button { font:inherit; color:inherit; background:transparent; border:1px solid var(--divider-color, rgba(0,0,0,.2)); border-radius:8px; padding:6px 12px; cursor:pointer; display:inline-flex; align-items:center; gap:6px; }
button:hover { background:color-mix(in srgb, var(--primary-color) 10%, transparent); }
button.icon { padding:6px; border:none; border-radius:50%; }
button.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
button.danger { color:var(--error-color, #db4437); border-color:var(--error-color, #db4437); }
ha-icon { --mdc-icon-size:20px; }
.hero { display:flex; gap:18px; align-items:center; padding:16px; margin-bottom:12px; flex-wrap:wrap; }
.hero .big { text-align:center; min-width:80px; }
.hero .big .num { font-size:52px; font-weight:500; line-height:1.05; }
.hero .big .sub, .muted { color:var(--secondary-text-color); font-size:13px; }
.hero .info { flex:1; min-width:220px; }
.hero .lunar { font-size:18px; font-weight:500; margin-bottom:2px; }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.chip { display:inline-flex; align-items:center; gap:5px; font-size:12px; padding:3px 10px; border-radius:999px; background:color-mix(in srgb, var(--primary-text-color) 7%, transparent); color:var(--secondary-text-color); }
.chip ha-icon { --mdc-icon-size:15px; }
.day-events { margin-top:10px; display:flex; flex-direction:column; gap:6px; }
.day-event { display:flex; align-items:center; gap:8px; font-size:14px; }
.tet { border-radius:12px; padding:10px 16px; text-align:center; background:rgba(239,159,39,.18); color:var(--primary-text-color); }
.tet .num { font-size:28px; font-weight:500; line-height:1.2; }
.grid-wrap { padding:10px; margin-bottom:12px; }
.grid { display:grid; grid-template-columns:repeat(7, minmax(0,1fr)); gap:5px; }
.dow { text-align:center; font-size:12px; color:var(--secondary-text-color); padding:4px 0; }
.dow.sun { color:var(--error-color, #db4437); }
.cell { position:relative; min-height:86px; border-radius:10px; padding:5px 6px 20px; cursor:pointer; border:1px solid transparent;
  background:color-mix(in srgb, var(--card-background-color, #fff) 55%, transparent); text-align:left; width:100%;
  display:flex; flex-direction:column; align-items:stretch; justify-content:flex-start; gap:2px; overflow:hidden; }
.cell:hover { border-color:var(--primary-color); }
.cell .top { display:flex; align-items:center; justify-content:space-between; gap:4px; min-height:24px; }
.cell .s { font-size:17px; font-weight:500; line-height:1.2; }
.cell .l { position:absolute; right:7px; bottom:4px; font-size:12px; color:var(--secondary-text-color); white-space:nowrap; }
.cell .top .badge { width:24px; height:24px; }
.cell.out { opacity:.42; }
.cell.sun .s, .cell.off .s { color:var(--error-color, #db4437); }
.cell.moon-1 { background:rgba(239,159,39,.12); }
.cell.moon-15 { background:rgba(239,159,39,.26); }
.cell.moon-1 .l, .cell.moon-15 .l { color:#b06e0a; font-weight:500; }
.cell.today { border:2px solid var(--primary-color); }
.cell.selected { box-shadow:inset 0 0 0 2px color-mix(in srgb, var(--primary-color) 45%, transparent); background:color-mix(in srgb, var(--primary-color) 14%, transparent); }
.cell .ev { display:flex; align-items:center; gap:4px; font-size:11px; line-height:1.3; min-width:0; }
.cell .ev .t { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }
.cell .ev.off .t { color:var(--error-color, #db4437); font-weight:500; }
.cell .ev .dot { width:6px; height:6px; border-radius:50%; flex:none; }
.cell .more { font-size:10.5px; color:var(--secondary-text-color); line-height:1.2; }
.tag { display:inline-block; font-size:11px; font-weight:500; line-height:1.5; padding:0 7px; border-radius:999px; white-space:nowrap; flex:none;
  background:rgba(29,158,117,.18); color:#12866a; vertical-align:middle; }
.cell .ev .tag { font-size:10px; padding:0 5px; line-height:1.4; }
.day-event .tag { margin-left:-2px; }
.dot-national { background:#e24b4a; } .dot-lunar, .dot-monthly { background:#ef9f27; } .dot-social { background:#7f77dd; }
.dot-international { background:#639922; } .dot-family { background:#1d9e75; }
.swatch { width:24px; height:24px; border-radius:6px; flex:none; display:inline-flex; align-items:center; justify-content:center; color:#b06e0a; }
.swatch ha-icon { --mdc-icon-size:14px; }
.badge { width:24px; height:24px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; flex:none; }
.badge ha-icon { --mdc-icon-size:15px; }
.cat-national { background:rgba(226,75,74,.18); color:#d43c3b; }
.cat-lunar, .cat-monthly { background:rgba(239,159,39,.22); color:#b06e0a; }
.cat-social { background:rgba(127,119,221,.2); color:#6158c9; }
.cat-international { background:rgba(99,153,34,.2); color:#4f7f1b; }
.cat-family { background:rgba(29,158,117,.2); color:#12866a; }
.cols { display:grid; grid-template-columns:minmax(0,3fr) minmax(0,2fr); gap:12px; }
.card { padding:12px 14px; margin-bottom:12px; }
.card h2 { font-size:16px; font-weight:500; margin:0 0 6px; display:flex; align-items:center; gap:8px; }
.card h2 .spacer { flex:1; }
.row { display:flex; align-items:center; gap:10px; padding:8px 0; border-top:1px solid var(--divider-color, rgba(0,0,0,.08)); }
.row:first-of-type { border-top:none; }
.row .name { flex:1; min-width:0; }
.row .name .t { overflow:hidden; text-overflow:ellipsis; }
.row .left { color:var(--secondary-text-color); font-size:13px; white-space:nowrap; }
.legend { display:flex; flex-direction:column; gap:8px; font-size:14px; }
.legend span { display:flex; align-items:center; gap:8px; }
.credit { display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap; font-size:12px; }
.credit > span { padding:4px 10px; border-radius:999px; display:inline-flex; align-items:center; gap:4px; }
.credit a { color:inherit; }
.error { color:var(--error-color, #db4437); font-size:13px; margin-top:6px; }
.empty { color:var(--secondary-text-color); font-size:14px; padding:6px 0; }
.overlay { position:fixed; inset:0; background:rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index:10; padding:16px; }
.dialog { background:var(--card-background-color, #fff); color:var(--primary-text-color); border-radius:16px; padding:18px; width:100%; max-width:440px; max-height:90vh; overflow:auto; }
.dialog h3 { margin:0 0 12px; font-size:18px; font-weight:500; }
.form { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.form label { display:flex; flex-direction:column; gap:4px; font-size:13px; color:var(--secondary-text-color); }
.form label.full { grid-column:1 / -1; }
.form input, .form select, .form textarea { font:inherit; font-size:15px; color:var(--primary-text-color); background:var(--input-fill-color, rgba(0,0,0,.04));
  border:1px solid var(--divider-color, rgba(0,0,0,.2)); border-radius:8px; padding:8px; width:100%; }
.actions { display:flex; gap:8px; margin-top:14px; align-items:center; }
.actions .spacer { flex:1; }
.loading { padding:40px; text-align:center; color:var(--secondary-text-color); }
@media (max-width: 700px) {
  .page { padding:8px 8px 20px; }
  .cols { grid-template-columns:1fr; }
  .grid { gap:3px; }
  .cell { min-height:64px; padding:3px 3px 15px; border-radius:8px; }
  .cell .top { min-height:18px; gap:2px; }
  .cell .s { font-size:15px; }
  .cell .top .badge { width:17px; height:17px; }
  .cell .top .badge ha-icon { --mdc-icon-size:11px; }
  .cell .l { font-size:10px; right:4px; bottom:2px; }
  .cell .ev { font-size:9.5px; gap:2px; line-height:1.2; align-items:flex-start; }
  .cell .ev .dot { width:4px; height:4px; margin-top:4px; }
  .cell .ev .t { white-space:normal; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .cell .more { font-size:9.5px; }
  .cell .ev .tag { display:none; }
  .hero .big .num { font-size:44px; }
  .toolbar .title { font-size:18px; }
  .toolbar .label { display:none; }
}
`;

class LichVietPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = {
      loading: true,
      error: "",
      overview: null,
      year: null,
      month: null,
      days: [],
      selected: null,
      selectedInfo: null,
      events: [],
      background: null,
      dialog: null,
      dialogError: "",
      confirmDelete: false,
    };
    this._started = false;
    this._onClick = this._onClick.bind(this);
    this._onChange = this._onChange.bind(this);
    this.shadowRoot.addEventListener("click", this._onClick);
    this.shadowRoot.addEventListener("change", this._onChange);
  }

  set hass(hass) {
    this._hass = hass;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = hass;
    if (!this._started) {
      this._started = true;
      this._load();
    }
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    this._narrow = value;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.narrow = value;
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    this._timer = setInterval(() => this._checkDateChange(), 60 * 1000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  _ws(msg) {
    return this._hass.connection.sendMessagePromise(msg);
  }

  get _isAdmin() {
    const ov = this._state.overview;
    return Boolean(ov ? ov.config.is_admin : this._hass && this._hass.user && this._hass.user.is_admin);
  }

  async _load() {
    try {
      const overview = await this._ws({ type: "lich_viet/overview" });
      const today = overview.today;
      Object.assign(this._state, {
        overview,
        year: today.year,
        month: today.month,
        selected: today.date,
        selectedInfo: today,
        todayIso: today.date,
      });
      const [month, events] = await Promise.all([
        this._ws({ type: "lich_viet/month", year: today.year, month: today.month }),
        this._ws({ type: "lich_viet/events/list" }),
      ]);
      this._state.days = month.days;
      this._state.events = events;
      this._state.loading = false;
      this._state.error = "";
      this._render();
      if (overview.config.background) this._loadBackground(false);
    } catch (err) {
      this._state.loading = false;
      this._state.error = `Không tải được Lịch Việt: ${err && err.message ? err.message : err}`;
      this._render();
    }
  }

  async _loadBackground(change) {
    try {
      this._state.background = await this._ws({ type: "lich_viet/background", change: Boolean(change) });
    } catch (err) {
      this._state.background = null;
    }
    this._render();
  }

  async _reloadAll() {
    const [overview, month, events] = await Promise.all([
      this._ws({ type: "lich_viet/overview" }),
      this._ws({ type: "lich_viet/month", year: this._state.year, month: this._state.month }),
      this._ws({ type: "lich_viet/events/list" }),
    ]);
    this._state.overview = overview;
    this._state.days = month.days;
    this._state.events = events;
    if (this._state.selected) {
      this._state.selectedInfo = await this._ws({ type: "lich_viet/day", date: this._state.selected });
    }
    this._render();
  }

  async _checkDateChange() {
    if (!this._state.overview) return;
    if (isoDate(new Date()) !== this._state.todayIso) {
      this._state.todayIso = isoDate(new Date());
      await this._load();
    }
  }

  async _goMonth(delta) {
    let { year, month } = this._state;
    month += delta;
    if (month < 1) {
      month = 12;
      year -= 1;
    } else if (month > 12) {
      month = 1;
      year += 1;
    }
    await this._showMonth(year, month);
  }

  async _showMonth(year, month) {
    const res = await this._ws({ type: "lich_viet/month", year, month });
    Object.assign(this._state, { year, month, days: res.days });
    this._render();
  }

  async _goToday() {
    const today = this._state.overview.today;
    this._state.selected = today.date;
    this._state.selectedInfo = today;
    await this._showMonth(today.year, today.month);
  }

  async _select(iso) {
    this._state.selected = iso;
    this._render();
    this._state.selectedInfo = await this._ws({ type: "lich_viet/day", date: iso });
    this._render();
  }

  // ------------------------------------------------------------ sự kiện
  _openDialog(event) {
    const base = { name: "", type: "sinh_nhat", calendar: "solar", day: "", month: "", year: "", repeat: true, remind_days: 3, note: "" };
    this._state.dialog = event ? { ...base, ...event, year: event.year || "", repeat: event.repeat !== false } : base;
    // Sự kiện mới: đổi loại thì tự đổi lịch (giỗ -> âm lịch) cho tới khi người dùng tự chọn lịch.
    this._calendarTouched = Boolean(event);
    this._state.dialogError = "";
    this._state.confirmDelete = false;
    this._render();
    const first = this.shadowRoot.querySelector("#f-name");
    if (first && first.focus) first.focus();
  }

  _closeDialog() {
    this._state.dialog = null;
    this._render();
  }

  _readForm() {
    const val = (id) => {
      const el = this.shadowRoot.querySelector(`#f-${id}`);
      return el ? el.value : "";
    };
    return {
      id: this._state.dialog.id || "",
      name: val("name").trim(),
      type: val("type"),
      calendar: val("calendar"),
      day: val("day"),
      month: val("month"),
      year: val("year"),
      repeat: val("repeat") !== "once",
      remind_days: val("remind") === "" ? 0 : val("remind"),
      note: val("note").trim(),
    };
  }

  _validate(ev) {
    if (!ev.name) return ERRORS.name_required;
    const day = Number(ev.day);
    const month = Number(ev.month);
    if (!Number.isInteger(day) || !Number.isInteger(month) || month < 1 || month > 12 || day < 1) return ERRORS.date_invalid;
    const maxDay = ev.calendar === "lunar" ? 30 : [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
    if (day > maxDay) return ERRORS.date_invalid;
    if (ev.year !== "" && (!Number.isInteger(Number(ev.year)) || Number(ev.year) < 1800 || Number(ev.year) > 2199))
      return ERRORS.year_invalid;
    if (!ev.repeat && ev.year === "") return ERRORS.year_required;
    const remind = Number(ev.remind_days);
    if (!Number.isInteger(remind) || remind < 0 || remind > 60) return ERRORS.remind_invalid;
    return "";
  }

  async _saveDialog() {
    const ev = this._readForm();
    this._state.dialog = { ...this._state.dialog, ...ev };
    const problem = this._validate(ev);
    if (problem) {
      this._state.dialogError = problem;
      this._render();
      return;
    }
    try {
      await this._ws({
        type: "lich_viet/events/save",
        event: {
          ...ev,
          day: Number(ev.day),
          month: Number(ev.month),
          year: ev.year === "" ? null : Number(ev.year),
          remind_days: Number(ev.remind_days),
        },
      });
    } catch (err) {
      this._state.dialogError = ERRORS[err && err.message] || `Không lưu được: ${err && err.message ? err.message : err}`;
      this._render();
      return;
    }
    this._state.dialog = null;
    await this._reloadAll();
  }

  async _deleteDialog() {
    if (!this._state.confirmDelete) {
      this._state.confirmDelete = true;
      this._render();
      return;
    }
    try {
      await this._ws({ type: "lich_viet/events/delete", event_id: this._state.dialog.id });
    } catch (err) {
      this._state.dialogError = ERRORS[err && err.message] || ERRORS.not_found;
      this._render();
      return;
    }
    this._state.dialog = null;
    await this._reloadAll();
  }

  // ------------------------------------------------------------ xử lý bấm
  _onClick(ev) {
    const target = ev.target.closest ? ev.target.closest("[data-action]") : null;
    if (!target) {
      if (ev.target.classList && ev.target.classList.contains("overlay")) this._closeDialog();
      return;
    }
    const action = target.dataset.action;
    const actions = {
      prev: () => this._goMonth(-1),
      next: () => this._goMonth(1),
      today: () => this._goToday(),
      select: () => this._select(target.dataset.date),
      "change-bg": () => this._loadBackground(true),
      add: () => this._openDialog(null),
      edit: () => this._openDialog(this._state.events.find((e) => e.id === target.dataset.id)),
      cancel: () => this._closeDialog(),
      save: () => this._saveDialog(),
      delete: () => this._deleteDialog(),
    };
    if (actions[action]) actions[action]();
  }

  _onChange(ev) {
    const id = ev.target && ev.target.id;
    if (!this._state.dialog || !id) return;
    if (id === "f-calendar") {
      this._calendarTouched = true;
      this._state.dialog = { ...this._state.dialog, ...this._readForm() };
    } else if (id === "f-type") {
      const type = ev.target.value;
      const name = this.shadowRoot.querySelector("#f-name");
      if (name) name.placeholder = TYPE_PLACEHOLDERS[type] || "";
      const cal = this.shadowRoot.querySelector("#f-calendar");
      if (cal && !this._calendarTouched) cal.value = TYPE_CALENDAR[type] || "solar";
    } else if (id === "f-repeat") {
      const label = this.shadowRoot.querySelector("#f-year-label");
      if (label) label.firstChild.textContent = ev.target.value === "once" ? "Năm (bắt buộc)" : "Năm (không bắt buộc)";
    }
  }

  // ------------------------------------------------------------ giao diện
  _badge(e, extra = "") {
    return `<span class="badge cat-${esc(e.category)} ${extra}" title="${esc(e.name)}"><ha-icon icon="${esc(e.icon)}"></ha-icon></span>`;
  }

  _yearsLabel(e) {
    if (!e.years) return "";
    return e.event_type === "sinh_nhat" ? `${e.years} tuổi` : `${e.years} năm`;
  }

  _yearsTag(e) {
    const label = this._yearsLabel(e);
    return label ? `<span class="tag">${esc(label)}</span>` : "";
  }

  _renderHero() {
    const info = this._state.selectedInfo;
    const ov = this._state.overview;
    if (!info) return "";
    const tet = ov.tet;
    const isToday = info.date === ov.today.date;
    const events = info.events
      .map(
        (e) =>
          `<div class="day-event">${this._badge(e)}<span>${esc(e.name)}</span>${this._yearsTag(e)}<span>${
            e.off ? ' <span class="muted">· nghỉ lễ</span>' : ""
          }</span></div>`
      )
      .join("");
    const hours = info.gio_hoang_dao.map((h) => esc(h.chi)).join(", ");
    return `
      <div class="glass hero">
        <div class="big">
          <div class="sub">${esc(info.weekday_name)}</div>
          <div class="num">${info.day}</div>
          <div class="sub">${pad(info.month)}/${info.year}</div>
        </div>
        <div class="info">
          <div class="lunar">${esc(info.lunar_text)}</div>
          <div class="muted">Ngày ${esc(info.can_chi_day)} · tháng ${esc(info.can_chi_month)} · năm ${esc(info.can_chi_year)} (${esc(info.con_giap)})</div>
          <div class="chips">
            <span class="chip"><ha-icon icon="mdi:leaf"></ha-icon>${esc(info.solar_term)}</span>
            <span class="chip"><ha-icon icon="mdi:clock-outline"></ha-icon>Hoàng đạo: ${hours}</span>
            <span class="chip"><ha-icon icon="mdi:moon-waxing-crescent"></ha-icon>Tháng ${info.lunar_month_length === 30 ? "đủ" : "thiếu"} (${info.lunar_month_length} ngày)</span>
          </div>
          ${events ? `<div class="day-events">${events}</div>` : ""}
        </div>
        ${
          isToday && tet
            ? `<div class="tet"><div class="muted">Còn tới Tết ${esc(tet.year_name)}</div><div class="num">${
                tet.days_left === 0 ? "Hôm nay!" : `${tet.days_left} ngày`
              }</div><div class="muted">${fmtDate(tet.date)}</div></div>`
            : ""
        }
      </div>`;
  }

  _renderGrid() {
    const MAX_LINES = 3;
    const cells = this._state.days
      .map((d) => {
        const cls = ["cell"];
        if (!d.in_month) cls.push("out");
        if (d.weekday === 6) cls.push("sun");
        if (d.is_off) cls.push("off");
        if (d.lunar_day === 1 || d.lunar_day === 15) cls.push(`moon-${d.lunar_day}`);
        if (d.is_today) cls.push("today");
        if (d.date === this._state.selected) cls.push("selected");
        const lunarText = d.lunar_day === 1 ? `${d.lunar_day}/${d.lunar_month}${d.lunar_leap ? "N" : ""}` : `${d.lunar_day}`;
        // Mùng 1/rằm đã thể hiện bằng màu ô và icon trăng, không lặp thành dòng chữ.
        const named = d.events.filter((e) => e.category !== "monthly");
        // Icon tròn góc trên: ngày lễ/sự kiện đầu tiên; ngày chỉ có mùng 1/rằm thì icon trăng.
        const iconEvent = named[0] || d.events[0];
        const lines = named
          .slice(0, MAX_LINES)
          .map(
            (e) => `<span class="ev${e.off ? " off" : ""}" data-cat="${esc(e.category)}">` +
              `<span class="dot dot-${esc(e.category)}"></span><span class="t">${esc(e.short || e.name)}</span>${this._yearsTag(e)}</span>`
          )
          .join("");
        const more = named.length > MAX_LINES ? `<span class="more">+${named.length - MAX_LINES} sự kiện</span>` : "";
        const title = d.events.map((e) => e.name).join("\n");
        return `<button class="${cls.join(" ")}" data-action="select" data-date="${d.date}" title="${esc(title)}">
          <span class="top"><span class="s">${d.day}</span>${iconEvent ? this._badge(iconEvent) : ""}</span>
          ${lines}${more}
          <span class="l">${lunarText}</span>
        </button>`;
      })
      .join("");
    const head = WEEKDAYS.map((w, i) => `<div class="dow${i === 6 ? " sun" : ""}">${w}</div>`).join("");
    return `<div class="glass grid-wrap"><div class="grid">${head}${cells}</div></div>`;
  }

  _renderUpcoming() {
    const items = this._state.overview.upcoming.slice(0, 8);
    const rows = items
      .map(
        (u) => `<div class="row">${this._badge(u)}
          <div class="name"><div class="t">${esc(u.name)} ${this._yearsTag(u)}</div>
          <div class="muted">${esc(u.weekday_name)} ${fmtDayMonth(u.date)}${u.lunar ? ` · ${esc(u.lunar)} âm` : ""}</div></div>
          <span class="left">${u.days_left === 1 ? "Ngày mai" : `${u.days_left} ngày`}</span></div>`
      )
      .join("");
    return `<div class="glass card"><h2><ha-icon icon="mdi:calendar-arrow-right"></ha-icon>Sắp tới</h2>${
      rows || '<div class="empty">Không có sự kiện nào trong 45 ngày tới.</div>'
    }</div>`;
  }

  _renderFamily() {
    const admin = this._isAdmin;
    const rows = this._state.events
      .map((e) => {
        const when = e.calendar === "lunar" ? `${e.day}/${e.month} âm lịch` : `${e.day}/${e.month} dương lịch`;
        const remind = e.remind_days ? ` · nhắc trước ${e.remind_days} ngày` : "";
        return `<div class="row"><span class="badge cat-family"><ha-icon icon="${esc(e.icon)}"></ha-icon></span>
          <div class="name"><div class="t">${esc(e.name)}</div>
          <div class="muted">${esc(TYPE_LABELS[e.type] || "")} · ${when}${
            e.repeat === false ? ` · một lần, năm ${e.year}` : `${e.year ? ` · từ ${e.year}` : ""} · hằng năm`
          }${remind}</div></div>
          ${admin ? `<button class="icon" data-action="edit" data-id="${esc(e.id)}" aria-label="Sửa"><ha-icon icon="mdi:pencil"></ha-icon></button>` : ""}
        </div>`;
      })
      .join("");
    return `<div class="glass card"><h2><ha-icon icon="mdi:account-heart"></ha-icon>Sự kiện gia đình<span class="spacer"></span>${
      admin ? '<button data-action="add"><ha-icon icon="mdi:plus"></ha-icon>Thêm</button>' : ""
    }</h2>${rows || `<div class="empty">Chưa có sự kiện nào.${admin ? " Bấm Thêm để ghi ngày giỗ, sinh nhật." : ""}</div>`}</div>`;
  }

  _renderLegend() {
    const items = [
      ["national", "mdi:flag"],
      ["lunar", "mdi:firework"],
      ["social", "mdi:school"],
      ["international", "mdi:pine-tree"],
      ["family", "mdi:candle"],
    ]
      .map(
        ([cat, icon]) =>
          `<span><span class="badge cat-${cat}"><ha-icon icon="${icon}"></ha-icon></span>${CATEGORY_LABELS[cat]}</span>`
      )
      .join("");
    return `<div class="glass card"><h2>Chú thích</h2><div class="legend">${items}
      <span><span class="swatch" style="background:rgba(239,159,39,.12)"><ha-icon icon="mdi:moon-new"></ha-icon></span>Ngày mùng 1</span>
      <span><span class="swatch" style="background:rgba(239,159,39,.26)"><ha-icon icon="mdi:moon-full"></ha-icon></span>Ngày rằm</span>
      <span><span class="badge" style="color:var(--error-color,#db4437);font-weight:500">17</span>Chủ nhật, ngày nghỉ lễ</span></div></div>`;
  }

  _renderCredit() {
    const bg = this._state.background;
    if (!bg) return "";
    const place = bg.title ? `<span class="glass"><ha-icon icon="mdi:map-marker"></ha-icon>${esc(bg.title)}</span>` : "<span></span>";
    const credit =
      bg.source === "unsplash"
        ? `<span class="glass">Ảnh: <a href="${esc(bg.credit_url)}" target="_blank" rel="noopener">${esc(
            bg.credit
          )}</a> / <a href="${esc(bg.unsplash_url)}" target="_blank" rel="noopener">Unsplash</a></span>`
        : "";
    return `<div class="credit">${place}${credit}</div>`;
  }

  _renderDialog() {
    const d = this._state.dialog;
    if (!d) return "";
    const opt = (value, label, current) =>
      `<option value="${esc(value)}"${String(current) === String(value) ? " selected" : ""}>${esc(label)}</option>`;
    const types = Object.entries(TYPE_LABELS).map(([v, l]) => opt(v, l, d.type)).join("");
    return `<div class="overlay"><div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-title">
      <h3 id="dlg-title">${d.id ? "Sửa sự kiện" : "Thêm sự kiện gia đình"}</h3>
      <div class="form">
        <label class="full">Tên<input id="f-name" maxlength="80" placeholder="${esc(TYPE_PLACEHOLDERS[d.type] || "")}" value="${esc(d.name)}"></label>
        <label>Loại<select id="f-type">${types}</select></label>
        <label>Theo lịch<select id="f-calendar">${opt("solar", "Dương lịch", d.calendar)}${opt("lunar", "Âm lịch", d.calendar)}</select></label>
        <label>Ngày<input id="f-day" type="number" min="1" max="31" inputmode="numeric" value="${esc(d.day)}"></label>
        <label>Tháng<input id="f-month" type="number" min="1" max="12" inputmode="numeric" value="${esc(d.month)}"></label>
        <label>Lặp lại<select id="f-repeat">${opt("yearly", "Hằng năm", d.repeat === false ? "once" : "yearly")}${opt("once", "Chỉ một lần", d.repeat === false ? "once" : "yearly")}</select></label>
        <label id="f-year-label">${d.repeat === false ? "Năm (bắt buộc)" : "Năm (không bắt buộc)"}<input id="f-year" type="number" min="1800" max="2199" placeholder="1994" value="${esc(d.year)}"></label>
        <label>Nhắc trước (ngày)<input id="f-remind" type="number" min="0" max="60" value="${esc(d.remind_days)}"></label>
        <label class="full">Ghi chú<textarea id="f-note" rows="2" maxlength="200">${esc(d.note)}</textarea></label>
      </div>
      ${this._state.dialogError ? `<div class="error" role="alert">${esc(this._state.dialogError)}</div>` : ""}
      <div class="actions">
        ${d.id ? `<button class="danger" data-action="delete">${this._state.confirmDelete ? "Bấm lần nữa để xóa" : "Xóa"}</button>` : ""}
        <span class="spacer"></span>
        <button data-action="cancel">Hủy</button>
        <button class="primary" data-action="save">Lưu</button>
      </div>
    </div></div>`;
  }

  _render() {
    const s = this._state;
    const ov = s.overview;
    const bg = s.background;
    const opacity = ov ? ov.config.opacity : 100;
    const toolbar = `<div class="glass toolbar">
        <ha-menu-button></ha-menu-button>
        <span class="title">Lịch Việt</span>
        ${
          ov
            ? `<button class="icon" data-action="prev" aria-label="Tháng trước"><ha-icon icon="mdi:chevron-left"></ha-icon></button>
        <span class="month">Tháng ${s.month}, ${s.year}</span>
        <button class="icon" data-action="next" aria-label="Tháng sau"><ha-icon icon="mdi:chevron-right"></ha-icon></button>
        <button data-action="today"><ha-icon icon="mdi:calendar-today"></ha-icon><span class="label">Hôm nay</span></button>
        ${ov.config.background ? '<button data-action="change-bg"><ha-icon icon="mdi:image-refresh"></ha-icon><span class="label">Đổi ảnh</span></button>' : ""}`
            : ""
        }
      </div>`;
    let body;
    if (s.loading) body = '<div class="glass loading">Đang tải lịch…</div>';
    else if (s.error) body = `<div class="glass card"><div class="error">${esc(s.error)}</div></div>`;
    else
      body = `${this._renderHero()}${this._renderGrid()}
        <div class="cols"><div>${this._renderUpcoming()}</div><div>${this._renderFamily()}${this._renderLegend()}</div></div>
        ${this._renderCredit()}`;
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      ${bg ? `<div class="bg" style="background-image:url('${esc(bg.url)}')"></div>` : ""}
      <div class="page${bg ? " with-bg" : ""}" style="--lv-opacity:${bg ? opacity : 100}%">${toolbar}${body}</div>
      ${this._renderDialog()}`;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) {
      menu.hass = this._hass;
      menu.narrow = this._narrow;
    }
  }
}

if (!customElements.get("lich-viet-panel")) {
  customElements.define("lich-viet-panel", LichVietPanel);
}
