"""Binary sensor: ngày nghỉ lễ, mùng 1, rằm, có sự kiện (dùng cho automation)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LichVietEntity
from .events import events_on
from .lunar import solar_to_lunar

PARALLEL_UPDATES = 0

ICONS = {
    "holiday": ("mdi:flag-variant", "mdi:flag-variant-outline"),
    "first_day": ("mdi:moon-new", "mdi:moon-waxing-crescent"),
    "full_moon": ("mdi:moon-full", "mdi:moon-waning-gibbous"),
    "has_event": ("mdi:calendar-star", "mdi:calendar-blank"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(LichVietBinarySensor(entry, key) for key in ICONS)


class LichVietBinarySensor(LichVietEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool:
        today = self.runtime.today
        key = self._attr_translation_key
        if key == "first_day":
            return solar_to_lunar(today).day == 1
        if key == "full_moon":
            return solar_to_lunar(today).day == 15
        events = events_on(today, self.runtime.custom_events)
        if key == "holiday":
            return any(e.off for e in events)
        return bool(events)

    @property
    def icon(self) -> str:
        on, off = ICONS[self._attr_translation_key]
        return on if self.is_on else off
