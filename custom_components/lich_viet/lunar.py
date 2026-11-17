"""Lịch âm Việt Nam: đổi ngày dương ↔ âm, can chi, tiết khí, giờ hoàng đạo.

Thuật toán thiên văn theo mô tả công khai của Hồ Ngọc Đức ("Âm lịch Việt Nam"),
tính theo múi giờ Hà Nội UTC+7. Dùng được cho các năm 1800–2199.
Module thuần Python, không phụ thuộc Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
import math

TIMEZONE = 7.0
MIN_YEAR = 1800
MAX_YEAR = 2199

CAN = ("Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý")
CHI = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
CON_GIAP = ("Chuột", "Trâu", "Hổ", "Mèo", "Rồng", "Rắn", "Ngựa", "Dê", "Khỉ", "Gà", "Chó", "Lợn")
WEEKDAYS = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật")

# 24 tiết khí, chỉ số i ứng với kinh độ mặt trời i*15° (0° = Xuân phân).
SOLAR_TERMS = (
    "Xuân phân", "Thanh minh", "Cốc vũ", "Lập hạ", "Tiểu mãn", "Mang chủng",
    "Hạ chí", "Tiểu thử", "Đại thử", "Lập thu", "Xử thử", "Bạch lộ",
    "Thu phân", "Hàn lộ", "Sương giáng", "Lập đông", "Tiểu tuyết", "Đại tuyết",
    "Đông chí", "Tiểu hàn", "Đại hàn", "Lập xuân", "Vũ thủy", "Kinh trập",
)
TERM_THANH_MINH = 1

# Giờ hoàng đạo theo chi của ngày (chỉ số chi % 6); vị trí = chi của giờ Tý..Hợi.
_GIO_HOANG_DAO = (
    "110100101100",
    "001101001011",
    "110011010010",
    "101100110100",
    "001011001101",
    "010010110011",
)

_SYNODIC = 29.530588853
_EPOCH = 2415021.076998695


@dataclass(frozen=True)
class LunarDate:
    """Một ngày âm lịch."""

    day: int
    month: int
    year: int
    leap: bool = False


# --------------------------------------------------------------- ngày Julius
def jd_from_date(d: date) -> int:
    """Số ngày Julius (lúc trưa) của một ngày dương lịch."""
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    jd = d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    if jd < 2299161:
        jd = d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083
    return jd


_JD_ORDINAL_OFFSET = jd_from_date(date(2000, 1, 1)) - date(2000, 1, 1).toordinal()


def date_from_jd(jd: int) -> date:
    """Ngày dương lịch (Gregory) từ số ngày Julius."""
    return date.fromordinal(jd - _JD_ORDINAL_OFFSET)


# ------------------------------------------------------------- thiên văn
def _new_moon(k: int) -> float:
    """Thời điểm sóc (trăng mới) thứ k tính từ 1/1/1900, theo giờ UTC (ngày Julius)."""
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    dr = math.pi / 180
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * t2 - 0.000000155 * t3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * t - 0.009173 * t2) * dr)
    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    mpr = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3
    c1 = (0.1734 - 0.000393 * t) * math.sin(m * dr) + 0.0021 * math.sin(2 * dr * m)
    c1 = c1 - 0.4068 * math.sin(mpr * dr) + 0.0161 * math.sin(dr * 2 * mpr)
    c1 = c1 - 0.0004 * math.sin(dr * 3 * mpr)
    c1 = c1 + 0.0104 * math.sin(dr * 2 * f) - 0.0051 * math.sin(dr * (m + mpr))
    c1 = c1 - 0.0074 * math.sin(dr * (m - mpr)) + 0.0004 * math.sin(dr * (2 * f + m))
    c1 = c1 - 0.0004 * math.sin(dr * (2 * f - m)) - 0.0006 * math.sin(dr * (2 * f + mpr))
    c1 = c1 + 0.0010 * math.sin(dr * (2 * f - mpr)) + 0.0005 * math.sin(dr * (2 * mpr + m))
    if t < -11:
        delta_t = 0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
    else:
        delta_t = -0.000278 + 0.000265 * t + 0.000262 * t2
    return jd1 + c1 - delta_t


def _sun_longitude(jdn: float) -> float:
    """Kinh độ mặt trời (radian, 0..2π) tại thời điểm jdn (ngày Julius, UTC)."""
    t = (jdn - 2451545.0) / 36525
    t2 = t * t
    dr = math.pi / 180
    m = 357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2
    l0 = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    dl = (1.914600 - 0.004817 * t - 0.000014 * t2) * math.sin(dr * m)
    dl += (0.019993 - 0.000101 * t) * math.sin(dr * 2 * m) + 0.000290 * math.sin(dr * 3 * m)
    lon = (l0 + dl) * dr
    lon -= math.pi * 2 * math.floor(lon / (math.pi * 2))
    return lon


@lru_cache(maxsize=8192)
def _new_moon_day(k: int) -> int:
    """Ngày Julius của ngày có sóc thứ k (theo giờ địa phương)."""
    return int(math.floor(_new_moon(k) + 0.5 + TIMEZONE / 24))


def _sun_longitude_major(day_jd: int) -> int:
    """Cung hoàng đạo (0..11, mỗi cung 30°) của mặt trời lúc nửa đêm đầu ngày."""
    return math.floor(_sun_longitude(day_jd - 0.5 - TIMEZONE / 24) / math.pi * 6)


@lru_cache(maxsize=1024)
def _lunar_month_11(year: int) -> int:
    """Ngày Julius bắt đầu tháng 11 âm lịch (tháng chứa Đông chí) của năm dương `year`."""
    off = jd_from_date(date(year, 12, 31)) - 2415021
    k = math.floor(off / _SYNODIC)
    nm = _new_moon_day(k)
    if _sun_longitude_major(nm) >= 9:
        nm = _new_moon_day(k - 1)
    return nm


@lru_cache(maxsize=1024)
def _leap_month_offset(a11: int) -> int:
    """Vị trí tháng nhuận (tính từ tháng 11) trong năm có 13 tháng."""
    k = math.floor((a11 - _EPOCH) / _SYNODIC + 0.5)
    i = 1
    arc = _sun_longitude_major(_new_moon_day(k + i))
    while True:
        last = arc
        i += 1
        arc = _sun_longitude_major(_new_moon_day(k + i))
        if arc == last or i >= 14:
            break
    return i - 1


def _check_year(year: int) -> None:
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError(f"Năm {year} nằm ngoài phạm vi {MIN_YEAR}–{MAX_YEAR}")


# --------------------------------------------------------------- chuyển đổi
@lru_cache(maxsize=16384)
def _solar_to_lunar_jd(day_jd: int, year: int) -> LunarDate:
    # Sóc gần nhất không sau ngày đang xét. Ước lượng k theo chu kỳ trung bình
    # có thể lệch 1 (vd. 7/5/2054), nên dò lại cho chắc.
    k = math.floor((day_jd - _EPOCH) / _SYNODIC) + 1
    while _new_moon_day(k) > day_jd:
        k -= 1
    while _new_moon_day(k + 1) <= day_jd:
        k += 1
    month_start = _new_moon_day(k)
    a11 = _lunar_month_11(year)
    b11 = a11
    if a11 >= month_start:
        lunar_year = year
        a11 = _lunar_month_11(year - 1)
    else:
        lunar_year = year + 1
        b11 = _lunar_month_11(year + 1)
    lunar_day = day_jd - month_start + 1
    diff = (month_start - a11) // 29
    leap = False
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_offset = _leap_month_offset(a11)
        if diff >= leap_offset:
            lunar_month = diff + 10
            if diff == leap_offset:
                leap = True
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return LunarDate(lunar_day, lunar_month, lunar_year, leap)


def solar_to_lunar(d: date) -> LunarDate:
    """Đổi ngày dương lịch sang âm lịch."""
    _check_year(d.year)
    return _solar_to_lunar_jd(jd_from_date(d), d.year)


def lunar_to_solar(day: int, month: int, year: int, leap: bool = False) -> date | None:
    """Đổi ngày âm lịch sang dương lịch. Trả về None nếu ngày không tồn tại."""
    _check_year(year)
    if not 1 <= month <= 12 or not 1 <= day <= 30:
        return None
    if month < 11:
        a11 = _lunar_month_11(year - 1)
        b11 = _lunar_month_11(year)
    else:
        a11 = _lunar_month_11(year)
        b11 = _lunar_month_11(year + 1)
    k = math.floor(0.5 + (a11 - _EPOCH) / _SYNODIC)
    off = month - 11
    if off < 0:
        off += 12
    if b11 - a11 > 365:
        leap_offset = _leap_month_offset(a11)
        leap_month = leap_offset - 2
        if leap_month < 0:
            leap_month += 12
        if leap and month != leap_month:
            return None
        if leap or off >= leap_offset:
            off += 1
    elif leap:
        return None
    month_start = _new_moon_day(k + off)
    if day > 29 and _new_moon_day(k + off + 1) - month_start < 30:
        return None
    return date_from_jd(month_start + day - 1)


def leap_month_of_year(year: int) -> int | None:
    """Tháng nhuận của năm âm lịch `year` (None nếu không nhuận)."""
    for month in range(1, 13):
        if lunar_to_solar(1, month, year, True) is not None:
            return month
    return None


def month_length(d: date) -> int:
    """Số ngày (29 hoặc 30) của tháng âm lịch chứa ngày dương `d`."""
    lunar = solar_to_lunar(d)
    start = d - timedelta(days=lunar.day - 1)
    return 30 if solar_to_lunar(start + timedelta(days=29)).day == 30 else 29


# --------------------------------------------------------------- can chi
def can_chi_day(d: date) -> str:
    jd = jd_from_date(d)
    return f"{CAN[(jd + 9) % 10]} {CHI[(jd + 1) % 12]}"


def can_chi_month(month: int, year: int) -> str:
    return f"{CAN[(year * 12 + month + 3) % 10]} {CHI[(month + 1) % 12]}"


def can_chi_year(year: int) -> str:
    return f"{CAN[(year + 6) % 10]} {CHI[(year + 8) % 12]}"


def con_giap(year: int) -> str:
    return CON_GIAP[(year + 8) % 12]


def gio_hoang_dao(d: date) -> list[dict[str, str]]:
    """Các giờ hoàng đạo của ngày, mỗi giờ gồm tên chi và khung giờ."""
    chi_index = (jd_from_date(d) + 1) % 12
    pattern = _GIO_HOANG_DAO[chi_index % 6]
    result = []
    for i, flag in enumerate(pattern):
        if flag == "1":
            start = (i * 2 + 23) % 24
            result.append({"chi": CHI[i], "gio": f"{start}-{(start + 2) % 24}"})
    return result


# --------------------------------------------------------------- tiết khí
def _term_index_at(day_jd: float) -> int:
    return math.floor(_sun_longitude(day_jd - 0.5 - TIMEZONE / 24) / (math.pi / 12))


def solar_term(d: date) -> int:
    """Tiết khí đang có hiệu lực vào cuối ngày `d` (chỉ số 0..23)."""
    return _term_index_at(jd_from_date(d) + 1)


def solar_term_starts(d: date) -> int | None:
    """Chỉ số tiết khí bắt đầu trong ngày `d`, hoặc None."""
    jd = jd_from_date(d)
    start, end = _term_index_at(jd), _term_index_at(jd + 1)
    return end if start != end else None


def next_solar_term(d: date) -> tuple[int, date]:
    """Tiết khí kế tiếp sau ngày `d` và ngày bắt đầu."""
    current = solar_term(d)
    day = d
    for _ in range(40):
        day += timedelta(days=1)
        idx = solar_term(day)
        if idx != current:
            return idx, day
    raise RuntimeError("Không tìm thấy tiết khí kế tiếp")


# --------------------------------------------------------------- hiển thị
def lunar_month_name(month: int, leap: bool = False) -> str:
    name = {1: "Giêng", 12: "Chạp"}.get(month, str(month))
    return f"{name} nhuận" if leap else name


def lunar_day_name(day: int) -> str:
    return f"Mùng {day}" if day <= 10 else str(day)


def lunar_text(lunar: LunarDate) -> str:
    """Ví dụ: 'Mùng 9 tháng 10 năm Bính Ngọ'."""
    return (
        f"{lunar_day_name(lunar.day)} tháng {lunar_month_name(lunar.month, lunar.leap)} "
        f"năm {can_chi_year(lunar.year)}"
    )


def next_tet(d: date) -> date:
    """Ngày Tết Nguyên Đán gần nhất từ ngày `d` (tính cả hôm nay)."""
    year = solar_to_lunar(d).year
    tet = lunar_to_solar(1, 1, year)
    if tet is None or tet < d:
        tet = lunar_to_solar(1, 1, year + 1)
    assert tet is not None
    return tet
