"""Kiểm thử ngày lễ, mùng 1/rằm, sự kiện gia đình."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.lich_viet.events import (
    BACKGROUND_FOLDERS,
    HOLIDAYS,
    background_folders_for,
    day_info,
    events_between,
    events_on,
    find_holiday,
    month_grid,
    next_event,
    normalize_custom_event,
    tet_info,
    upcoming,
)


def _ids(d, custom=()):
    return [e.id for e in events_on(d, custom)]


@pytest.mark.parametrize(
    ("holiday_id", "year", "expected"),
    [
        ("gio_to", 2024, date(2024, 4, 18)),
        ("gio_to", 2025, date(2025, 4, 7)),
        ("trung_thu", 2024, date(2024, 9, 17)),
        ("trung_thu", 2025, date(2025, 10, 6)),
        ("vu_lan", 2024, date(2024, 8, 18)),
        ("phat_dan", 2024, date(2024, 5, 22)),
        ("doan_ngo", 2025, date(2025, 5, 31)),
        ("ong_tao", 2024, date(2024, 2, 2)),
        ("ong_tao", 2026, date(2026, 2, 10)),
        ("tet_nguyen_dan", 2026, date(2026, 2, 17)),
        ("giao_thua", 2026, date(2026, 2, 16)),
        ("giao_thua", 2025, date(2025, 1, 28)),
        ("quoc_khanh", 2026, date(2026, 9, 2)),
        ("nha_giao", 2026, date(2026, 11, 20)),
    ],
)
def test_known_holiday_dates(holiday_id, year, expected):
    assert find_holiday(holiday_id, year) == expected


def test_every_builtin_holiday_occurs_once_per_year():
    for year in (2024, 2025, 2026, 2027):
        occ = events_between(date(year, 1, 1), date(year, 12, 31), monthly=False)
        ids = [o.id for o in occ]
        for h in HOLIDAYS:
            # ông Táo/Tết có thể rơi 0 hoặc 1 lần trong năm dương (luôn 1 với các năm này)
            assert ids.count(h.id) == 1, (year, h.id)
        assert ids.count("giao_thua") == 1
        assert ids.count("thanh_minh") == 1


def test_thanh_minh_in_early_april():
    for year in range(2020, 2031):
        d = find_holiday("thanh_minh", year)
        assert d in (date(year, 4, 4), date(year, 4, 5)), (year, d)


def test_monthly_markers_and_dedupe():
    assert _ids(date(2026, 11, 9)) == ["mung_1"]  # mùng 1 tháng 10
    assert events_on(date(2026, 11, 9))[0].name == "Mùng 1 tháng 10"
    # rằm tháng 10 có tên riêng (Tết Hạ nguyên) nên không thêm "Rằm" chung
    assert _ids(date(2026, 11, 23)) == ["ha_nguyen"]
    assert _ids(date(2026, 2, 17)) == ["tet_nguyen_dan"]  # mùng 1 Tết không lặp "Mùng 1"
    assert _ids(date(2026, 3, 3)) == ["ram_thang_gieng"]
    # tháng nhuận cũng có mùng 1 và rằm
    leap = events_on(date(2025, 7, 25))
    assert [e.name for e in leap] == ["Mùng 1 tháng 6 nhuận"]
    # rằm tháng 6 nhuận 2025 không phải ngày lễ nào khác
    assert [e.name for e in events_on(date(2025, 8, 8))] == ["Rằm tháng 6 nhuận"]


def test_off_days():
    assert day_info(date(2026, 9, 2))["is_off"] is True
    assert day_info(date(2026, 2, 16))["is_off"] is True  # giao thừa
    assert day_info(date(2026, 11, 20))["is_off"] is False
    assert day_info(date(2026, 4, 26))["is_off"] is True  # giỗ tổ 10/3 Bính Ngọ


GIO_ONG = {"id": "a1", "name": "Giỗ ông nội", "type": "gio", "calendar": "lunar", "day": 15, "month": 11,
           "year": 2010, "remind_days": 3, "icon": "mdi:candle", "note": ""}


def test_custom_lunar_event_and_years():
    occ = [o for o in events_on(date(2026, 12, 23), [GIO_ONG]) if o.source == "custom"]
    assert len(occ) == 1
    assert occ[0].name == "Giỗ ông nội" and occ[0].years == 16 and occ[0].remind_days == 3
    assert occ[0].as_dict()["lunar"] == "15/11"


def test_custom_lunar_day_30_in_short_month():
    ev = dict(GIO_ONG, id="b", day=30, month=12, year=None)
    # tháng Chạp Ất Tỵ thiếu: tính vào 29 Chạp = 16/2/2026
    assert "custom_b" in _ids(date(2026, 2, 16), [ev])
    hits = [o for o in events_between(date(2026, 1, 1), date(2026, 12, 31), [ev]) if o.source == "custom"]
    assert len(hits) == 1


def test_custom_lunar_event_not_in_leap_month():
    ev = dict(GIO_ONG, id="c", day=10, month=6, year=None)
    hits = [o.date for o in events_between(date(2025, 1, 1), date(2025, 12, 31), [ev]) if o.source == "custom"]
    assert hits == [date(2025, 7, 4)]  # 10/6 thường, không lặp ở tháng 6 nhuận


def test_custom_solar_feb_29():
    ev = {"id": "d", "name": "Sinh nhật", "type": "sinh_nhat", "calendar": "solar", "day": 29, "month": 2,
          "year": 2000, "remind_days": 0, "icon": "mdi:cake-variant", "note": ""}
    assert "custom_d" in _ids(date(2028, 2, 29), [ev])
    assert "custom_d" not in _ids(date(2028, 2, 28), [ev])
    occ = [o for o in events_on(date(2027, 2, 28), [ev]) if o.source == "custom"]
    assert occ and occ[0].years == 27


def test_normalize_custom_event():
    ok = normalize_custom_event({"name": " Giỗ bà ", "calendar": "lunar", "day": "8", "month": "3",
                                 "type": "gio", "remind_days": "2", "year": ""})
    assert ok["name"] == "Giỗ bà" and ok["day"] == 8 and ok["year"] is None and ok["icon"] == "mdi:candle"
    for bad, code in (
        ({"name": "", "day": 1, "month": 1}, "name_required"),
        ({"name": "x", "day": 31, "month": 1, "calendar": "lunar"}, "date_invalid"),
        ({"name": "x", "day": 31, "month": 4, "calendar": "solar"}, "date_invalid"),
        ({"name": "x", "day": 1, "month": 13}, "date_invalid"),
        ({"name": "x", "day": 1, "month": 1, "calendar": "abc"}, "calendar_invalid"),
        ({"name": "x", "day": 1, "month": 1, "type": "abc"}, "type_invalid"),
        ({"name": "x", "day": 1, "month": 1, "remind_days": 99}, "remind_invalid"),
        ({"name": "x", "day": 1, "month": 1, "year": 1500}, "year_invalid"),
    ):
        with pytest.raises(ValueError, match=code):
            normalize_custom_event(bad)


def test_day_info_today():
    info = day_info(date(2026, 11, 17), today=date(2026, 11, 17))
    assert info["lunar_text"] == "Mùng 9 tháng 10 năm Bính Ngọ"
    assert info["can_chi_day"] == "Ất Mùi" and info["can_chi_month"] == "Kỷ Hợi"
    assert info["solar_term"] == "Lập đông" and info["next_solar_term"] == "Tiểu tuyết"
    assert info["weekday_name"] == "Thứ Ba" and info["is_today"] is True
    assert info["lunar_month_length"] in (29, 30)
    assert len(info["gio_hoang_dao"]) == 6


def test_month_grid():
    grid = month_grid(2026, 11, today=date(2026, 11, 17))
    assert len(grid) == 42
    assert grid[0]["date"] == "2026-10-26" and grid[0]["in_month"] is False
    assert grid[6]["date"] == "2026-11-01" and grid[6]["weekday"] == 6
    today = [g for g in grid if g["is_today"]]
    assert len(today) == 1 and today[0]["lunar_day"] == 9
    nov9 = next(g for g in grid if g["date"] == "2026-11-09")
    assert nov9["lunar_day"] == 1 and nov9["lunar_month"] == 10
    assert [e["id"] for e in nov9["events"]] == ["mung_1"]
    # tháng bắt đầu đúng thứ Hai
    feb = month_grid(2027, 2)
    assert feb[0]["date"] == "2027-02-01"


def test_upcoming_next_event_and_tet():
    up = upcoming(date(2026, 11, 17), 40, [GIO_ONG])
    names = [u["name"] for u in up]
    assert names[:2] == ["Ngày Nhà giáo Việt Nam", "Rằm tháng 10 (Tết Hạ nguyên)"]
    assert up[0]["days_left"] == 3 and up[0]["weekday_name"] == "Thứ Sáu"
    assert "Giỗ ông nội" in names
    nxt = next_event(date(2026, 11, 17))
    assert nxt["id"] == "nha_giao" and nxt["days_left"] == 3
    assert next_event(date(2026, 11, 20))["days_left"] == 0
    tet = tet_info(date(2026, 11, 17))
    assert tet == {"date": "2027-02-06", "days_left": 81, "year_name": "Đinh Mùi", "con_giap": "Dê"}


def test_background_occasions():
    assert background_folders_for(date(2026, 2, 10)) == ["tet"]  # Tết 17/2, trước 7 ngày
    assert background_folders_for(date(2026, 2, 24)) == ["tet"]
    assert background_folders_for(date(2026, 2, 25)) == []
    assert background_folders_for(date(2026, 9, 25)) == ["trung_thu"]
    assert background_folders_for(date(2026, 9, 2)) == ["quoc_khanh"]
    assert background_folders_for(date(2026, 12, 22)) == ["giang_sinh"]
    assert background_folders_for(date(2026, 11, 17)) == []
    assert "chung" in BACKGROUND_FOLDERS


def test_year_range_performance():
    occ = events_between(date(2026, 1, 1), date(2026, 12, 31), [GIO_ONG])
    assert len(occ) > 40
    assert all(o.date.year == 2026 for o in occ)
    assert occ == sorted(occ, key=lambda o: o.date)
    assert date(2026, 1, 1) + timedelta(days=364) == date(2026, 12, 31)


def test_short_names_for_calendar_cells():
    assert [e.as_dict()["short"] for e in events_on(date(2026, 11, 20))] == ["Nhà giáo VN"]
    assert [e.as_dict()["short"] for e in events_on(date(2026, 11, 9))] == ["Mùng 1"]
    ev = dict(GIO_ONG, id="s", name="Giỗ cụ cố")
    custom = [e.as_dict()["short"] for e in events_on(date(2026, 12, 23), [ev]) if e.source == "custom"]
    assert custom == ["Giỗ cụ cố"]
    for h in HOLIDAYS:
        occ = [e for e in events_between(date(2026, 1, 1), date(2027, 2, 28), monthly=False) if e.id == h.id]
        assert occ and len(occ[0].as_dict()["short"]) <= 20, h.id
