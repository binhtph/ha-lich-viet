"""Kiểm thử nội dung bản tin buổi sáng (nhắc trước mùng 1, rằm, ngày lễ, giỗ)."""

from __future__ import annotations

from datetime import date

from custom_components.lich_viet.notifier import build_morning_message


def _msg(day, holiday=1, monthly=1, custom=()):
    return build_morning_message(day, list(custom), holiday, monthly)


def test_remind_first_day_of_lunar_month():
    title, msg, has = _msg(date(2026, 12, 8))
    assert "Sắp tới:\n• Mùng 1 tháng 11: ngày mai (Thứ Tư 09/12)" in msg
    assert has is True
    assert title == "📅 LỊCH VIỆT › THỨ BA 08/12/2026"


def test_monthly_remind_off():
    _, msg, has = _msg(date(2026, 12, 8), monthly=0)
    assert "Mùng 1" not in msg and has is False


def test_remind_full_moon_two_days_before_together_with_holiday():
    _, msg, _ = _msg(date(2026, 12, 21), holiday=1, monthly=2)
    assert "• Ngày thành lập Quân đội Nhân dân Việt Nam: ngày mai (Thứ Ba 22/12)" in msg
    assert "• Rằm tháng 11: còn 2 ngày (Thứ Tư 23/12)" in msg


def test_named_full_moon_follows_holiday_setting_without_duplicate():
    # 23/11/2026 là rằm tháng 10 = Tết Hạ nguyên (ngày lễ có tên)
    _, msg, has = _msg(date(2026, 11, 22), holiday=0, monthly=1)
    assert "Hạ nguyên" not in msg and "Rằm tháng 10" not in msg and has is False
    _, msg, _ = _msg(date(2026, 11, 22), holiday=1, monthly=1)
    assert msg.count("Rằm tháng 10") == 1
    assert "• Rằm tháng 10 (Tết Hạ nguyên): ngày mai (Thứ Hai 23/11)" in msg


def test_leap_month_full_moon():
    _, msg, _ = _msg(date(2025, 8, 7))
    assert "• Rằm tháng 6 nhuận: ngày mai (Thứ Sáu 08/08)" in msg


def test_tet_not_duplicated_as_first_day():
    _, msg, _ = _msg(date(2027, 2, 5), holiday=1, monthly=1)
    assert "Tết Nguyên Đán: ngày mai" in msg
    assert "Mùng 1 tháng Giêng" not in msg
    assert "Hôm nay:\n• Giao thừa" in msg


def test_today_first_day_and_family_reminder():
    gio = {"id": "a", "name": "Giỗ bà", "type": "gio", "calendar": "lunar", "day": 4, "month": 11,
           "year": None, "remind_days": 3, "icon": "mdi:candle", "note": ""}
    _, msg, has = _msg(date(2026, 12, 9), custom=[gio])
    assert "Hôm nay:\n• Mùng 1 tháng 11" in msg
    assert "• Giỗ bà: còn 3 ngày (Thứ Bảy 12/12, 4/11 âm)" in msg
    assert has is True


def test_years_label_by_event_type():
    be = {"id": "b", "name": "Bé Bin", "type": "sinh_nhat", "calendar": "solar", "day": 21, "month": 12,
          "year": 1994, "repeat": True, "remind_days": 1, "icon": "mdi:cake-variant", "note": ""}
    _, msg, _ = _msg(date(2026, 12, 20), custom=[be], holiday=0, monthly=0)
    assert "• Bé Bin (32 tuổi): ngày mai (Thứ Hai 21/12, 13/11 âm)" in msg
    _, msg, _ = _msg(date(2026, 12, 21), custom=[be], holiday=0, monthly=0)
    assert "Hôm nay:\n• Bé Bin (32 tuổi)" in msg
    cuoi = dict(be, id="c", name="Ngày cưới", type="ky_niem", year=2027, day=10, month=1, remind_days=1)
    _, msg, _ = _msg(date(2027, 1, 9), custom=[cuoi], holiday=0, monthly=0)
    assert "• Ngày cưới: ngày mai" in msg  # năm đầu tiên: không ghi số
    _, msg, _ = _msg(date(2028, 1, 9), custom=[cuoi], holiday=0, monthly=0)
    assert "• Ngày cưới (1 năm): ngày mai" in msg
