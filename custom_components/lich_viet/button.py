"""Nút: gửi thử bản tin buổi sáng."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import LichVietEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([SendReportButton(entry, "send_report")])


class SendReportButton(LichVietEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        await self.runtime.notifier.async_send_morning(force=True)
