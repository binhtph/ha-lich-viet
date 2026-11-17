// Kiểm thử trang sidebar Lịch Việt bằng jsdom. Chạy: node --test tests/js/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(process.env.JSDOM_PATH || import.meta.url);
const { JSDOM } = require("jsdom");
const code = readFileSync(path.join(here, "../../custom_components/lich_viet/frontend/lich-viet-panel.js"), "utf8");
const FX = JSON.parse(readFileSync(path.join(here, "fixtures.json"), "utf8"));

const clone = (o) => JSON.parse(JSON.stringify(o));
const tick = () => new Promise((r) => setTimeout(r, 0));
const settle = async () => {
  for (let i = 0; i < 6; i++) await tick();
};

function setup({ admin = true, background = { source: "local", url: "/api/lich_viet/background/chung/ha-long.jpg?authSig=x", title: "Vịnh Hạ Long", folder: "chung", file: "ha-long.jpg" }, failOverview = false, events = FX.events } = {}) {
  const dom = new JSDOM("<!doctype html><html><body></body></html>", { runScripts: "outside-only", pretendToBeVisual: true });
  const { window } = dom;
  window.eval(code);
  const calls = [];
  let currentEvents = clone(events);
  const overview = clone(FX.overview);
  overview.config.is_admin = admin;
  const handlers = {
    "lich_viet/overview": () => (failOverview ? Promise.reject(new Error("Unknown command")) : overview),
    "lich_viet/month": (m) => (m.month === 12 ? clone(FX.month_12) : clone(FX.month_11)),
    "lich_viet/day": (m) => (m.date === "2026-11-20" ? clone(FX.day_20) : clone(FX.overview.today)),
    "lich_viet/events/list": () => clone(currentEvents),
    "lich_viet/events/save": (m) => {
      if (m.event.name === "lỗi server") return Promise.reject({ code: "invalid_event", message: "date_invalid" });
      const saved = { ...m.event, id: m.event.id || "new1", icon: "mdi:cake-variant" };
      currentEvents = currentEvents.filter((e) => e.id !== saved.id).concat(saved);
      return saved;
    },
    "lich_viet/events/delete": (m) => {
      currentEvents = currentEvents.filter((e) => e.id !== m.event_id);
      return { deleted: m.event_id };
    },
    "lich_viet/background": () => clone(background),
  };
  const hass = {
    user: { is_admin: admin },
    themes: { darkMode: false },
    connection: {
      sendMessagePromise: (msg) => {
        calls.push(clone(msg)); // đối tượng từ jsdom khác realm, chuẩn hóa để so sánh
        const h = handlers[msg.type];
        return h ? Promise.resolve(h(msg)) : Promise.reject(new Error(`no handler ${msg.type}`));
      },
    },
  };
  const el = window.document.createElement("lich-viet-panel");
  window.document.body.appendChild(el);
  el.narrow = false;
  el.hass = hass;
  const root = el.shadowRoot;
  const $ = (sel) => root.querySelector(sel);
  const $$ = (sel) => [...root.querySelectorAll(sel)];
  const click = async (node) => {
    node.dispatchEvent(new window.MouseEvent("click", { bubbles: true, composed: true }));
    await settle();
  };
  const setVal = (id, value) => {
    $(`#f-${id}`).value = value;
  };
  return { window, el, root, $, $$, calls, click, setVal, cleanup: () => { el.remove(); window.close(); } };
}

test("hiển thị thẻ hôm nay, đếm ngược Tết và lưới tháng", async () => {
  const t = setup();
  await settle();
  assert.match(t.$(".hero .lunar").textContent, /Mùng 9 tháng 10 năm Bính Ngọ/);
  assert.equal(t.$(".hero .num").textContent, "17");
  assert.match(t.$(".tet").textContent, /81 ngày/);
  assert.match(t.$(".tet").textContent, /Đinh Mùi/);
  assert.match(t.$(".toolbar .month").textContent, /Tháng 11, 2026/);
  const cells = t.$$(".cell");
  assert.equal(cells.length, 42);
  const today = t.$$(".cell.today");
  assert.equal(today.length, 1);
  assert.equal(today[0].dataset.date, "2026-11-17");
  assert.equal(today[0].querySelector(".l").textContent, "9");
  const nov9 = t.$('[data-date="2026-11-09"]');
  assert.equal(nov9.querySelector(".l").textContent, "1/10");
  assert.equal(nov9.querySelector(".top .badge.cat-monthly ha-icon").getAttribute("icon"), "mdi:moon-new");
  const nov20 = t.$('[data-date="2026-11-20"]');
  assert.equal(nov20.querySelector(".top .badge.cat-social ha-icon").getAttribute("icon"), "mdi:school");
  const ev = nov20.querySelectorAll(".ev");
  assert.equal(ev.length, 1);
  assert.equal(ev[0].textContent, "Nhà giáo VN");
  assert.ok(ev[0].querySelector(".dot.dot-social"));
  // Ngày Văn hóa Việt Nam 24/11: ngày nghỉ lễ, số ngày và tên tô đỏ
  const nov24 = t.$('[data-date="2026-11-24"]');
  assert.ok(nov24.classList.contains("off"));
  assert.equal(nov24.querySelector(".top .badge.cat-national ha-icon").getAttribute("icon"), "mdi:drama-masks");
  assert.equal(nov24.querySelector(".ev.off").textContent, "Văn hóa VN");
  assert.ok(!nov20.classList.contains("off"));
  assert.ok(t.$('[data-date="2026-11-22"]').classList.contains("sun"));
  assert.ok(t.$('[data-date="2026-10-26"]').classList.contains("out"));
  const upcoming = t.$$(".cols .card")[0].textContent;
  assert.match(upcoming, /Ngày Nhà giáo Việt Nam/);
  assert.match(upcoming, /3 ngày/);
  assert.match(upcoming, /Ngày Văn hóa Việt Nam/);
  t.cleanup();
});

test("ô mùng 1, rằm có màu riêng; mùng 1/rằm không lặp thành dòng chữ", async () => {
  const t = setup();
  await settle();
  const nov9 = t.$('[data-date="2026-11-09"]');
  assert.ok(nov9.classList.contains("moon-1"));
  assert.equal(nov9.querySelectorAll(".ev").length, 0, "mùng 1 chỉ tô màu, không thêm chữ");
  const nov23 = t.$('[data-date="2026-11-23"]');
  assert.ok(nov23.classList.contains("moon-15"));
  assert.equal(nov23.querySelector(".l").textContent, "15");
  // rằm trùng lễ có tên: icon góc là icon của lễ đó
  assert.equal(nov23.querySelector(".top .badge ha-icon").getAttribute("icon"), "mdi:rice");
  assert.equal(nov23.querySelector(".ev .t").textContent, "Hạ nguyên", "rằm có tên lễ vẫn hiện chữ");
  const plain = t.$('[data-date="2026-11-18"]');
  assert.ok(!plain.classList.contains("moon-1") && !plain.classList.contains("moon-15"));
  assert.equal(plain.querySelectorAll(".ev").length, 0);
  assert.equal(plain.querySelector(".badge"), null, "ngày thường không có icon");
  // tháng 12: rằm tháng 11 trùng giỗ ông nội -> ô tô màu rằm + một dòng "Giỗ ông nội"
  await t.click(t.$('[data-action="next"]'));
  const dec23 = t.$('[data-date="2026-12-23"]');
  assert.ok(dec23.classList.contains("moon-15"));
  assert.deepEqual([...dec23.querySelectorAll(".ev .t")].map((n) => n.textContent), ["Giỗ ông nội"]);
  assert.ok(dec23.querySelector(".dot-family"));
  assert.equal(dec23.querySelector(".top .badge.cat-family ha-icon").getAttribute("icon"), "mdi:candle");
  const dec9 = t.$('[data-date="2026-12-09"]');
  assert.equal(dec9.querySelector(".top .badge ha-icon").getAttribute("icon"), "mdi:moon-new");
  // ngày nghỉ lễ: chữ đỏ
  t.cleanup();
});

test("nhiều sự kiện cùng ngày: mỗi sự kiện một dòng, quá 3 thì gộp '+N'", async () => {
  const t = setup();
  await settle();
  const month = JSON.parse(JSON.stringify(FX.month_11));
  const cell = month.days.find((d) => d.date === "2026-11-20");
  const mk = (id, short, category, off = false) => ({ id, name: short, short, category, icon: "mdi:star", off, date: cell.date });
  cell.events = [mk("a", "Nhà giáo VN", "social"), mk("b", "Sinh nhật <b>Bin</b>", "family"),
    mk("c", "Quốc khánh", "national", true), mk("d", "Thêm 1", "family"), mk("e", "Thêm 2", "family"),
    mk("ram", "Rằm", "monthly")];
  t.el._state.days = month.days;
  t.el._render();
  const c = t.$('[data-date="2026-11-20"]');
  const lines = [...c.querySelectorAll(".ev .t")].map((n) => n.textContent);
  assert.deepEqual(lines, ["Nhà giáo VN", "Sinh nhật <b>Bin</b>", "Quốc khánh"]);
  assert.equal(c.querySelectorAll("b").length, 0, "tên được hiển thị an toàn");
  assert.equal(c.querySelector(".more").textContent, "+2 sự kiện");
  assert.equal(c.querySelectorAll(".top .badge").length, 1, "một icon ở góc cho sự kiện đầu tiên");
  assert.ok(c.querySelector(".top .badge.cat-social"));
  assert.ok(c.querySelectorAll(".ev")[2].classList.contains("off"));
  assert.match(c.getAttribute("title"), /Nhà giáo VN\nSinh nhật/);
  t.cleanup();
});

test("chuyển tháng, về hôm nay và chọn ngày", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="next"]'));
  assert.deepEqual(t.calls.at(-1), { type: "lich_viet/month", year: 2026, month: 12 });
  assert.match(t.$(".toolbar .month").textContent, /Tháng 12, 2026/);
  await t.click(t.$('[data-action="prev"]'));
  assert.deepEqual(t.calls.at(-1), { type: "lich_viet/month", year: 2026, month: 11 });
  await t.click(t.$('[data-date="2026-11-20"]'));
  assert.deepEqual(t.calls.at(-1), { type: "lich_viet/day", date: "2026-11-20" });
  assert.equal(t.$(".hero .num").textContent, "20");
  assert.match(t.$(".hero").textContent, /Ngày Nhà giáo Việt Nam/);
  assert.equal(t.$(".tet"), null);
  assert.ok(t.$('[data-date="2026-11-20"]').classList.contains("selected"));
  await t.click(t.$('[data-action="next"]'));
  await t.click(t.$('[data-action="today"]'));
  assert.match(t.$(".toolbar .month").textContent, /Tháng 11, 2026/);
  assert.equal(t.$(".hero .num").textContent, "17");
  t.cleanup();
});

test("chuyển năm khi qua tháng 12 và tháng 1", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="next"]'));
  await t.click(t.$('[data-action="next"]'));
  assert.deepEqual(t.calls.at(-1), { type: "lich_viet/month", year: 2027, month: 1 });
  t.cleanup();
});

test("ảnh nền thư mục và nút đổi ảnh", async () => {
  const t = setup();
  await settle();
  const bg = t.$(".bg");
  assert.ok(bg, "có lớp ảnh nền");
  assert.match(bg.getAttribute("style"), /ha-long\.jpg/);
  assert.ok(t.$(".page").classList.contains("with-bg"));
  assert.match(t.$(".page").getAttribute("style"), /--lv-opacity:80%/);
  assert.match(t.$(".credit").textContent, /Vịnh Hạ Long/);
  await t.click(t.$('[data-action="change-bg"]'));
  assert.deepEqual(t.calls.at(-1), { type: "lich_viet/background", change: true });
  t.cleanup();
});

test("ảnh Unsplash ghi tên tác giả", async () => {
  const t = setup({
    background: { source: "unsplash", url: "https://images.unsplash.com/p?w=2048", title: "Ninh Bình", credit: "Nguyễn A",
      credit_url: "https://unsplash.com/@a?utm_source=x", unsplash_url: "https://unsplash.com/?utm_source=x" },
  });
  await settle();
  const links = t.$$(".credit a");
  assert.equal(links.length, 2);
  assert.equal(links[0].textContent, "Nguyễn A");
  assert.equal(links[0].getAttribute("href"), "https://unsplash.com/@a?utm_source=x");
  assert.equal(links[1].textContent, "Unsplash");
  t.cleanup();
});

test("không có ảnh nền thì không có lớp ảnh", async () => {
  const t = setup({ background: null });
  await settle();
  assert.equal(t.$(".bg"), null);
  assert.ok(!t.$(".page").classList.contains("with-bg"));
  t.cleanup();
});

test("admin thêm sự kiện: kiểm tra dữ liệu trước khi gửi", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="add"]'));
  assert.ok(t.$(".dialog"));
  const before = t.calls.length;
  await t.click(t.$('[data-action="save"]'));
  assert.equal(t.$(".error").textContent, "Nhập tên sự kiện");
  assert.equal(t.calls.length, before, "không gửi khi thiếu tên");

  t.setVal("name", "Sinh nhật Bin");
  t.setVal("type", "sinh_nhat");
  t.setVal("calendar", "solar");
  t.setVal("day", "31");
  t.setVal("month", "4");
  await t.click(t.$('[data-action="save"]'));
  assert.equal(t.$(".error").textContent, "Ngày hoặc tháng không hợp lệ");
  assert.equal(t.$("#f-name").value, "Sinh nhật Bin", "giữ lại dữ liệu đã nhập");

  t.setVal("day", "30");
  t.setVal("year", "1500");
  await t.click(t.$('[data-action="save"]'));
  assert.equal(t.$(".error").textContent, "Năm phải trong khoảng 1800–2199");

  t.setVal("year", "2020");
  t.setVal("remind", "2");
  await t.click(t.$('[data-action="save"]'));
  const save = t.calls.find((c) => c.type === "lich_viet/events/save");
  assert.deepEqual(save.event, { id: "", name: "Sinh nhật Bin", type: "sinh_nhat", calendar: "solar", day: 30, month: 4,
    year: 2020, repeat: true, remind_days: 2, note: "" });
  assert.equal(t.$(".dialog"), null, "đóng hộp thoại sau khi lưu");
  assert.match(t.$$(".cols .card")[1].textContent, /Sinh nhật Bin/);
  t.cleanup();
});

test("hộp thoại thêm mới: mặc định Sinh nhật, Dương lịch; thứ tự loại; đổi sang Giỗ thì tự chọn Âm lịch", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="add"]'));
  assert.deepEqual([...t.$$("#f-type option")].map((o) => o.textContent), ["Sinh nhật", "Giỗ", "Kỷ niệm", "Khác"]);
  assert.equal(t.$("#f-type").value, "sinh_nhat");
  assert.equal(t.$("#f-calendar").value, "solar");
  assert.equal(t.$("#f-repeat").value, "yearly");
  assert.equal(t.$("#f-name").getAttribute("placeholder"), "Sinh nhật con");
  const change = (sel, value) => {
    const el = t.$(sel);
    el.value = value;
    el.dispatchEvent(new t.window.Event("change", { bubbles: true }));
  };
  change("#f-type", "gio");
  assert.equal(t.$("#f-calendar").value, "lunar");
  assert.equal(t.$("#f-name").placeholder, "Giỗ ông nội");
  // người dùng tự chọn lịch thì không bị đổi theo loại nữa
  change("#f-calendar", "solar");
  change("#f-type", "gio");
  assert.equal(t.$("#f-calendar").value, "solar");
  change("#f-repeat", "once");
  assert.match(t.$("#f-year-label").textContent, /Năm \(bắt buộc\)/);
  t.cleanup();
});

test("sự kiện chỉ một lần: bắt buộc nhập năm, gửi repeat=false", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="add"]'));
  t.setVal("name", "Họp lớp");
  t.setVal("type", "khac");
  t.setVal("day", "5");
  t.setVal("month", "6");
  t.setVal("repeat", "once");
  const before = t.calls.length;
  await t.click(t.$('[data-action="save"]'));
  assert.equal(t.$(".error").textContent, "Sự kiện chỉ một lần cần nhập năm");
  assert.equal(t.calls.length, before);
  t.setVal("year", "2027");
  await t.click(t.$('[data-action="save"]'));
  const save = t.calls.find((c) => c.type === "lich_viet/events/save");
  assert.equal(save.event.repeat, false);
  assert.equal(save.event.year, 2027);
  assert.equal(save.event.calendar, "solar");
  t.cleanup();
});

test("tag số năm: danh sách sắp tới, ô lịch, sự kiện gia đình", async () => {
  const t = setup();
  await settle();
  const upcomingTags = [...t.$$(".cols .card")[0].querySelectorAll(".tag")].map((n) => n.textContent);
  assert.deepEqual(upcomingTags, ["16 năm"]);
  assert.match(t.$$(".cols .card")[1].textContent, /từ 2010 · hằng năm/);
  await t.click(t.$('[data-action="next"]'));
  const dec23 = t.$('[data-date="2026-12-23"]');
  assert.equal(dec23.querySelector(".ev .tag").textContent, "16 năm");
  t.cleanup();
});

test("lỗi từ server hiện trong hộp thoại", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="add"]'));
  t.setVal("name", "lỗi server");
  t.setVal("day", "1");
  t.setVal("month", "1");
  await t.click(t.$('[data-action="save"]'));
  assert.equal(t.$(".error").textContent, "Ngày hoặc tháng không hợp lệ");
  assert.ok(t.$(".dialog"));
  t.cleanup();
});

test("sửa và xóa sự kiện cần bấm xác nhận", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="edit"][data-id="e1"]'));
  assert.equal(t.$("#f-name").value, "Giỗ ông nội");
  assert.equal(t.$("#f-calendar").value, "lunar");
  assert.equal(t.$("#f-day").value, "15");
  await t.click(t.$('[data-action="delete"]'));
  assert.equal(t.calls.filter((c) => c.type === "lich_viet/events/delete").length, 0);
  assert.match(t.$('[data-action="delete"]').textContent, /Bấm lần nữa/);
  await t.click(t.$('[data-action="delete"]'));
  assert.deepEqual(t.calls.find((c) => c.type === "lich_viet/events/delete"), { type: "lich_viet/events/delete", event_id: "e1" });
  assert.equal(t.$(".dialog"), null);
  assert.match(t.$$(".cols .card")[1].textContent, /Chưa có sự kiện nào/);
  t.cleanup();
});

test("hủy hộp thoại không gửi gì", async () => {
  const t = setup();
  await settle();
  await t.click(t.$('[data-action="add"]'));
  const before = t.calls.length;
  await t.click(t.$('[data-action="cancel"]'));
  assert.equal(t.$(".dialog"), null);
  assert.equal(t.calls.length, before);
  t.cleanup();
});

test("người dùng thường chỉ xem, không có nút thêm/sửa", async () => {
  const t = setup({ admin: false });
  await settle();
  assert.equal(t.$('[data-action="add"]'), null);
  assert.equal(t.$('[data-action="edit"]'), null);
  assert.match(t.$$(".cols .card")[1].textContent, /Giỗ ông nội/);
  t.cleanup();
});

test("tên sự kiện có ký tự HTML được hiển thị an toàn", async () => {
  const evil = [{ ...FX.events[0], id: "x", name: '<img src=x onerror="alert(1)">' }];
  const t = setup({ events: evil });
  await settle();
  assert.equal(t.root.querySelectorAll("img").length, 0);
  assert.match(t.$$(".cols .card")[1].textContent, /<img src=x/);
  t.cleanup();
});

test("báo lỗi khi integration chưa được cài", async () => {
  const t = setup({ failOverview: true });
  await settle();
  assert.match(t.$(".error").textContent, /Không tải được Lịch Việt: Unknown command/);
  t.cleanup();
});
