"""Sensor: âm lịch hôm nay, sự kiện hôm nay, sự kiện sắp tới, đếm ngược Tết, tiết khí."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LichVietEntity
from .events import day_info, events_on, next_event, tet_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([
        LunarDateSensor(entry, "lunar_date"),
        TodayEventsSensor(entry, "today_events"),
        NextEventSensor(entry, "next_event"),
        TetCountdownSensor(entry, "tet_countdown"),
        SolarTermSensor(entry, "solar_term"),
    ])


class LunarDateSensor(LichVietEntity, SensorEntity):
    """Ví dụ: 'Mùng 9 tháng 10'; thuộc tính có đủ can chi, tiết khí, giờ hoàng đạo."""

    _attr_icon = "mdi:calendar-star"

    @property
    def native_value(self) -> str:
        info = day_info(self.runtime.today)
        return f"{info['lunar_day_name']} tháng {info['lunar_month_name']}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = day_info(self.runtime.today)
        return {
            "ngay": info["lunar_day"],
            "thang": info["lunar_month"],
            "nam": info["lunar_year"],
            "thang_nhuan": info["lunar_leap"],
            "so_ngay_trong_thang": info["lunar_month_length"],
            "ngay_am_lich": info["lunar_text"],
            "can_chi_ngay": info["can_chi_day"],
            "can_chi_thang": info["can_chi_month"],
            "can_chi_nam": info["can_chi_year"],
            "con_giap": info["con_giap"],
            "tiet_khi": info["solar_term"],
            "gio_hoang_dao": ", ".join(f"{h['chi']} ({h['gio']}h)" for h in info["gio_hoang_dao"]),
        }


class TodayEventsSensor(LichVietEntity, SensorEntity):
    """Tên các sự kiện hôm nay (rỗng nếu không có)."""

    _attr_icon = "mdi:calendar-today"

    def _events(self):
        return events_on(self.runtime.today, self.runtime.custom_events)

    @property
    def native_value(self) -> str:
        return ", ".join(e.name for e in self._events())[:255] or "Không có"

    @property
    def icon(self) -> str:
        events = self._events()
        return events[0].icon if events else "mdi:calendar-today"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        events = self._events()
        return {
            "so_su_kien": len(events),
            "ngay_nghi_le": any(e.off for e in events),
            "su_kien": [e.as_dict() for e in events],
        }


class NextEventSensor(LichVietEntity, SensorEntity):
    """Ngày lễ hoặc sự kiện gia đình gần nhất (tính cả hôm nay)."""

    def _next(self) -> dict[str, Any] | None:
        return next_event(self.runtime.today, self.runtime.custom_events)

    @property
    def native_value(self) -> str | None:
        nxt = self._next()
        return nxt["name"] if nxt else None

    @property
    def icon(self) -> str:
        nxt = self._next()
        return nxt["icon"] if nxt else "mdi:calendar-arrow-right"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        nxt = self._next()
        if not nxt:
            return {}
        return {
            "ngay": nxt["date"],
            "am_lich": nxt["lunar"],
            "con_lai_ngay": nxt["days_left"],
            "nhom": nxt["category"],
            "ngay_nghi_le": nxt["off"],
            "cung_ngay": nxt["all"],
        }


class TetCountdownSensor(LichVietEntity, SensorEntity):
    """Số ngày còn lại tới Tết Nguyên Đán."""

    _attr_icon = "mdi:firework"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> int:
        return tet_info(self.runtime.today)["days_left"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        tet = tet_info(self.runtime.today)
        return {"ngay_tet": tet["date"], "nam": tet["year_name"], "con_giap": tet["con_giap"]}


class SolarTermSensor(LichVietEntity, SensorEntity):
    """Tiết khí hiện tại."""

    _attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self) -> str:
        return day_info(self.runtime.today)["solar_term"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = day_info(self.runtime.today)
        return {"tiet_khi_ke_tiep": info["next_solar_term"], "ngay_bat_dau": info["next_solar_term_date"]}
