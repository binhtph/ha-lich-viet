"""Công tắc: bật/tắt bản tin buổi sáng và từng kênh gửi."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .const import SWITCH_MORNING
from .entity import LichVietEntity
from .notifier import channel_key, channels

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    entities = [LichVietSwitch(entry, SWITCH_MORNING, SWITCH_MORNING)]
    for kind, target in channels(runtime.options):
        state = hass.states.get(target) if kind == "telegram" else None
        label = state.name if state else target.removeprefix("notify.").removeprefix("mobile_app_")
        entities.append(LichVietSwitch(entry, f"ch_{kind}_{slugify(target)}", channel_key(kind, target),
                                       translation_key=f"channel_{kind}", placeholders={"target": label}))
    async_add_entities(entities)


class LichVietSwitch(LichVietEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, uid: str, key: str, *, translation_key: str | None = None,
                 placeholders: dict[str, str] | None = None) -> None:
        super().__init__(entry, uid)
        self._key = key
        self._attr_translation_key = translation_key or key
        self._attr_translation_placeholders = placeholders or {}

    @property
    def is_on(self) -> bool:
        return self.runtime.switches.get(self._key, True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.runtime.set_switch(self._key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.runtime.set_switch(self._key, False)
        self.async_write_ha_state()
