"""Lịch Việt: lịch âm, ngày lễ Việt Nam, sự kiện gia đình và trang lịch trên sidebar."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from . import websocket_api
from .background import BackgroundManager, BackgroundView
from .const import DOMAIN, NAME, PANEL_ELEMENT, PANEL_ICON, PANEL_URL, STATIC_URL, VERSION
from .notifier import LichVietNotifier
from .runtime import LichVietRuntime

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SWITCH, Platform.BUTTON]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_SETUP_KEY = f"{DOMAIN}_http"

type LichVietConfigEntry = ConfigEntry[LichVietRuntime]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Đăng ký API websocket (một lần)."""
    websocket_api.async_register(hass)
    return True


async def _async_register_http(hass: HomeAssistant) -> None:
    if hass.data.get(_SETUP_KEY):
        return
    await hass.http.async_register_static_paths([
        StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "frontend"), cache_headers=False)
    ])
    hass.http.register_view(BackgroundView())
    hass.data[_SETUP_KEY] = True


async def async_setup_entry(hass: HomeAssistant, entry: LichVietConfigEntry) -> bool:
    runtime = LichVietRuntime(hass, entry)
    await runtime.async_load()
    runtime.background = BackgroundManager(hass, runtime)
    await runtime.background.async_setup()
    runtime.notifier = LichVietNotifier(hass, runtime)
    runtime.notifier.async_setup()
    entry.runtime_data = runtime
    hass.data[DOMAIN] = runtime

    await _async_register_http(hass)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name=PANEL_ELEMENT,
        sidebar_title=NAME,
        sidebar_icon=PANEL_ICON,
        module_url=f"{STATIC_URL}/lich-viet-panel.js?v={VERSION}",
        require_admin=False,
        config={"version": VERSION},
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: LichVietConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LichVietConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        frontend.async_remove_panel(hass, PANEL_URL, warn_if_unknown=False)
        runtime = entry.runtime_data
        runtime.notifier.async_unload()
        runtime.async_unload()
        await runtime.async_flush()
        hass.data.pop(DOMAIN, None)
    return unloaded
