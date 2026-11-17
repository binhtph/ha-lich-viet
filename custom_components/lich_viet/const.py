"""Hằng số cho Lịch Việt."""

from __future__ import annotations

DOMAIN = "lich_viet"
VERSION = "1.0.0"
NAME = "Lịch Việt"

PANEL_URL = "lich-viet"
PANEL_ELEMENT = "lich-viet-panel"
PANEL_ICON = "mdi:calendar-star"
STATIC_URL = "/lich_viet_static"

STORAGE_VERSION = 1
SAVE_DELAY = 5

# --- thông báo
CONF_TELEGRAM = "telegram_targets"
CONF_MOBILE = "mobile_targets"
CONF_REPORT_TIME = "report_time"
CONF_ONLY_WHEN_EVENTS = "only_when_events"
CONF_HOLIDAY_REMIND = "holiday_remind_days"
CONF_MONTHLY_REMIND = "monthly_remind_days"
DEFAULT_REPORT_TIME = "06:30:00"
DEFAULT_HOLIDAY_REMIND = 1
DEFAULT_MONTHLY_REMIND = 1

# --- ảnh nền
CONF_BG_ENABLED = "background_enabled"
CONF_BG_MODE = "background_mode"  # daily | random
CONF_BG_FOLDER = "background_folder"
CONF_UNSPLASH_KEY = "unsplash_key"
CONF_UNSPLASH_QUERY = "unsplash_query"
CONF_UNSPLASH_MIX = "unsplash_mix"
CONF_PANEL_OPACITY = "panel_opacity"
DEFAULT_BG_MODE = "daily"
DEFAULT_UNSPLASH_QUERY = "Vietnam landscape"
DEFAULT_PANEL_OPACITY = 80
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif")

SWITCH_MORNING = "morning_report"
