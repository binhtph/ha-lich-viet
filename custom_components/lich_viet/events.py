"""Ngày lễ Việt Nam, mùng 1/rằm, sự kiện gia đình và thông tin từng ngày.

Module thuần Python (không phụ thuộc Home Assistant) để dễ kiểm thử.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from .lunar import (
    SOLAR_TERMS,
    TERM_THANH_MINH,
    WEEKDAYS,
    LunarDate,
    can_chi_day,
    can_chi_month,
    can_chi_year,
    con_giap,
    gio_hoang_dao,
    lunar_day_name,
    lunar_month_name,
    lunar_text,
    month_length,
    next_solar_term,
    next_tet,
    solar_term,
    solar_term_starts,
    solar_to_lunar,
)

# Nhóm sự kiện -> dùng cho màu sắc trên giao diện.
CAT_NATIONAL = "national"  # lễ quốc gia (đỏ)
CAT_LUNAR = "lunar"  # lễ truyền thống âm lịch (vàng cam)
CAT_MONTHLY = "monthly"  # mùng 1, rằm (vàng cam nhạt)
CAT_SOCIAL = "social"  # ngày kỷ niệm xã hội (tím)
CAT_INTERNATIONAL = "international"  # lễ quốc tế (xanh lá)
CAT_FAMILY = "family"  # sự kiện gia đình (xanh ngọc)
CATEGORIES = (CAT_NATIONAL, CAT_LUNAR, CAT_MONTHLY, CAT_SOCIAL, CAT_INTERNATIONAL, CAT_FAMILY)

# Loại sự kiện gia đình -> icon mặc định.
FAMILY_TYPES = {
    "sinh_nhat": "mdi:cake-variant",
    "gio": "mdi:candle",
    "ky_niem": "mdi:heart-multiple",
    "khac": "mdi:star",
}


@dataclass(frozen=True)
class Holiday:
    """Một ngày lễ dựng sẵn."""

    id: str
    name: str
    calendar: str  # "solar" | "lunar"
    day: int
    month: int
    category: str
    icon: str
    off: bool = False  # ngày nghỉ lễ chính thức


HOLIDAYS: tuple[Holiday, ...] = (
    # --- dương lịch
    Holiday("tet_duong_lich", "Tết Dương lịch", "solar", 1, 1, CAT_NATIONAL, "mdi:party-popper", True),
    Holiday("thanh_lap_dang", "Ngày thành lập Đảng Cộng sản Việt Nam", "solar", 3, 2, CAT_NATIONAL, "mdi:flag"),
    Holiday("valentine", "Lễ Tình nhân", "solar", 14, 2, CAT_INTERNATIONAL, "mdi:heart"),
    Holiday("quoc_te_phu_nu", "Ngày Quốc tế Phụ nữ", "solar", 8, 3, CAT_SOCIAL, "mdi:flower"),
    Holiday("giai_phong", "Ngày Giải phóng miền Nam", "solar", 30, 4, CAT_NATIONAL, "mdi:flag", True),
    Holiday("quoc_te_lao_dong", "Ngày Quốc tế Lao động", "solar", 1, 5, CAT_NATIONAL, "mdi:hammer-wrench", True),
    Holiday("sinh_nhat_bac", "Ngày sinh Chủ tịch Hồ Chí Minh", "solar", 19, 5, CAT_NATIONAL, "mdi:star"),
    Holiday("thieu_nhi", "Ngày Quốc tế Thiếu nhi", "solar", 1, 6, CAT_SOCIAL, "mdi:balloon"),
    Holiday("gia_dinh", "Ngày Gia đình Việt Nam", "solar", 28, 6, CAT_SOCIAL, "mdi:home-heart"),
    Holiday("thuong_binh_liet_si", "Ngày Thương binh Liệt sĩ", "solar", 27, 7, CAT_NATIONAL, "mdi:candelabra"),
    Holiday("quoc_khanh", "Quốc khánh", "solar", 2, 9, CAT_NATIONAL, "mdi:flag-variant", True),
    Holiday("phu_nu_viet_nam", "Ngày Phụ nữ Việt Nam", "solar", 20, 10, CAT_SOCIAL, "mdi:flower-tulip"),
    Holiday("nha_giao", "Ngày Nhà giáo Việt Nam", "solar", 20, 11, CAT_SOCIAL, "mdi:school"),
    Holiday("quan_doi", "Ngày thành lập Quân đội Nhân dân Việt Nam", "solar", 22, 12, CAT_NATIONAL, "mdi:shield-star"),
    Holiday("dem_giang_sinh", "Đêm Giáng sinh", "solar", 24, 12, CAT_INTERNATIONAL, "mdi:pine-tree"),
    Holiday("giang_sinh", "Lễ Giáng sinh", "solar", 25, 12, CAT_INTERNATIONAL, "mdi:pine-tree"),
    # --- âm lịch
    Holiday("tet_nguyen_dan", "Tết Nguyên Đán", "lunar", 1, 1, CAT_LUNAR, "mdi:firework", True),
    Holiday("mung_2_tet", "Mùng 2 Tết", "lunar", 2, 1, CAT_LUNAR, "mdi:firework", True),
    Holiday("mung_3_tet", "Mùng 3 Tết", "lunar", 3, 1, CAT_LUNAR, "mdi:firework", True),
    Holiday("ram_thang_gieng", "Rằm tháng Giêng (Tết Nguyên tiêu)", "lunar", 15, 1, CAT_LUNAR, "mdi:moon-full"),
    Holiday("han_thuc", "Tết Hàn thực", "lunar", 3, 3, CAT_LUNAR, "mdi:bowl-mix"),
    Holiday("gio_to", "Giỗ Tổ Hùng Vương", "lunar", 10, 3, CAT_NATIONAL, "mdi:pillar", True),
    Holiday("phat_dan", "Lễ Phật Đản", "lunar", 15, 4, CAT_LUNAR, "mdi:temple-buddhist"),
    Holiday("doan_ngo", "Tết Đoan Ngọ", "lunar", 5, 5, CAT_LUNAR, "mdi:weather-sunny"),
    Holiday("vu_lan", "Lễ Vu Lan", "lunar", 15, 7, CAT_LUNAR, "mdi:flower-poppy"),
    Holiday("trung_thu", "Tết Trung thu", "lunar", 15, 8, CAT_LUNAR, "mdi:cookie"),
    Holiday("ha_nguyen", "Rằm tháng 10 (Tết Hạ nguyên)", "lunar", 15, 10, CAT_LUNAR, "mdi:rice"),
    Holiday("ong_tao", "Ông Công Ông Táo", "lunar", 23, 12, CAT_LUNAR, "mdi:fish"),
)
HOLIDAY_BY_ID = {h.id: h for h in HOLIDAYS}

# Ngày lễ tính theo cách riêng (không cố định ngày/tháng).
GIAO_THUA = Holiday("giao_thua", "Giao thừa", "lunar", 0, 12, CAT_LUNAR, "mdi:firework", True)
THANH_MINH = Holiday("thanh_minh", "Tết Thanh minh", "solar", 0, 4, CAT_LUNAR, "mdi:leaf")

# Tên ngắn hiển thị trong ô lịch (ô nhỏ, cần gọn).
SHORT_NAMES: dict[str, str] = {
    "tet_duong_lich": "Tết Dương lịch",
    "thanh_lap_dang": "Thành lập Đảng",
    "valentine": "Valentine",
    "quoc_te_phu_nu": "Quốc tế Phụ nữ",
    "giai_phong": "Giải phóng MN",
    "quoc_te_lao_dong": "Quốc tế Lao động",
    "sinh_nhat_bac": "Sinh nhật Bác",
    "thieu_nhi": "Thiếu nhi",
    "gia_dinh": "Gia đình VN",
    "thuong_binh_liet_si": "Thương binh Liệt sĩ",
    "quoc_khanh": "Quốc khánh",
    "phu_nu_viet_nam": "Phụ nữ VN",
    "nha_giao": "Nhà giáo VN",
    "quan_doi": "Quân đội ND",
    "dem_giang_sinh": "Đêm Noel",
    "giang_sinh": "Giáng sinh",
    "tet_nguyen_dan": "Mùng 1 Tết",
    "mung_2_tet": "Mùng 2 Tết",
    "mung_3_tet": "Mùng 3 Tết",
    "ram_thang_gieng": "Rằm tháng Giêng",
    "han_thuc": "Hàn thực",
    "gio_to": "Giỗ Tổ",
    "phat_dan": "Phật Đản",
    "doan_ngo": "Đoan Ngọ",
    "vu_lan": "Vu Lan",
    "trung_thu": "Trung thu",
    "ha_nguyen": "Hạ nguyên",
    "ong_tao": "Ông Táo",
    "giao_thua": "Giao thừa",
    "thanh_minh": "Thanh minh",
    "mung_1": "Mùng 1",
    "ram": "Rằm",
}

# Thư mục ảnh nền theo dịp: (thư mục, id ngày lễ mốc, số ngày trước, số ngày sau).
BACKGROUND_OCCASIONS: tuple[tuple[str, str, int, int], ...] = (
    ("tet", "tet_nguyen_dan", 7, 7),
    ("trung_thu", "trung_thu", 5, 0),
    ("quoc_khanh", "quoc_khanh", 1, 1),
    ("giai_phong", "giai_phong", 1, 1),
    ("giang_sinh", "giang_sinh", 5, 1),
    ("vu_lan", "vu_lan", 1, 0),
)
BACKGROUND_FOLDERS = ("chung",) + tuple(o[0] for o in BACKGROUND_OCCASIONS)

_SOLAR_INDEX: dict[tuple[int, int], list[Holiday]] = {}
_LUNAR_INDEX: dict[tuple[int, int], list[Holiday]] = {}
for _h in HOLIDAYS:
    target = _SOLAR_INDEX if _h.calendar == "solar" else _LUNAR_INDEX
    target.setdefault((_h.day, _h.month), []).append(_h)


@dataclass
class Occurrence:
    """Một sự kiện xảy ra vào một ngày dương lịch cụ thể."""

    id: str
    name: str
    date: date
    category: str
    icon: str
    off: bool = False
    source: str = "builtin"  # builtin | custom
    event_id: str | None = None
    years: int | None = None  # số năm (giỗ lần thứ, tuổi, kỷ niệm)
    note: str = ""
    remind_days: int = 0
    event_type: str | None = None  # loại sự kiện gia đình (sinh_nhat, gio, ky_niem, khac)
    lunar: LunarDate | None = field(default=None, repr=False)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["date"] = self.date.isoformat()
        data["short"] = SHORT_NAMES.get(self.id, self.name) if self.source == "builtin" else self.name
        data.pop("lunar")
        if self.lunar is not None:
            data["lunar"] = f"{self.lunar.day}/{self.lunar.month}" + (" nhuận" if self.lunar.leap else "")
        else:
            data["lunar"] = None
        return data


# --------------------------------------------------------------- sự kiện gia đình
def normalize_custom_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Kiểm tra và chuẩn hóa một sự kiện gia đình. Ném ValueError nếu sai."""
    name = str(raw.get("name", "")).strip()
    if not name:
        raise ValueError("name_required")
    calendar = raw.get("calendar", "solar")
    if calendar not in ("lunar", "solar"):
        raise ValueError("calendar_invalid")
    try:
        day = int(raw["day"])
        month = int(raw["month"])
    except (KeyError, TypeError, ValueError) as err:
        raise ValueError("date_invalid") from err
    max_day = 30 if calendar == "lunar" else (29 if month == 2 else 30 if month in (4, 6, 9, 11) else 31)
    if not 1 <= month <= 12 or not 1 <= day <= max_day:
        raise ValueError("date_invalid")
    year = raw.get("year")
    year = int(year) if year not in (None, "", 0, "0") else None
    if year is not None and not 1800 <= year <= 2199:
        raise ValueError("year_invalid")
    etype = raw.get("type", "khac")
    if etype not in FAMILY_TYPES:
        raise ValueError("type_invalid")
    repeat = raw.get("repeat", True)
    repeat = repeat not in (False, "false", "False", 0, "0", "once")
    if not repeat and year is None:
        raise ValueError("year_required")
    remind = int(raw.get("remind_days") or 0)
    if not 0 <= remind <= 60:
        raise ValueError("remind_invalid")
    return {
        "id": str(raw.get("id") or ""),
        "name": name[:80],
        "type": etype,
        "calendar": calendar,
        "day": day,
        "month": month,
        "year": year,
        "repeat": repeat,
        "remind_days": remind,
        "icon": str(raw.get("icon") or FAMILY_TYPES[etype]),
        "note": str(raw.get("note") or "")[:200],
    }


def _custom_ref_year(ev: dict[str, Any], d: date, lunar: LunarDate) -> int:
    """Năm dùng để so với năm của sự kiện: năm âm cho sự kiện âm lịch, năm dương cho dương lịch."""
    return lunar.year if ev["calendar"] == "lunar" else d.year


def _custom_matches(ev: dict[str, Any], d: date, lunar: LunarDate, mlen: int) -> bool:
    if ev.get("year"):
        ref_year = _custom_ref_year(ev, d, lunar)
        if ref_year < ev["year"]:
            return False  # chưa tới năm bắt đầu (vd. ngày cưới năm sau)
        if not ev.get("repeat", True) and ref_year != ev["year"]:
            return False  # sự kiện chỉ một lần
    if ev["calendar"] == "solar":
        if ev["month"] == 2 and ev["day"] == 29:
            leap_year = d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0)
            return d.month == 2 and (d.day == 29 or (not leap_year and d.day == 28))
        return d.day == ev["day"] and d.month == ev["month"]
    if lunar.leap or lunar.month != ev["month"]:
        return False
    if lunar.day == ev["day"]:
        return True
    # Ngày 30 âm nhưng tháng thiếu (29 ngày): tính vào ngày 29.
    return ev["day"] == 30 and lunar.day == 29 and mlen == 29


def _custom_years(ev: dict[str, Any], d: date, lunar: LunarDate) -> int | None:
    """Số năm tính từ năm đã nhập (sinh nhật: tuổi; giỗ, kỷ niệm: năm thứ N).

    Đúng năm bắt đầu (ngày sinh, ngày cưới) và sự kiện chỉ một lần thì không ghi số.
    """
    if not ev.get("year") or not ev.get("repeat", True):
        return None
    years = _custom_ref_year(ev, d, lunar) - ev["year"]
    return years if years > 0 else None


# --------------------------------------------------------------- tìm sự kiện
def events_on(d: date, custom: Iterable[dict[str, Any]] = (), *, monthly: bool = True) -> list[Occurrence]:
    """Mọi sự kiện của một ngày."""
    lunar = solar_to_lunar(d)
    result: list[Occurrence] = []

    def add(h: Holiday, **extra: Any) -> None:
        result.append(Occurrence(h.id, h.name, d, h.category, h.icon, h.off, lunar=lunar, **extra))

    for h in _SOLAR_INDEX.get((d.day, d.month), ()):
        add(h)
    named_lunar = []
    if not lunar.leap:
        named_lunar = _LUNAR_INDEX.get((lunar.day, lunar.month), [])
        for h in named_lunar:
            add(h)
    if solar_to_lunar(d + timedelta(days=1)) == LunarDate(1, 1, lunar.year + 1):
        add(GIAO_THUA)
    if solar_term_starts(d) == TERM_THANH_MINH:
        add(THANH_MINH)
    if monthly and not named_lunar and lunar.day in (1, 15):
        month = lunar_month_name(lunar.month, lunar.leap)
        if lunar.day == 1:
            result.append(Occurrence("mung_1", f"Mùng 1 tháng {month}", d, CAT_MONTHLY, "mdi:moon-new", lunar=lunar))
        else:
            result.append(Occurrence("ram", f"Rằm tháng {month}", d, CAT_MONTHLY, "mdi:moon-full", lunar=lunar))

    custom = list(custom)
    if custom:
        mlen = month_length(d) if lunar.day >= 29 else 30
        for ev in custom:
            if _custom_matches(ev, d, lunar, mlen):
                result.append(
                    Occurrence(
                        id=f"custom_{ev['id']}",
                        name=ev["name"],
                        date=d,
                        category=CAT_FAMILY,
                        icon=ev.get("icon") or FAMILY_TYPES.get(ev.get("type", "khac"), "mdi:star"),
                        source="custom",
                        event_id=ev["id"],
                        years=_custom_years(ev, d, lunar),
                        note=ev.get("note", ""),
                        remind_days=int(ev.get("remind_days") or 0),
                        event_type=ev.get("type", "khac"),
                        lunar=lunar,
                    )
                )
    return result


def events_between(
    start: date, end: date, custom: Iterable[dict[str, Any]] = (), *, monthly: bool = True
) -> list[Occurrence]:
    """Mọi sự kiện từ `start` đến `end` (tính cả hai đầu)."""
    custom = list(custom)
    result: list[Occurrence] = []
    d = start
    while d <= end:
        result.extend(events_on(d, custom, monthly=monthly))
        d += timedelta(days=1)
    return result


def find_holiday(holiday_id: str, year: int) -> date | None:
    """Ngày dương lịch của một ngày lễ dựng sẵn trong năm dương `year`."""
    for occ in events_between(date(year, 1, 1), date(year, 12, 31), monthly=False):
        if occ.id == holiday_id:
            return occ.date
    return None


# --------------------------------------------------------------- thông tin ngày
def day_info(d: date, custom: Iterable[dict[str, Any]] = (), *, today: date | None = None) -> dict[str, Any]:
    """Đầy đủ thông tin một ngày (dùng cho giao diện và sensor)."""
    lunar = solar_to_lunar(d)
    term = solar_term(d)
    next_term, next_term_day = next_solar_term(d)
    events = events_on(d, custom)
    return {
        "date": d.isoformat(),
        "day": d.day,
        "month": d.month,
        "year": d.year,
        "weekday": d.weekday(),
        "weekday_name": WEEKDAYS[d.weekday()],
        "lunar_day": lunar.day,
        "lunar_month": lunar.month,
        "lunar_year": lunar.year,
        "lunar_leap": lunar.leap,
        "lunar_month_length": month_length(d),
        "lunar_text": lunar_text(lunar),
        "lunar_short": f"{lunar.day}/{lunar.month}" + ("N" if lunar.leap else ""),
        "lunar_day_name": lunar_day_name(lunar.day),
        "lunar_month_name": lunar_month_name(lunar.month, lunar.leap),
        "can_chi_day": can_chi_day(d),
        "can_chi_month": can_chi_month(lunar.month, lunar.year),
        "can_chi_year": can_chi_year(lunar.year),
        "con_giap": con_giap(lunar.year),
        "solar_term": SOLAR_TERMS[term],
        "solar_term_starts": solar_term_starts(d) is not None,
        "next_solar_term": SOLAR_TERMS[next_term],
        "next_solar_term_date": next_term_day.isoformat(),
        "gio_hoang_dao": gio_hoang_dao(d),
        "is_today": today is not None and d == today,
        "is_off": any(e.off for e in events),
        "events": [e.as_dict() for e in events],
    }


def month_grid(year: int, month: int, custom: Iterable[dict[str, Any]] = (), *, today: date | None = None) -> list[dict[str, Any]]:
    """42 ngày (6 tuần, bắt đầu thứ Hai) phủ kín tháng `month/year`."""
    custom = list(custom)
    first = date(year, month, 1)
    start = first - timedelta(days=first.weekday())
    days = []
    for i in range(42):
        d = start + timedelta(days=i)
        lunar = solar_to_lunar(d)
        events = events_on(d, custom)
        days.append({
            "date": d.isoformat(),
            "day": d.day,
            "in_month": d.month == month,
            "weekday": d.weekday(),
            "is_today": today is not None and d == today,
            "lunar_day": lunar.day,
            "lunar_month": lunar.month,
            "lunar_leap": lunar.leap,
            "is_off": any(e.off for e in events),
            "events": [e.as_dict() for e in events],
        })
    return days


def upcoming(today: date, days: int, custom: Iterable[dict[str, Any]] = (), *, monthly: bool = False) -> list[dict[str, Any]]:
    """Sự kiện trong `days` ngày tới (không tính hôm nay), có số ngày còn lại."""
    result = []
    for occ in events_between(today + timedelta(days=1), today + timedelta(days=days), custom, monthly=monthly):
        item = occ.as_dict()
        item["days_left"] = (occ.date - today).days
        item["weekday_name"] = WEEKDAYS[occ.date.weekday()]
        result.append(item)
    return result


def next_event(today: date, custom: Iterable[dict[str, Any]] = (), *, horizon: int = 400) -> dict[str, Any] | None:
    """Sự kiện gần nhất từ hôm nay trở đi (không tính mùng 1/rằm)."""
    custom = list(custom)
    d = today
    for _ in range(horizon):
        occs = events_on(d, custom, monthly=False)
        if occs:
            item = occs[0].as_dict()
            item["days_left"] = (d - today).days
            item["all"] = [o.name for o in occs]
            return item
        d += timedelta(days=1)
    return None


def tet_info(today: date) -> dict[str, Any]:
    tet = next_tet(today)
    lunar_year = solar_to_lunar(tet).year
    return {
        "date": tet.isoformat(),
        "days_left": (tet - today).days,
        "year_name": can_chi_year(lunar_year),
        "con_giap": con_giap(lunar_year),
    }


def background_folders_for(d: date) -> list[str]:
    """Các thư mục ảnh theo dịp đang hiệu lực vào ngày `d` (ưu tiên trước)."""
    result = []
    window = max(before for _, _, before, _ in BACKGROUND_OCCASIONS) + 1
    nearby = events_between(d - timedelta(days=window), d + timedelta(days=window), monthly=False)
    for folder, holiday_id, before, after in BACKGROUND_OCCASIONS:
        for occ in nearby:
            if occ.id == holiday_id and -before <= (d - occ.date).days <= after:
                result.append(folder)
                break
    return result
