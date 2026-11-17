"""Chạy thật automation mẫu "Nhắc lịch ăn chay" trong README để bảo đảm nó đúng."""

from __future__ import annotations

from pathlib import Path
import re

import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

README = Path(__file__).parent.parent / "README.md"


def _automation(ngay_chay: list[int]) -> dict:
    text = README.read_text(encoding="utf-8")
    section = text[text.index("### Ví dụ automation: nhắc lịch ăn chay"):]
    block = re.search(r"```yaml\n(.*?)```", section, re.S).group(1)
    config = yaml.safe_load(block)
    config["variables"]["ngay_chay"] = ngay_chay
    config["id"] = "an_chay"
    return config


async def _run(hass, freezer, ngay_chay, lunar_day, month_len, when):
    calls = async_mock_service(hass, "notify", "notify")
    freezer.move_to(f"2026-11-17 {when}+07:00")
    hass.states.async_set("sensor.lich_viet_lunar_date", "x",
                          {"ngay": lunar_day, "so_ngay_trong_thang": month_len})
    assert await async_setup_component(hass, "automation", {"automation": [_automation(ngay_chay)]})
    await hass.async_block_till_done()
    hh, mm = (20, 0) if when.startswith("19") else (6, 0)
    freezer.move_to(f"2026-11-17 {hh:02d}:{mm:02d}:00+07:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    return calls


@pytest.fixture(autouse=True)
async def _tz(hass):
    await hass.config.async_set_time_zone("Asia/Ho_Chi_Minh")


@pytest.mark.parametrize(
    ("ngay_chay", "lunar_day", "month_len", "when", "expected"),
    [
        # tối hôm trước
        ([1, 15], 14, 30, "19:59:58", "Ngày mai là rằm âm lịch, nhớ ăn chay."),
        ([1, 15], 30, 30, "19:59:58", "Ngày mai là mùng 1 âm lịch, nhớ ăn chay."),
        ([1, 15], 29, 29, "19:59:58", "Ngày mai là mùng 1 âm lịch, nhớ ăn chay."),
        ([1, 15], 13, 30, "19:59:58", None),
        # 4 ngày: 30 = cuối tháng, tháng thiếu tính vào 29
        ([1, 14, 15, 30], 28, 29, "19:59:58", "Ngày mai là ngày cuối tháng âm lịch, nhớ ăn chay."),
        ([1, 14, 15, 30], 29, 30, "19:59:58", "Ngày mai là ngày cuối tháng âm lịch, nhớ ăn chay."),
        ([1, 14, 15, 30], 13, 30, "19:59:58", "Ngày mai là ngày 14 âm lịch, nhớ ăn chay."),
        # sáng hôm đó
        ([1, 15], 15, 30, "05:59:58", "Hôm nay là rằm âm lịch, nhớ ăn chay."),
        ([1, 15], 1, 29, "05:59:58", "Hôm nay là mùng 1 âm lịch, nhớ ăn chay."),
        ([1, 14, 15, 30], 29, 29, "05:59:58", "Hôm nay là ngày cuối tháng âm lịch, nhớ ăn chay."),
        ([1, 14, 15, 30], 29, 30, "05:59:58", None),
        ([1, 8, 14, 15, 18, 23, 24, 28, 29, 30], 8, 30, "05:59:58", "Hôm nay là ngày 8 âm lịch, nhớ ăn chay."),
        ([1, 15], 2, 30, "05:59:58", None),
    ],
)
async def test_an_chay_automation(hass: HomeAssistant, freezer, ngay_chay, lunar_day, month_len, when, expected):
    calls = await _run(hass, freezer, ngay_chay, lunar_day, month_len, when)
    if expected is None:
        assert calls == []
    else:
        assert len(calls) == 1
        assert calls[0].data["message"] == expected
        assert calls[0].data["title"] == "🥗 Lịch ăn chay"


async def test_sensor_missing_does_not_notify(hass: HomeAssistant, freezer):
    calls = async_mock_service(hass, "notify", "notify")
    freezer.move_to("2026-11-17 05:59:58+07:00")
    assert await async_setup_component(hass, "automation", {"automation": [_automation([1, 15])]})
    await hass.async_block_till_done()
    freezer.move_to("2026-11-17 06:00:00+07:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert calls == []
