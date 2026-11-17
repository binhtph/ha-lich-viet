"""Tạo lại tests/js/fixtures.json từ backend (dữ liệu giống websocket trả về).

Chạy từ thư mục gốc repo:  python tests/js/make_fixtures.py
"""

from __future__ import annotations

from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "custom_components" / "lich_viet"

# Nạp lunar.py và events.py như một package nhỏ, không cần Home Assistant.
pkg = types.ModuleType("lv")
pkg.__path__ = [str(PKG)]
sys.modules["lv"] = pkg
for name in ("lunar", "events"):
    spec = importlib.util.spec_from_file_location(f"lv.{name}", PKG / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"lv.{name}"] = mod
    spec.loader.exec_module(mod)
ev = sys.modules["lv.events"]

TODAY = date(2026, 11, 17)
CUSTOM = [{"id": "e1", "name": "Giỗ ông nội", "type": "gio", "calendar": "lunar", "day": 15, "month": 11,
           "year": 2010, "repeat": True, "remind_days": 3, "icon": "mdi:candle", "note": ""}]


def build() -> dict:
    return {
        "overview": {
            "today": ev.day_info(TODAY, CUSTOM, today=TODAY),
            "tet": ev.tet_info(TODAY),
            "upcoming": ev.upcoming(TODAY, 45, CUSTOM),
            "config": {"background": True, "opacity": 80, "event_types": list(ev.FAMILY_TYPES), "is_admin": True},
        },
        "month_11": {"year": 2026, "month": 11, "days": ev.month_grid(2026, 11, CUSTOM, today=TODAY)},
        "month_12": {"year": 2026, "month": 12, "days": ev.month_grid(2026, 12, CUSTOM, today=TODAY)},
        "day_20": ev.day_info(date(2026, 11, 20), CUSTOM, today=TODAY),
        "events": CUSTOM,
    }


if __name__ == "__main__":
    out = Path(__file__).with_name("fixtures.json")
    out.write_text(json.dumps(build(), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Đã ghi {out}")
