"""Kiểm thử nội dung bản tin buổi sáng (nhắc trước mùng 1, rằm, ngày lễ, giỗ)."""

from __future__ import annotations

from datetime import date

from custom_components.lich_viet.const import PANEL_URL
from custom_components.lich_viet.notifier import build_morning_message, mobile_data


def _msg(day, holiday=1, monthly=1, custom=()):
    return build_morning_message(day, list(custom), holiday, monthly)


def test_remind_first_day_of_lunar_month():
    title, msg, has = _msg(date(2026, 12, 8))
    assert msg == "Ngày mai: Mùng 1 tháng 11\nNgày Bính Thìn · năm Bính Ngọ"
    assert has is True
    assert title == "📅 LỊCH VIỆT › T3 08/12 · 30/10 ÂL"


def test_monthly_remind_off():
    _, msg, has = _msg(date(2026, 12, 8), monthly=0)
    assert "Mùng 1" not in msg and has is False


def test_remind_full_moon_two_days_before_together_with_holiday():
    _, msg, _ = _msg(date(2026, 12, 21), holiday=1, monthly=2)
    assert msg.splitlines() == [
        "Ngày mai: Ngày thành lập Quân đội Nhân dân Việt Nam",
        "Còn 2 ngày (T4 23/12): Rằm tháng 11",
        "Ngày Kỷ Tỵ · năm Bính Ngọ",
    ]


def test_named_full_moon_follows_holiday_setting_without_duplicate():
    # 23/11/2026 là rằm tháng 10 = Tết Hạ nguyên (ngày lễ có tên)
    _, msg, has = _msg(date(2026, 11, 22), holiday=0, monthly=1)
    assert "Hạ nguyên" not in msg and "Rằm tháng 10" not in msg and has is False
    _, msg, _ = _msg(date(2026, 11, 22), holiday=1, monthly=1)
    assert msg.count("Rằm tháng 10") == 1
    assert "Ngày mai: Rằm tháng 10 (Tết Hạ nguyên)" in msg


def test_leap_month_full_moon():
    title, msg, _ = _msg(date(2025, 8, 7))
    assert title == "📅 LỊCH VIỆT › T5 07/08 · 14/6 nhuận ÂL"
    assert "Ngày mai: Rằm tháng 6 nhuận" in msg


def test_tet_not_duplicated_as_first_day():
    _, msg, _ = _msg(date(2027, 2, 5), holiday=1, monthly=1)
    assert "Ngày mai: Tết Nguyên Đán" in msg
    assert "Mùng 1 tháng Giêng" not in msg
    assert msg.startswith("Hôm nay: Giao thừa\n")


def test_today_first_day_and_family_reminder():
    gio = {"id": "a", "name": "Giỗ bà", "type": "gio", "calendar": "lunar", "day": 4, "month": 11,
           "year": None, "remind_days": 3, "icon": "mdi:candle", "note": ""}
    _, msg, has = _msg(date(2026, 12, 9), custom=[gio])
    assert msg.startswith("Hôm nay: Mùng 1 tháng 11\n")
    assert "Còn 3 ngày (T7 12/12 · 4/11 ÂL): Giỗ bà" in msg
    assert has is True


def test_years_label_by_event_type():
    be = {"id": "b", "name": "Bé Bin", "type": "sinh_nhat", "calendar": "solar", "day": 21, "month": 12,
          "year": 1994, "repeat": True, "remind_days": 1, "icon": "mdi:cake-variant", "note": ""}
    _, msg, _ = _msg(date(2026, 12, 20), custom=[be], holiday=0, monthly=0)
    assert "Ngày mai: Bé Bin (32 tuổi)" in msg
    _, msg, _ = _msg(date(2026, 12, 21), custom=[be], holiday=0, monthly=0)
    assert "Hôm nay: Bé Bin (32 tuổi)" in msg
    cuoi = dict(be, id="c", name="Ngày cưới", type="ky_niem", year=2027, day=10, month=1, remind_days=1)
    _, msg, _ = _msg(date(2027, 1, 9), custom=[cuoi], holiday=0, monthly=0)
    assert "Ngày mai: Ngày cưới\n" in msg  # năm đầu tiên: không ghi số
    _, msg, _ = _msg(date(2028, 1, 9), custom=[cuoi], holiday=0, monthly=0)
    assert "Ngày mai: Ngày cưới (1 năm)" in msg


def test_mobile_data_opens_panel():
    """Link trong tin app trùng đường dẫn trang sidebar."""
    assert mobile_data() == {"url": f"/{PANEL_URL}", "clickAction": f"/{PANEL_URL}"}
    assert mobile_data()["url"] == "/lich-viet"


def test_compact_for_lock_screen():
    """Gọn để màn hình khóa thấy đủ: tiêu đề 1 dòng, mỗi mốc 1 dòng, can chi để cuối."""
    title, msg, has = _msg(date(2026, 11, 20))
    assert title == "📅 LỊCH VIỆT › T6 20/11 · 12/10 ÂL"
    assert msg == "Hôm nay: Ngày Nhà giáo Việt Nam\nNgày Mậu Tuất · năm Bính Ngọ"
    assert has is True
    # rằm + ngày lễ hôm sau: vẫn chỉ 3 dòng nội dung
    _, msg, _ = _msg(date(2026, 11, 23))
    assert msg.splitlines() == [
        "Hôm nay: Rằm tháng 10 (Tết Hạ nguyên)",
        "Ngày mai: Ngày Văn hóa Việt Nam",
        "Ngày Tân Sửu · năm Bính Ngọ",
    ]


def test_same_day_reminders_on_one_line():
    a = {"id": "a", "name": "Giỗ bà", "type": "gio", "calendar": "lunar", "day": 4, "month": 11,
         "year": None, "remind_days": 3, "icon": "mdi:candle", "note": ""}
    b = dict(a, id="b", name="Sinh nhật Bin", type="sinh_nhat", calendar="solar", day=12, month=12)
    _, msg, _ = _msg(date(2026, 12, 9), custom=[a, b])
    assert "Còn 3 ngày (T7 12/12 · 4/11 ÂL): Giỗ bà, Sinh nhật Bin" in msg


def test_no_events_only_can_chi():
    title, msg, has = _msg(date(2026, 11, 17))
    assert title == "📅 LỊCH VIỆT › T3 17/11 · 9/10 ÂL"
    assert msg == "Ngày Ất Mùi · năm Bính Ngọ" and has is False


def test_title_fits_one_line():
    """Tiêu đề không quá 38 ký tự (màn hình khóa iPhone ~ 38 ký tự/dòng), kể cả tháng nhuận, Chủ nhật."""
    for d in (date(2025, 8, 7), date(2026, 11, 22), date(2026, 12, 31), date(2027, 2, 6)):
        title, _, _ = _msg(d)
        assert len(title) <= 38, title


def test_lunar_family_reminder_keeps_lunar_date():
    """Giỗ (âm lịch) ghi kèm ngày âm; sinh nhật dương lịch không ghi."""
    gio = {"id": "g", "name": "Giỗ ông nội", "type": "gio", "calendar": "lunar", "day": 15, "month": 11,
           "year": 2010, "remind_days": 1, "icon": "mdi:candle", "note": ""}
    _, msg, _ = _msg(date(2026, 12, 22), custom=[gio])
    assert "Ngày mai (15/11 ÂL): Rằm tháng 11, Giỗ ông nội (16 năm)" in msg
    _, msg, _ = _msg(date(2026, 12, 20), custom=[dict(gio, remind_days=3)], holiday=0, monthly=0)
    assert msg.splitlines()[0] == "Còn 3 ngày (T4 23/12 · 15/11 ÂL): Giỗ ông nội (16 năm)"
    # đúng ngày giỗ: ngày âm đã có ở tiêu đề
    title, msg, _ = _msg(date(2026, 12, 23), custom=[gio])
    assert title.endswith("15/11 ÂL") and msg.startswith("Hôm nay: Rằm tháng 11, Giỗ ông nội (16 năm)\n")
    # sinh nhật theo dương lịch không kèm ngày âm
    bin_ = {"id": "s", "name": "Sinh nhật Bin", "type": "sinh_nhat", "calendar": "solar", "day": 23,
            "month": 12, "year": None, "remind_days": 1, "icon": "mdi:cake-variant", "note": ""}
    _, msg, _ = _msg(date(2026, 12, 22), custom=[bin_], holiday=0, monthly=0)
    assert "Ngày mai: Sinh nhật Bin\n" in msg and "ÂL)" not in msg
    # rằm (ngày lễ hằng tháng) không kèm ngày âm khi không có giỗ cùng ngày
    _, msg, _ = _msg(date(2026, 12, 22))
    assert "Ngày mai: Rằm tháng 11" in msg
