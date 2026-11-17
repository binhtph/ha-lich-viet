"""Calendar entity: ngày lễ, mùng 1/rằm và sự kiện gia đình (xem trong mục Lịch của HA)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LichVietEntity
from .events import Occurrence, events_between
from .lunar import MAX_YEAR, MIN_YEAR
from .notifier import years_label

PARALLEL_UPDATES = 0
_MAX_RANGE_DAYS = 800


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([LichVietCalendar(entry, "calendar")])


def _to_event(occ: Occurrence) -> CalendarEvent:
    lunar = occ.as_dict()["lunar"]
    details = [f"Âm lịch: {lunar}"] if lunar else []
    if label := years_label(occ.years, occ.event_type):
        details.append(label)
    if occ.off:
        details.append("Ngày nghỉ lễ")
    if occ.note:
        details.append(occ.note)
    return CalendarEvent(
        start=occ.date,
        end=occ.date + timedelta(days=1),
        summary=occ.name,
        description="\n".join(details) or None,
        uid=f"{occ.id}_{occ.date.isoformat()}",
    )


class LichVietCalendar(LichVietEntity, CalendarEntity):
    _attr_icon = "mdi:calendar-star"

    @property
    def event(self) -> CalendarEvent | None:
        today = self.runtime.today
        occs = events_between(today, today + timedelta(days=400), self.runtime.custom_events, monthly=False)
        return _to_event(occs[0]) if occs else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        start = dt_util.as_local(start_date).date() if isinstance(start_date, datetime) else start_date
        end = dt_util.as_local(end_date).date() if isinstance(end_date, datetime) else end_date
        start = max(start, date(MIN_YEAR + 1, 1, 1))
        end = min(end, start + timedelta(days=_MAX_RANGE_DAYS), date(MAX_YEAR - 1, 12, 31))
        if end < start:
            return []
        custom = list(self.runtime.custom_events)
        occs = await hass.async_add_executor_job(events_between, start, end, custom)
        return [_to_event(o) for o in occs]
