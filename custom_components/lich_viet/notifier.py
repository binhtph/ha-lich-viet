"""Thông báo buổi sáng: hôm nay là ngày gì, nhắc trước giỗ/sinh nhật/ngày lễ."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
import html
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    CONF_HOLIDAY_REMIND,
    CONF_MOBILE,
    CONF_MONTHLY_REMIND,
    CONF_ONLY_WHEN_EVENTS,
    CONF_REPORT_TIME,
    CONF_TELEGRAM,
    DEFAULT_HOLIDAY_REMIND,
    DEFAULT_MONTHLY_REMIND,
    DEFAULT_REPORT_TIME,
    NOTIFY_OPEN_PATH,
    SWITCH_MORNING,
)
from .events import CAT_FAMILY, CAT_MONTHLY, Occurrence, day_info, events_between, events_on

_LOGGER = logging.getLogger(__name__)
_MAX_REMIND = 60
WEEKDAYS_SHORT = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")


def channel_key(kind: str, target: str) -> str:
    return f"{kind}:{target}"


def channels(options: dict[str, Any]) -> list[tuple[str, str]]:
    return [("telegram", t) for t in options.get(CONF_TELEGRAM, [])] + [
        ("mobile", m) for m in options.get(CONF_MOBILE, [])
    ]


def mobile_data() -> dict[str, str]:
    """Dữ liệu kèm tin app điện thoại: nhấn vào tin thì mở trang Lịch Việt.

    iOS đọc `url`, Android đọc `clickAction`; mỗi bên bỏ qua khóa của bên kia.
    """
    return {"url": NOTIFY_OPEN_PATH, "clickAction": NOTIFY_OPEN_PATH}


def years_label(years: int | None, event_type: str | None) -> str:
    """'32 tuổi' cho sinh nhật, '16 năm' cho giỗ/kỷ niệm/khác; rỗng nếu không có số."""
    if not years:
        return ""
    return f"{years} tuổi" if event_type == "sinh_nhat" else f"{years} năm"


def _years_text(occ: Occurrence) -> str:
    label = years_label(occ.years, occ.event_type)
    return f" ({label})" if label else ""


def _wd(d: date) -> str:
    return WEEKDAYS_SHORT[d.weekday()]


def _names(occs: list[Occurrence]) -> str:
    return ", ".join(f"{o.name}{_years_text(o)}" for o in occs)


def build_morning_message(
    today: date, custom: list[dict[str, Any]], holiday_remind: int, monthly_remind: int = 0
) -> tuple[str, str, bool]:
    """(tiêu đề, nội dung, có sự kiện hay không) cho bản tin buổi sáng.

    Viết gọn để màn hình khóa thấy đủ (Telegram và app gửi y hệt nhau):
    tiêu đề có ngày âm, mỗi mốc một dòng (hôm nay, ngày mai, còn N ngày), can chi để cuối.

    - Sự kiện gia đình: nhắc trước theo số ngày cài riêng từng sự kiện.
    - Mùng 1, rằm (không trùng ngày lễ có tên): nhắc trước `monthly_remind` ngày.
    - Các ngày lễ còn lại: nhắc trước `holiday_remind` ngày.
    0 = không nhắc.
    """
    info = day_info(today, custom)
    today_events = events_on(today, custom)
    lunar = f"{info['lunar_day']}/{info['lunar_month']}" + (" nhuận" if info["lunar_leap"] else "")
    title = f"📅 LỊCH VIỆT › {_wd(today)} {today:%d/%m} · {lunar} ÂL"

    lines: list[str] = []
    if today_events:
        lines.append(f"Hôm nay: {_names(today_events)}")

    due: dict[date, list[Occurrence]] = {}
    horizon = today + timedelta(days=_MAX_REMIND)
    for occ in events_between(today + timedelta(days=1), horizon, custom, monthly=True):
        days_left = (occ.date - today).days
        if occ.category == CAT_FAMILY:
            ok = occ.remind_days and days_left == occ.remind_days
        elif occ.category == CAT_MONTHLY:
            ok = bool(monthly_remind) and days_left == monthly_remind
        else:
            ok = bool(holiday_remind) and days_left == holiday_remind
        if ok:
            due.setdefault(occ.date, []).append(occ)
    for day in sorted(due):
        days_left = (day - today).days
        when = "Ngày mai" if days_left == 1 else f"Còn {days_left} ngày ({_wd(day)} {day:%d/%m})"
        lines.append(f"{when}: {_names(due[day])}")

    lines.append(f"Ngày {info['can_chi_day']} · năm {info['can_chi_year']}")
    return title, "\n".join(lines), bool(today_events or due)


class LichVietNotifier:
    """Gửi bản tin buổi sáng tới Telegram / app điện thoại."""

    def __init__(self, hass: HomeAssistant, runtime: Any) -> None:
        self.hass = hass
        self.runtime = runtime
        self._unsub: Callable[[], None] | None = None

    @callback
    def async_setup(self) -> None:
        opts = self.runtime.options
        h, m, s = (int(x) for x in str(opts.get(CONF_REPORT_TIME, DEFAULT_REPORT_TIME)).split(":"))
        self._unsub = async_track_time_change(self.hass, self._on_time, hour=h, minute=m, second=s)

    @callback
    def async_unload(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _on_time(self, now: datetime) -> None:
        if not self.runtime.switches.get(SWITCH_MORNING, True):
            return
        await self.async_send_morning(force=False)

    async def async_send_morning(self, *, force: bool = True) -> bool:
        """Gửi bản tin. force=False thì bỏ qua ngày không có gì (nếu đã cài vậy)."""
        opts = self.runtime.options
        title, message, has_events = build_morning_message(
            self.runtime.today,
            self.runtime.custom_events,
            int(opts.get(CONF_HOLIDAY_REMIND, DEFAULT_HOLIDAY_REMIND)),
            int(opts.get(CONF_MONTHLY_REMIND, DEFAULT_MONTHLY_REMIND)),
        )
        if not force and opts.get(CONF_ONLY_WHEN_EVENTS, True) and not has_events:
            return False
        await self.async_send(title, message)
        return True

    async def async_send(self, title: str, message: str) -> None:
        for kind, target in channels(self.runtime.options):
            if not self.runtime.switches.get(channel_key(kind, target), True):
                continue
            try:
                if kind == "telegram":
                    await self.hass.services.async_call(
                        "telegram_bot", "send_message",
                        {"entity_id": [target], "title": f"<b>{html.escape(title)}</b>",
                         "message": html.escape(message), "parse_mode": "html"},
                        blocking=True,
                    )
                else:
                    await self.hass.services.async_call(
                        "notify", target.removeprefix("notify."),
                        {"title": title, "message": message, "data": mobile_data()},
                        blocking=True,
                    )
            except Exception as err:  # noqa: BLE001 - một kênh lỗi không chặn kênh khác
                _LOGGER.warning("Gửi thông báo tới %s lỗi: %s", target, err)
