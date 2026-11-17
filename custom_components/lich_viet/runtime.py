"""Trạng thái chạy của Lịch Việt: sự kiện gia đình, công tắc, cập nhật hằng ngày."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
import logging
from typing import Any
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SAVE_DELAY, STORAGE_VERSION
from .events import normalize_custom_event

_LOGGER = logging.getLogger(__name__)


class LichVietRuntime:
    """Dữ liệu dùng chung cho entity, websocket, thông báo và ảnh nền."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.data")
        self.custom_events: list[dict[str, Any]] = []
        self.switches: dict[str, bool] = {}
        self.unsplash_cache: dict[str, Any] = {}
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []
        self.notifier: Any = None
        self.background: Any = None

    @property
    def options(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    @property
    def today(self) -> date:
        return dt_util.now().date()

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.custom_events = []
        for raw in data.get("events", []):
            try:
                ev = normalize_custom_event(raw)
            except ValueError:
                _LOGGER.warning("Bỏ qua sự kiện lỗi trong storage: %s", raw)
                continue
            ev["id"] = raw.get("id") or uuid.uuid4().hex[:12]
            self.custom_events.append(ev)
        self.switches = dict(data.get("switches", {}))
        self.unsplash_cache = dict(data.get("unsplash", {}))
        self._unsubs.append(
            async_track_time_change(self.hass, self._on_midnight, hour=0, minute=0, second=2)
        )

    @callback
    def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    async def async_flush(self) -> None:
        await self._store.async_save(self._data())

    def _data(self) -> dict[str, Any]:
        return {"events": self.custom_events, "switches": self.switches, "unsplash": self.unsplash_cache}

    @callback
    def schedule_save(self) -> None:
        self._store.async_delay_save(self._data, SAVE_DELAY)

    # ------------------------------------------------------------ listeners
    @callback
    def add_listener(self, update: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update)

        @callback
        def remove() -> None:
            if update in self._listeners:
                self._listeners.remove(update)

        return remove

    @callback
    def notify_listeners(self) -> None:
        for update in list(self._listeners):
            update()

    @callback
    def _on_midnight(self, _now: datetime) -> None:
        self.notify_listeners()

    # ------------------------------------------------------------ sự kiện gia đình
    @callback
    def save_event(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Thêm hoặc sửa sự kiện. Ném ValueError nếu dữ liệu sai hoặc không tìm thấy id."""
        ev = normalize_custom_event(raw)
        if ev["id"]:
            for i, old in enumerate(self.custom_events):
                if old["id"] == ev["id"]:
                    self.custom_events[i] = ev
                    break
            else:
                raise ValueError("not_found")
        else:
            ev["id"] = uuid.uuid4().hex[:12]
            self.custom_events.append(ev)
        self.custom_events.sort(key=lambda e: (e["calendar"], e["month"], e["day"], e["name"]))
        self.schedule_save()
        self.notify_listeners()
        return ev

    @callback
    def delete_event(self, event_id: str) -> None:
        before = len(self.custom_events)
        self.custom_events = [e for e in self.custom_events if e["id"] != event_id]
        if len(self.custom_events) == before:
            raise ValueError("not_found")
        self.schedule_save()
        self.notify_listeners()

    # ------------------------------------------------------------ công tắc
    @callback
    def set_switch(self, key: str, value: bool) -> None:
        self.switches[key] = value
        self.schedule_save()
