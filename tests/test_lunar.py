"""Kiểm thử phần tính lịch âm (đối chiếu số liệu đã biết)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.lich_viet.lunar import (
    LunarDate,
    can_chi_day,
    can_chi_month,
    can_chi_year,
    con_giap,
    gio_hoang_dao,
    leap_month_of_year,
    lunar_text,
    lunar_to_solar,
    month_length,
    next_solar_term,
    next_tet,
    SOLAR_TERMS,
    solar_term,
    solar_term_starts,
    solar_to_lunar,
)

# Tết Nguyên Đán theo lịch Việt Nam (UTC+7).
TET = {
    1985: date(1985, 1, 21),  # Việt Nam ăn Tết sớm hơn Trung Quốc 1 tháng (20/2/1985)
    1990: date(1990, 1, 27), 1995: date(1995, 1, 31),
    2000: date(2000, 2, 5), 2001: date(2001, 1, 24), 2002: date(2002, 2, 12),
    2003: date(2003, 2, 1), 2004: date(2004, 1, 22), 2005: date(2005, 2, 9),
    2006: date(2006, 1, 29),
    2007: date(2007, 2, 17),  # Trung Quốc: 18/2/2007
    2008: date(2008, 2, 7), 2009: date(2009, 1, 26), 2010: date(2010, 2, 14),
    2011: date(2011, 2, 3), 2012: date(2012, 1, 23), 2013: date(2013, 2, 10),
    2014: date(2014, 1, 31), 2015: date(2015, 2, 19), 2016: date(2016, 2, 8),
    2017: date(2017, 1, 28), 2018: date(2018, 2, 16), 2019: date(2019, 2, 5),
    2020: date(2020, 1, 25), 2021: date(2021, 2, 12), 2022: date(2022, 2, 1),
    2023: date(2023, 1, 22), 2024: date(2024, 2, 10), 2025: date(2025, 1, 29),
    2026: date(2026, 2, 17), 2027: date(2027, 2, 6), 2028: date(2028, 1, 26),
    2029: date(2029, 2, 13),
    2030: date(2030, 2, 2),  # sóc 16:07 UTC: Việt Nam 2/2, Trung Quốc 3/2
}

# Tháng nhuận âm lịch Việt Nam.
LEAP = {2001: 4, 2004: 2, 2006: 7, 2009: 5, 2012: 4, 2014: 9, 2017: 6, 2020: 4,
        2023: 2, 2025: 6, 2028: 5}


@pytest.mark.parametrize(("year", "tet"), TET.items())
def test_tet_dates(year, tet):
    assert solar_to_lunar(tet) == LunarDate(1, 1, year, False)
    assert lunar_to_solar(1, 1, year) == tet
    # hôm trước là ngày cuối tháng Chạp năm trước
    eve = solar_to_lunar(tet - timedelta(days=1))
    assert (eve.month, eve.year, eve.leap) == (12, year - 1, False)
    assert eve.day in (29, 30)


@pytest.mark.parametrize("year", range(2000, 2031))
def test_leap_months(year):
    assert leap_month_of_year(year) == LEAP.get(year)


def test_known_leap_month_dates():
    assert solar_to_lunar(date(2025, 7, 25)) == LunarDate(1, 6, 2025, True)
    assert solar_to_lunar(date(2023, 3, 22)) == LunarDate(1, 2, 2023, True)
    assert solar_to_lunar(date(2020, 5, 23)) == LunarDate(1, 4, 2020, True)
    assert lunar_to_solar(1, 6, 2025, True) == date(2025, 7, 25)
    assert lunar_to_solar(1, 6, 2025, False) == date(2025, 6, 25)
    assert lunar_to_solar(1, 5, 2025, True) is None  # 2025 không nhuận tháng 5
    assert lunar_to_solar(1, 1, 2026, True) is None  # 2026 không nhuận


def test_lunation_estimate_edge_case():
    # ước lượng chu kỳ trung bình lệch 1 tháng ở ngày này (lỗi cũ: ngày âm = 0)
    lunar = solar_to_lunar(date(2054, 5, 7))
    assert 1 <= lunar.day <= 30


def test_round_trip_every_day_1900_2150():
    d = date(1900, 2, 1)
    prev = solar_to_lunar(d - timedelta(days=1))
    while d <= date(2150, 12, 31):
        lunar = solar_to_lunar(d)
        assert lunar_to_solar(lunar.day, lunar.month, lunar.year, lunar.leap) == d, d
        if lunar.day == 1:
            assert prev.day in (29, 30), d
            if not lunar.leap:
                assert lunar.month == prev.month % 12 + 1, d
            else:
                assert (lunar.month, lunar.year) == (prev.month, prev.year), d
        else:
            assert (lunar.day, lunar.month, lunar.year, lunar.leap) == (
                prev.day + 1, prev.month, prev.year, prev.leap), d
        prev = lunar
        d += timedelta(days=1)


def test_month_length_and_invalid_day():
    # tháng Chạp Ất Tỵ bắt đầu 19/1/2026, thiếu (29 ngày): giao thừa 16/2, ông Táo 10/2
    assert solar_to_lunar(date(2026, 1, 19)) == LunarDate(1, 12, 2025)
    assert month_length(date(2026, 2, 16)) == 29
    assert lunar_to_solar(30, 12, 2025) is None
    assert lunar_to_solar(23, 12, 2025) == date(2026, 2, 10)
    for d in (date(2026, 1, 1), date(2026, 6, 1), date(2027, 3, 3)):
        length = month_length(d)
        lunar = solar_to_lunar(d)
        assert length in (29, 30)
        assert (lunar_to_solar(30, lunar.month, lunar.year, lunar.leap) is not None) == (length == 30)
    with pytest.raises(ValueError):
        solar_to_lunar(date(1700, 1, 1))


def test_can_chi():
    assert can_chi_day(date(2000, 1, 1)) == "Mậu Ngọ"
    assert can_chi_day(date(2026, 11, 17)) == "Ất Mùi"
    assert can_chi_year(2024) == "Giáp Thìn"
    assert can_chi_year(2026) == "Bính Ngọ"
    assert can_chi_year(1984) == "Giáp Tý"
    assert can_chi_year(2000) == "Canh Thìn"
    assert can_chi_year(1975) == "Ất Mão"
    assert can_chi_month(1, 2024) == "Bính Dần"
    assert can_chi_month(11, 2024) == "Bính Tý"
    assert can_chi_month(1, 2026) == "Canh Dần"
    assert can_chi_month(10, 2026) == "Kỷ Hợi"
    assert con_giap(2026) == "Ngựa"
    # 60 ngày lặp lại một vòng can chi
    assert can_chi_day(date(2026, 1, 1)) == can_chi_day(date(2026, 1, 1) + timedelta(days=60))


def test_gio_hoang_dao():
    hours = gio_hoang_dao(date(2026, 11, 17))  # ngày Mùi
    assert [h["chi"] for h in hours] == ["Dần", "Mão", "Tỵ", "Thân", "Tuất", "Hợi"]
    assert hours[0]["gio"] == "3-5"
    for offset in range(12):
        assert len(gio_hoang_dao(date(2026, 1, 1) + timedelta(days=offset))) == 6


def test_solar_terms_2026():
    assert solar_term_starts(date(2026, 3, 20)) == SOLAR_TERMS.index("Xuân phân")
    assert solar_term_starts(date(2026, 6, 21)) == SOLAR_TERMS.index("Hạ chí")
    assert solar_term_starts(date(2026, 9, 23)) == SOLAR_TERMS.index("Thu phân")
    assert solar_term_starts(date(2026, 12, 22)) == SOLAR_TERMS.index("Đông chí")
    assert solar_term_starts(date(2025, 12, 21)) == SOLAR_TERMS.index("Đông chí")
    assert SOLAR_TERMS[solar_term(date(2026, 11, 17))] == "Lập đông"
    idx, day = next_solar_term(date(2026, 11, 17))
    assert SOLAR_TERMS[idx] == "Tiểu tuyết" and day in (date(2026, 11, 22), date(2026, 11, 23))
    # mỗi năm đúng 24 tiết khí
    count = sum(1 for i in range(365) if solar_term_starts(date(2026, 1, 1) + timedelta(days=i)) is not None)
    assert count == 24


def test_texts_and_next_tet():
    assert lunar_text(solar_to_lunar(date(2026, 11, 17))) == "Mùng 9 tháng 10 năm Bính Ngọ"
    assert lunar_text(LunarDate(15, 1, 2026)) == "15 tháng Giêng năm Bính Ngọ"
    assert lunar_text(LunarDate(1, 6, 2025, True)) == "Mùng 1 tháng 6 nhuận năm Ất Tỵ"
    assert next_tet(date(2026, 11, 17)) == date(2027, 2, 6)
    assert next_tet(date(2026, 2, 17)) == date(2026, 2, 17)
    assert next_tet(date(2026, 2, 18)) == date(2027, 2, 6)


@pytest.fixture
def utc8():
    """Chạy cùng thuật toán với múi giờ Bắc Kinh để đối chiếu bảng lịch Trung Quốc."""
    import custom_components.lich_viet.lunar as mod

    caches = (mod._new_moon_day, mod._lunar_month_11, mod._leap_month_offset, mod._solar_to_lunar_jd)
    for f in caches:
        f.cache_clear()
    mod.TIMEZONE = 8.0
    yield mod
    mod.TIMEZONE = 7.0
    for f in caches:
        f.cache_clear()


def test_algorithm_matches_official_chinese_tables_at_utc8(utc8):
    """Cùng thuật toán, đặt UTC+8, phải khớp bảng lịch chính thức Trung Quốc (thư viện lunardate)
    cho mọi ngày 1979–2090. Đây là phép kiểm độc lập cho phần thiên văn. (Thuật toán là gần đúng:
    ngoài khoảng này có vài tháng sóc rơi sát nửa đêm bị lệch 1 ngày, vd. 7/8/2097.)"""
    lunardate = pytest.importorskip("lunardate")
    d = date(1979, 1, 1)
    while d <= date(2090, 12, 31):
        ours = utc8.solar_to_lunar(d)
        ref = lunardate.LunarDate.from_solar_date(d.year, d.month, d.day)
        assert (ours.day, ours.month, ours.year, ours.leap) == (
            ref.day, ref.month, ref.year, bool(ref.is_leap_month)), d
        d += timedelta(days=1)


def test_vietnam_differs_from_china_on_known_dates():
    """Các năm nổi tiếng Việt Nam và Trung Quốc ăn Tết khác ngày."""
    lunardate = pytest.importorskip("lunardate")
    for vn_tet, cn_tet in ((date(1985, 1, 21), date(1985, 2, 20)), (date(2007, 2, 17), date(2007, 2, 18)),
                           (date(2030, 2, 2), date(2030, 2, 3))):
        assert solar_to_lunar(vn_tet) == LunarDate(1, 1, vn_tet.year)
        ref = lunardate.LunarDate.from_solar_date(cn_tet.year, cn_tet.month, cn_tet.day)
        assert (ref.day, ref.month) == (1, 1)
