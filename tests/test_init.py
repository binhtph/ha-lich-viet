"""Kiểm thử integration Lịch Việt trên Home Assistant."""

from __future__ import annotations

from datetime import date
from http import HTTPStatus

import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from custom_components.lich_viet.const import DOMAIN

TG = "notify.tele_bot"
UNSPLASH = "https://api.unsplash.com/photos/random"


@pytest.fixture(autouse=True)
def _auto(enable_custom_integrations, hass, tmp_path):
    hass.config.language = "vi"
    hass.config.media_dirs = {"local": str(tmp_path / "media")}
    yield


@pytest.fixture
async def tz(hass):
    await hass.config.async_set_time_zone("Asia/Ho_Chi_Minh")


async def _setup(hass: HomeAssistant):
    assert await async_setup_component(hass, "http", {})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result["result"]


async def _options(hass, entry, step, data):
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": step})
    r = await hass.config_entries.options.async_configure(r["flow_id"], data)
    assert r["type"] is FlowResultType.MENU
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "save"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()


async def _tick(hass, freezer, when):
    freezer.move_to(when)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def _token(hass, user):
    """Token tạo ở thời điểm đã đóng băng (freezer) để không bị hết hạn."""
    refresh = await hass.auth.async_create_refresh_token(user, "https://example.com/app")
    return hass.auth.async_create_access_token(refresh)


def _state(hass, eid):
    st = hass.states.get(eid)
    assert st is not None, eid
    return st


NOTIFY = {"telegram_targets": [TG], "mobile_targets": ["mobile_app_brians_iphone"],
          "report_time": "06:30:00", "only_when_events": True, "holiday_remind_days": 1,
          "monthly_remind_days": 1}


# ------------------------------------------------------------------ cài đặt
async def test_single_instance_and_panel(hass, tz, freezer, hass_client, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT

    panels = hass.data["frontend_panels"]
    assert "lich-viet" in panels
    panel = panels["lich-viet"]
    assert panel.sidebar_title == "Lịch Việt" and panel.sidebar_icon == "mdi:calendar-star"
    assert panel.require_admin is False
    client = await hass_client(await _token(hass, hass_admin_user))
    resp = await client.get("/lich_viet_static/lich-viet-panel.js")
    assert resp.status == HTTPStatus.OK
    # tạo sẵn thư mục ảnh theo dịp
    media = hass.config.media_dirs["local"]
    import os
    assert sorted(os.listdir(f"{media}/lich_viet"))[:3] == ["chung", "giai_phong", "giang_sinh"]

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert "lich-viet" not in hass.data["frontend_panels"]


async def test_sensors_today(hass, tz, freezer):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    lunar = _state(hass, "sensor.lich_viet_lunar_date")
    assert lunar.state == "Mùng 9 tháng 10"
    assert lunar.attributes["can_chi_nam"] == "Bính Ngọ"
    assert lunar.attributes["can_chi_ngay"] == "Ất Mùi"
    assert lunar.attributes["tiet_khi"] == "Lập đông"
    assert lunar.attributes["friendly_name"] == "Lịch Việt Âm lịch hôm nay"
    assert _state(hass, "sensor.lich_viet_events_today").state == "Không có"
    nxt = _state(hass, "sensor.lich_viet_next_event")
    assert nxt.state == "Ngày Nhà giáo Việt Nam" and nxt.attributes["con_lai_ngay"] == 3
    assert nxt.attributes["icon"] == "mdi:school"
    tet = _state(hass, "sensor.lich_viet_days_until_tet")
    assert float(tet.state) == 81 and tet.attributes["nam"] == "Đinh Mùi"
    assert _state(hass, "sensor.lich_viet_solar_term").state == "Lập đông"
    for key in ("public_holiday", "first_lunar_day", "full_moon_day", "has_event"):
        assert _state(hass, f"binary_sensor.lich_viet_{key}").state == "off"


async def test_midnight_rollover(hass, tz, freezer):
    freezer.move_to("2026-11-22 23:59:50+07:00")
    await _setup(hass)
    assert _state(hass, "binary_sensor.lich_viet_full_moon_day").state == "off"
    await _tick(hass, freezer, "2026-11-23 00:00:03+07:00")
    assert _state(hass, "binary_sensor.lich_viet_full_moon_day").state == "on"
    assert _state(hass, "binary_sensor.lich_viet_has_event").state == "on"
    assert _state(hass, "sensor.lich_viet_events_today").state == "Rằm tháng 10 (Tết Hạ nguyên)"
    assert _state(hass, "sensor.lich_viet_lunar_date").state == "15 tháng 10"
    # Quốc khánh: ngày nghỉ lễ
    await _tick(hass, freezer, "2027-09-02 00:00:03+07:00")
    assert _state(hass, "binary_sensor.lich_viet_public_holiday").state == "on"


async def test_calendar_entity(hass, tz, freezer):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    cal = _state(hass, "calendar.lich_viet_calendar")
    assert cal.attributes["message"] == "Ngày Nhà giáo Việt Nam"
    assert cal.attributes["all_day"] is True and cal.attributes["start_time"] == "2026-11-20 00:00:00"
    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": "calendar.lich_viet_calendar", "start_date_time": "2027-01-01 00:00:00",
         "end_date_time": "2027-02-28 00:00:00"},
        blocking=True, return_response=True,
    )
    events = resp["calendar.lich_viet_calendar"]["events"]
    summary = {e["summary"]: e["start"] for e in events}
    assert summary["Tết Nguyên Đán"] == "2027-02-06"
    assert summary["Giao thừa"] == "2027-02-05"
    assert summary["Ông Công Ông Táo"] == "2027-01-30"
    assert summary["Tết Dương lịch"] == "2027-01-01"
    assert any(s.startswith("Mùng 1 tháng") for s in summary)


# ------------------------------------------------------------------ websocket
async def test_websocket_api(hass, tz, freezer, hass_ws_client, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))

    await ws.send_json({"id": 1, "type": "lich_viet/overview"})
    res = (await ws.receive_json())["result"]
    assert res["today"]["lunar_text"] == "Mùng 9 tháng 10 năm Bính Ngọ"
    assert res["tet"]["days_left"] == 81
    assert res["upcoming"][0]["name"] == "Ngày Nhà giáo Việt Nam"
    assert res["config"]["is_admin"] is True and res["config"]["opacity"] == 80

    await ws.send_json({"id": 2, "type": "lich_viet/month", "year": 2026, "month": 11})
    res = (await ws.receive_json())["result"]
    assert len(res["days"]) == 42 and sum(d["is_today"] for d in res["days"]) == 1

    await ws.send_json({"id": 3, "type": "lich_viet/day", "date": "2026-02-17"})
    res = (await ws.receive_json())["result"]
    assert res["events"][0]["name"] == "Tết Nguyên Đán" and res["is_off"] is True

    await ws.send_json({"id": 4, "type": "lich_viet/day", "date": "abc"})
    assert (await ws.receive_json())["error"]["code"] == "invalid_date"
    await ws.send_json({"id": 5, "type": "lich_viet/month", "year": 2026, "month": 13})
    assert (await ws.receive_json())["success"] is False

    # thêm, sửa, xóa sự kiện gia đình
    ev = {"name": "Giỗ ông nội", "type": "gio", "calendar": "lunar", "day": 15, "month": 11,
          "year": 2010, "remind_days": 3}
    await ws.send_json({"id": 6, "type": "lich_viet/events/save", "event": ev})
    saved = (await ws.receive_json())["result"]
    assert saved["id"] and saved["icon"] == "mdi:candle"
    await hass.async_block_till_done()

    await ws.send_json({"id": 7, "type": "lich_viet/upcoming", "days": 40})
    names = [u["name"] for u in (await ws.receive_json())["result"]]
    assert "Giỗ ông nội" in names

    await ws.send_json({"id": 8, "type": "lich_viet/events/save", "event": {**saved, "name": "Giỗ ông"}})
    assert (await ws.receive_json())["result"]["name"] == "Giỗ ông"
    await ws.send_json({"id": 9, "type": "lich_viet/events/list"})
    assert [e["name"] for e in (await ws.receive_json())["result"]] == ["Giỗ ông"]

    await ws.send_json({"id": 10, "type": "lich_viet/events/save", "event": {"name": "", "day": 1, "month": 1}})
    err = (await ws.receive_json())["error"]
    assert err["code"] == "invalid_event" and err["message"] == "name_required"
    await ws.send_json({"id": 11, "type": "lich_viet/events/save", "event": {**saved, "id": "khong_co"}})
    assert (await ws.receive_json())["error"]["message"] == "not_found"

    await ws.send_json({"id": 12, "type": "lich_viet/events/delete", "event_id": saved["id"]})
    assert (await ws.receive_json())["success"] is True
    await ws.send_json({"id": 13, "type": "lich_viet/events/delete", "event_id": saved["id"]})
    assert (await ws.receive_json())["error"]["code"] == "not_found"


async def test_events_persist_and_update_entities(hass, tz, freezer, hass_ws_client, hass_storage, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/events/save", "event": {
        "name": "Sinh nhật Bin", "type": "sinh_nhat", "calendar": "solar", "day": 18, "month": 11, "year": 2020}})
    await ws.receive_json()
    await hass.async_block_till_done()
    nxt = _state(hass, "sensor.lich_viet_next_event")
    assert nxt.state == "Sinh nhật Bin" and nxt.attributes["icon"] == "mdi:cake-variant"
    # lưu bền qua reload
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass_storage["lich_viet.data"]["data"]["events"][0]["name"] == "Sinh nhật Bin"
    assert _state(hass, "sensor.lich_viet_next_event").state == "Sinh nhật Bin"


async def test_non_admin_can_read_but_not_edit(hass, tz, freezer, hass_ws_client, hass_read_only_user, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    ws = await hass_ws_client(hass, await _token(hass, hass_read_only_user))
    await ws.send_json({"id": 1, "type": "lich_viet/overview"})
    res = await ws.receive_json()
    assert res["success"] is True and res["result"]["config"]["is_admin"] is False
    await ws.send_json({"id": 2, "type": "lich_viet/events/save",
                        "event": {"name": "x", "day": 1, "month": 1}})
    assert (await ws.receive_json())["error"]["code"] == "unauthorized"
    await ws.send_json({"id": 3, "type": "lich_viet/events/delete", "event_id": "abc"})
    assert (await ws.receive_json())["error"]["code"] == "unauthorized"


# ------------------------------------------------------------------ ảnh nền
def _img(path, name, content=b"\xff\xd8\xff fake jpeg"):
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_bytes(content)


async def test_background_local_folders(hass, tz, freezer, hass_ws_client, hass_client_no_auth, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    base = hass.config.media_dirs["local"] + "/lich_viet"
    from pathlib import Path
    _img(Path(base) / "chung", "Vịnh Hạ Long.jpg", b"HALONG")
    _img(Path(base) / "chung", "sa-pa.webp", b"SAPA")
    _img(Path(base) / "chung", "ghi-chu.txt")
    _img(Path(base) / "tet", "hoa-dao.jpg", b"DAO")

    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/background"})
    bg1 = (await ws.receive_json())["result"]
    assert bg1["source"] == "local" and bg1["folder"] == "chung"
    assert bg1["title"] in ("Vịnh Hạ Long", "Sa pa")
    # mỗi ngày một ảnh: gọi lại vẫn ra cùng ảnh
    await ws.send_json({"id": 2, "type": "lich_viet/background"})
    assert (await ws.receive_json())["result"]["file"] == bg1["file"]
    # đổi ảnh: ra ảnh khác, các lần sau trong ngày giữ ảnh mới
    await ws.send_json({"id": 3, "type": "lich_viet/background", "change": True})
    bg2 = (await ws.receive_json())["result"]
    assert bg2["file"] != bg1["file"]
    await ws.send_json({"id": 4, "type": "lich_viet/background"})
    assert (await ws.receive_json())["result"]["file"] == bg2["file"]

    # link có chữ ký tải được không cần đăng nhập; link không ký thì bị chặn
    client = await hass_client_no_auth()
    resp = await client.get(bg2["url"])
    assert resp.status == HTTPStatus.OK
    assert await resp.read() in (b"HALONG", b"SAPA")
    resp = await client.get(bg2["url"].split("?")[0])
    assert resp.status == HTTPStatus.UNAUTHORIZED

    # dịp Tết dùng thư mục tet
    await _tick(hass, freezer, "2027-02-03 08:00:00+07:00")
    ws2 = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws2.send_json({"id": 5, "type": "lich_viet/background"})
    bg3 = (await ws2.receive_json())["result"]
    assert bg3["folder"] == "tet" and bg3["title"] == "Hoa dao"

    # tắt ảnh nền
    await _options(hass, entry, "background", {"background_enabled": False, "background_mode": "daily",
                                               "unsplash_query": "Vietnam", "unsplash_mix": False,
                                               "panel_opacity": 70})
    ws3 = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws3.send_json({"id": 6, "type": "lich_viet/background"})
    assert (await ws3.receive_json())["result"] is None
    await ws3.send_json({"id": 7, "type": "lich_viet/overview"})
    cfg = (await ws3.receive_json())["result"]["config"]
    assert cfg == {**cfg, "background": False, "opacity": 70}


async def test_background_file_view_blocks_bad_paths(hass, tz, freezer, hass_client, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    from pathlib import Path
    base = Path(hass.config.media_dirs["local"]) / "lich_viet"
    _img(base / "chung", "ok.jpg")
    (base.parent / "secret.jpg").write_bytes(b"secret")
    client = await hass_client(await _token(hass, hass_admin_user))
    assert (await client.get("/api/lich_viet/background/chung/ok.jpg")).status == HTTPStatus.OK
    for bad in ("/api/lich_viet/background/khac/ok.jpg", "/api/lich_viet/background/chung/..%2Fsecret.jpg",
                "/api/lich_viet/background/chung/ghi.txt", "/api/lich_viet/background/chung/khong-co.jpg"):
        assert (await client.get(bad)).status in (HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST), bad


async def test_background_unsplash(hass, tz, freezer, hass_ws_client, aioclient_mock, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    aioclient_mock.get(UNSPLASH, json=[{
        "id": "p1", "urls": {"regular": "https://images.unsplash.com/photo-1?ixid=x"},
        "user": {"name": "Nguyen Van A", "links": {"html": "https://unsplash.com/@a"}},
        "links": {"html": "https://unsplash.com/photos/p1", "download_location": "https://api.unsplash.com/photos/p1/download"},
        "location": {"name": "Ninh Bình, Việt Nam"},
    }])
    aioclient_mock.get("https://api.unsplash.com/photos/p1/download", json={})
    await _options(hass, entry, "background", {"background_enabled": True, "background_mode": "daily",
                                               "unsplash_key": "KEY", "unsplash_query": "Vietnam landscape",
                                               "unsplash_mix": False, "panel_opacity": 80})
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/background"})
    bg = (await ws.receive_json())["result"]
    await hass.async_block_till_done()
    assert bg["source"] == "unsplash" and bg["credit"] == "Nguyen Van A"
    assert bg["title"] == "Ninh Bình, Việt Nam"
    assert bg["url"] == "https://images.unsplash.com/photo-1?ixid=x&w=2048"
    assert "utm_source=" in bg["credit_url"] and "download_location" not in bg
    api_calls = [c for c in aioclient_mock.mock_calls if str(c[1]).startswith(UNSPLASH)]
    assert len(api_calls) == 1 and api_calls[0][3]["Authorization"] == "Client-ID KEY"
    # cùng ngày dùng lại cache, không gọi API nữa
    await ws.send_json({"id": 2, "type": "lich_viet/background", "change": True})
    await ws.receive_json()
    await hass.async_block_till_done()
    assert len([c for c in aioclient_mock.mock_calls if str(c[1]).startswith(UNSPLASH)]) == 1
    assert any("download" in str(c[1]) for c in aioclient_mock.mock_calls)


async def test_background_unsplash_error_falls_back(hass, tz, freezer, hass_ws_client, aioclient_mock, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    aioclient_mock.get(UNSPLASH, status=403)
    await _options(hass, entry, "background", {"background_enabled": True, "background_mode": "random",
                                               "unsplash_key": "BAD", "unsplash_query": "Vietnam",
                                               "unsplash_mix": True, "panel_opacity": 80})
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/background"})
    assert (await ws.receive_json())["result"] is None


BAD_DOWNLOAD = [
    "https://evil.example.com/photos/p1/download",
    "http://api.unsplash.com/photos/p1/download",
    "https://api.unsplash.com.evil.example/photos/p1/download",
    "https://user:pass@api.unsplash.com/photos/p1/download",
    "https://api.unsplash.com:8443/photos/p1/download",
]


@pytest.mark.parametrize("bad", BAD_DOWNLOAD)
async def test_background_unsplash_key_only_sent_to_api(
    hass, tz, freezer, hass_ws_client, aioclient_mock, hass_admin_user, caplog, bad
):
    """Access key chỉ gửi tới https://api.unsplash.com, kể cả khi download_location bị đổi."""
    freezer.move_to("2026-11-17 08:00:00+07:00")
    entry = await _setup(hass)
    aioclient_mock.get(UNSPLASH, json=[{
        "id": "p1", "urls": {"regular": "https://images.unsplash.com/photo-1?ixid=x"},
        "user": {"name": "A"}, "links": {"download_location": bad},
    }])
    aioclient_mock.get(bad, json={})
    await _options(hass, entry, "background", {"background_enabled": True, "background_mode": "daily",
                                               "unsplash_key": "KEY", "unsplash_query": "Vietnam",
                                               "unsplash_mix": False, "panel_opacity": 80})
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/background"})
    assert (await ws.receive_json())["result"]["source"] == "unsplash"
    await hass.async_block_till_done()
    urls = [str(c[1]) for c in aioclient_mock.mock_calls]
    assert urls and all(u.startswith(UNSPLASH) for u in urls), urls
    assert "Bỏ qua download_location" in caplog.text


def test_is_unsplash_api():
    from custom_components.lich_viet.background import _is_unsplash_api

    assert _is_unsplash_api("https://api.unsplash.com/photos/p1/download?ixid=x")
    assert _is_unsplash_api("https://API.Unsplash.com:443/photos/p1/download")
    for bad in BAD_DOWNLOAD + ["", None, 123, "api.unsplash.com/photos/p1", "https://api.unsplash.com:abc/x"]:
        assert not _is_unsplash_api(bad), bad


# ------------------------------------------------------------------ thông báo
async def test_morning_report_and_reminders(hass, tz, freezer, hass_ws_client, hass_admin_user):
    tg = async_mock_service(hass, "telegram_bot", "send_message")
    app = async_mock_service(hass, "notify", "mobile_app_brians_iphone")
    freezer.move_to("2026-11-17 06:00:00+07:00")
    entry = await _setup(hass)
    await _options(hass, entry, "notify", NOTIFY)
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/events/save", "event": {
        "name": "Giỗ ông nội", "type": "gio", "calendar": "lunar", "day": 15, "month": 11, "year": 2010,
        "remind_days": 3}})
    await ws.receive_json()

    # 17/11: không có sự kiện, nhưng 19/11 nhắc trước 1 ngày Nhà giáo (20/11) -> 17/11 chưa có gì
    await _tick(hass, freezer, "2026-11-17 06:30:00+07:00")
    assert tg == [] and app == []

    # 19/11: nhắc ngày mai là Ngày Nhà giáo
    await _tick(hass, freezer, "2026-11-19 06:30:00+07:00")
    assert len(tg) == 1 and len(app) == 1
    assert "Ngày Nhà giáo Việt Nam: ngày mai (Thứ Sáu 20/11)" in tg[0].data["message"]
    assert tg[0].data["title"].startswith("<b>📅 LỊCH VIỆT › THỨ NĂM 19/11/2026")
    assert app[0].data["message"].startswith("Âm lịch: 11 tháng 10 năm Bính Ngọ")
    # nhấn vào tin trên app thì mở trang Lịch Việt (iOS: url, Android: clickAction)
    assert app[0].data["data"] == {"url": "/lich-viet", "clickAction": "/lich-viet"}
    assert "data" not in tg[0].data

    # 23/11 rằm: có sự kiện hôm nay
    await _tick(hass, freezer, "2026-11-23 06:30:00+07:00")
    assert "Hôm nay:\n• Rằm tháng 10 (Tết Hạ nguyên)" in tg[-1].data["message"]

    # 20/12: nhắc trước 3 ngày giỗ ông nội (15/11 âm = 23/12), năm thứ 16
    await _tick(hass, freezer, "2026-12-20 06:30:00+07:00")
    assert "Giỗ ông nội (16 năm): còn 3 ngày (Thứ Tư 23/12, 15/11 âm)" in tg[-1].data["message"]


async def test_scheduled_report_reminds_first_lunar_day(hass, tz, freezer):
    tg = async_mock_service(hass, "telegram_bot", "send_message")
    freezer.move_to("2026-12-08 06:00:00+07:00")
    entry = await _setup(hass)
    await _options(hass, entry, "notify", {**NOTIFY, "mobile_targets": []})
    assert entry.options["monthly_remind_days"] == 1
    await _tick(hass, freezer, "2026-12-08 06:30:00+07:00")
    assert len(tg) == 1
    assert "Mùng 1 tháng 11: ngày mai (Thứ Tư 09/12)" in tg[0].data["message"]


async def test_monthly_remind_defaults_for_existing_entry(hass, tz, freezer):
    """Entry cài từ bản trước (chưa có tùy chọn mới) vẫn nhắc trước 1 ngày."""
    tg = async_mock_service(hass, "telegram_bot", "send_message")
    freezer.move_to("2026-12-08 06:00:00+07:00")
    entry = await _setup(hass)
    opts = {k: v for k, v in entry.options.items() if k != "monthly_remind_days"}
    hass.config_entries.async_update_entry(entry, options={**opts, "telegram_targets": [TG]})
    await hass.async_block_till_done()
    await _tick(hass, freezer, "2026-12-08 06:30:00+07:00")
    assert "Mùng 1 tháng 11: ngày mai" in tg[-1].data["message"]


async def test_report_switches_and_button(hass, tz, freezer):
    tg = async_mock_service(hass, "telegram_bot", "send_message")
    app = async_mock_service(hass, "notify", "mobile_app_brians_iphone")
    freezer.move_to("2026-11-19 06:00:00+07:00")
    entry = await _setup(hass)
    await _options(hass, entry, "notify", NOTIFY)
    switches = sorted(s.entity_id for s in hass.states.async_all("switch"))
    assert switches == ["switch.lich_viet_app_brians_iphone", "switch.lich_viet_morning_report",
                        "switch.lich_viet_telegram_tele_bot"]
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.lich_viet_app_brians_iphone"},
                                   blocking=True)
    await _tick(hass, freezer, "2026-11-19 06:30:00+07:00")
    assert len(tg) == 1 and app == []

    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.lich_viet_morning_report"},
                                   blocking=True)
    await _tick(hass, freezer, "2026-11-20 06:30:00+07:00")
    assert len(tg) == 1

    # nút gửi thử luôn gửi, kể cả ngày không có sự kiện
    await hass.services.async_call("button", "press", {"entity_id": "button.lich_viet_send_report_now"},
                                   blocking=True)
    assert len(tg) == 2


async def test_only_when_events_off_sends_every_day(hass, tz, freezer):
    tg = async_mock_service(hass, "telegram_bot", "send_message")
    freezer.move_to("2026-11-17 06:00:00+07:00")
    entry = await _setup(hass)
    await _options(hass, entry, "notify", {**NOTIFY, "mobile_targets": [], "only_when_events": False,
                                           "holiday_remind_days": 0, "monthly_remind_days": 0})
    await _tick(hass, freezer, "2026-11-17 06:30:00+07:00")
    assert len(tg) == 1 and "Hôm nay" not in tg[0].data["message"]
    assert date(2026, 11, 17).isoformat() == "2026-11-17"


async def test_websocket_one_time_and_year_bounds(hass, tz, freezer, hass_ws_client, hass_admin_user):
    freezer.move_to("2026-11-17 08:00:00+07:00")
    await _setup(hass)
    ws = await hass_ws_client(hass, await _token(hass, hass_admin_user))
    await ws.send_json({"id": 1, "type": "lich_viet/events/save",
                        "event": {"name": "Họp lớp", "type": "khac", "day": 5, "month": 6, "repeat": False}})
    assert (await ws.receive_json())["error"]["message"] == "year_required"
    await ws.send_json({"id": 2, "type": "lich_viet/events/save", "event": {
        "name": "Sinh nhật con", "type": "sinh_nhat", "day": 21, "month": 12, "year": 1994}})
    saved = (await ws.receive_json())["result"]
    assert saved["calendar"] == "solar" and saved["repeat"] is True
    await ws.send_json({"id": 3, "type": "lich_viet/upcoming", "days": 40})
    sn = next(u for u in (await ws.receive_json())["result"] if u["name"] == "Sinh nhật con")
    assert sn["years"] == 32 and sn["event_type"] == "sinh_nhat"
    # tháng 12/1993 (trước năm sinh) không có sự kiện
    await ws.send_json({"id": 4, "type": "lich_viet/month", "year": 1993, "month": 12})
    days = (await ws.receive_json())["result"]["days"]
    assert not any(e["name"] == "Sinh nhật con" for d in days for e in d["events"])
