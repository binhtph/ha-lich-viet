"""API websocket cho trang Lịch Việt."""

from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import CONF_BG_ENABLED, CONF_PANEL_OPACITY, DEFAULT_PANEL_OPACITY, DOMAIN
from .events import FAMILY_TYPES, day_info, month_grid, tet_info, upcoming
from .lunar import MAX_YEAR, MIN_YEAR

_YEAR = vol.All(vol.Coerce(int), vol.Range(min=MIN_YEAR + 1, max=MAX_YEAR - 1))


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in (ws_overview, ws_month, ws_day, ws_upcoming, ws_events_list, ws_events_save,
                    ws_events_delete, ws_background):
        websocket_api.async_register_command(hass, handler)


def _runtime(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]):
    runtime = hass.data.get(DOMAIN)
    if runtime is None:
        connection.send_error(msg["id"], "not_loaded", "Lịch Việt chưa được cài đặt")
    return runtime


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/overview"})
@callback
def ws_overview(hass, connection, msg):
    """Dữ liệu ban đầu: hôm nay, đếm ngược Tết, 30 ngày tới, cấu hình giao diện."""
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    today = rt.today
    opts = rt.options
    connection.send_result(msg["id"], {
        "today": day_info(today, rt.custom_events, today=today),
        "tet": tet_info(today),
        "upcoming": upcoming(today, 45, rt.custom_events),
        "config": {
            "background": bool(opts.get(CONF_BG_ENABLED, True)),
            "opacity": int(opts.get(CONF_PANEL_OPACITY, DEFAULT_PANEL_OPACITY)),
            "event_types": list(FAMILY_TYPES),
            "is_admin": bool(connection.user and connection.user.is_admin),
        },
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/month",
    vol.Required("year"): _YEAR,
    vol.Required("month"): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
})
@callback
def ws_month(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], {
        "year": msg["year"],
        "month": msg["month"],
        "days": month_grid(msg["year"], msg["month"], rt.custom_events, today=rt.today),
    })


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/day", vol.Required("date"): str})
@callback
def ws_day(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    try:
        d = date.fromisoformat(msg["date"])
        if not MIN_YEAR < d.year < MAX_YEAR:
            raise ValueError
    except ValueError:
        connection.send_error(msg["id"], "invalid_date", "Ngày không hợp lệ")
        return
    connection.send_result(msg["id"], day_info(d, rt.custom_events, today=rt.today))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/upcoming",
    vol.Optional("days", default=30): vol.All(vol.Coerce(int), vol.Range(min=1, max=400)),
})
@callback
def ws_upcoming(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], upcoming(rt.today, msg["days"], rt.custom_events))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/events/list"})
@callback
def ws_events_list(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], rt.custom_events)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/events/save",
    vol.Required("event"): dict,
})
@websocket_api.require_admin
@callback
def ws_events_save(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    try:
        ev = rt.save_event(msg["event"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_event", str(err))
        return
    connection.send_result(msg["id"], ev)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/events/delete",
    vol.Required("event_id"): str,
})
@websocket_api.require_admin
@callback
def ws_events_delete(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    try:
        rt.delete_event(msg["event_id"])
    except ValueError:
        connection.send_error(msg["id"], "not_found", "Không tìm thấy sự kiện")
        return
    connection.send_result(msg["id"], {"deleted": msg["event_id"]})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/background",
    vol.Optional("change", default=False): bool,
})
@websocket_api.async_response
async def ws_background(hass, connection, msg):
    if (rt := _runtime(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], await rt.background.async_get(change=msg["change"]))
