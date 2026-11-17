"""Config flow (một lần, không cần nhập gì) và options flow dạng menu."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
)

from .const import (
    CONF_BG_ENABLED,
    CONF_BG_FOLDER,
    CONF_BG_MODE,
    CONF_HOLIDAY_REMIND,
    CONF_MOBILE,
    CONF_MONTHLY_REMIND,
    CONF_ONLY_WHEN_EVENTS,
    CONF_PANEL_OPACITY,
    CONF_REPORT_TIME,
    CONF_TELEGRAM,
    CONF_UNSPLASH_KEY,
    CONF_UNSPLASH_MIX,
    CONF_UNSPLASH_QUERY,
    DEFAULT_BG_MODE,
    DEFAULT_HOLIDAY_REMIND,
    DEFAULT_MONTHLY_REMIND,
    DEFAULT_PANEL_OPACITY,
    DEFAULT_REPORT_TIME,
    DEFAULT_UNSPLASH_QUERY,
    DOMAIN,
    NAME,
)

DEFAULT_OPTIONS: dict[str, Any] = {
    CONF_TELEGRAM: [],
    CONF_MOBILE: [],
    CONF_REPORT_TIME: DEFAULT_REPORT_TIME,
    CONF_ONLY_WHEN_EVENTS: True,
    CONF_HOLIDAY_REMIND: DEFAULT_HOLIDAY_REMIND,
    CONF_MONTHLY_REMIND: DEFAULT_MONTHLY_REMIND,
    CONF_BG_ENABLED: True,
    CONF_BG_MODE: DEFAULT_BG_MODE,
    CONF_BG_FOLDER: "",
    CONF_UNSPLASH_KEY: "",
    CONF_UNSPLASH_QUERY: DEFAULT_UNSPLASH_QUERY,
    CONF_UNSPLASH_MIX: False,
    CONF_PANEL_OPACITY: DEFAULT_PANEL_OPACITY,
}


def _box(**kw: Any) -> NumberSelector:
    return NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, **kw))


def _notify_schema(hass: HomeAssistant, v: dict[str, Any]) -> vol.Schema:
    mobile = {s for s in hass.services.async_services_for_domain("notify") if s.startswith("mobile_app_")}
    mobile |= set(v.get(CONF_MOBILE, []))
    return vol.Schema({
        vol.Optional(CONF_TELEGRAM, default=v.get(CONF_TELEGRAM, [])): EntitySelector(
            EntitySelectorConfig(domain="notify", multiple=True)),
        vol.Optional(CONF_MOBILE, default=v.get(CONF_MOBILE, [])): SelectSelector(
            SelectSelectorConfig(options=sorted(mobile), multiple=True, custom_value=True)),
        vol.Required(CONF_REPORT_TIME, default=v.get(CONF_REPORT_TIME, DEFAULT_REPORT_TIME)): TimeSelector(),
        vol.Required(CONF_ONLY_WHEN_EVENTS, default=v.get(CONF_ONLY_WHEN_EVENTS, True)): BooleanSelector(),
        vol.Required(CONF_HOLIDAY_REMIND, default=v.get(CONF_HOLIDAY_REMIND, DEFAULT_HOLIDAY_REMIND)): _box(
            min=0, max=30, step=1, unit_of_measurement="ngày"),
        vol.Required(CONF_MONTHLY_REMIND, default=v.get(CONF_MONTHLY_REMIND, DEFAULT_MONTHLY_REMIND)): _box(
            min=0, max=7, step=1, unit_of_measurement="ngày"),
    })


def _background_schema(v: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_BG_ENABLED, default=v.get(CONF_BG_ENABLED, True)): BooleanSelector(),
        vol.Required(CONF_BG_MODE, default=v.get(CONF_BG_MODE, DEFAULT_BG_MODE)): SelectSelector(
            SelectSelectorConfig(options=["daily", "random"], translation_key="background_mode")),
        vol.Optional(CONF_BG_FOLDER, description={"suggested_value": v.get(CONF_BG_FOLDER, "")}): TextSelector(),
        vol.Optional(CONF_UNSPLASH_KEY, description={"suggested_value": v.get(CONF_UNSPLASH_KEY, "")}): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        vol.Required(CONF_UNSPLASH_QUERY, default=v.get(CONF_UNSPLASH_QUERY, DEFAULT_UNSPLASH_QUERY)): TextSelector(),
        vol.Required(CONF_UNSPLASH_MIX, default=v.get(CONF_UNSPLASH_MIX, False)): BooleanSelector(),
        vol.Required(CONF_PANEL_OPACITY, default=v.get(CONF_PANEL_OPACITY, DEFAULT_PANEL_OPACITY)): _box(
            min=30, max=100, step=5, unit_of_measurement="%"),
    })


class LichVietConfigFlow(ConfigFlow, domain=DOMAIN):
    """Thêm Lịch Việt (chỉ một lần)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={}, options=dict(DEFAULT_OPTIONS))
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> LichVietOptionsFlow:
        return LichVietOptionsFlow()


class LichVietOptionsFlow(OptionsFlow):
    """Menu: thông báo, ảnh nền, lưu."""

    def __init__(self) -> None:
        self._opts: dict[str, Any] | None = None

    @property
    def opts(self) -> dict[str, Any]:
        if self._opts is None:
            self._opts = {**DEFAULT_OPTIONS, **self.config_entry.options}
        return self._opts

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["notify", "background", "save"])

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_create_entry(data=self.opts)

    async def async_step_notify(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self.opts.update({
                CONF_TELEGRAM: list(user_input.get(CONF_TELEGRAM) or []),
                CONF_MOBILE: [m.removeprefix("notify.") for m in user_input.get(CONF_MOBILE) or []],
                CONF_REPORT_TIME: user_input[CONF_REPORT_TIME],
                CONF_ONLY_WHEN_EVENTS: bool(user_input[CONF_ONLY_WHEN_EVENTS]),
                CONF_HOLIDAY_REMIND: int(user_input[CONF_HOLIDAY_REMIND]),
                CONF_MONTHLY_REMIND: int(user_input[CONF_MONTHLY_REMIND]),
            })
            return await self.async_step_init()
        return self.async_show_form(step_id="notify", data_schema=_notify_schema(self.hass, self.opts))

    async def async_step_background(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self.opts.update({
                CONF_BG_ENABLED: bool(user_input[CONF_BG_ENABLED]),
                CONF_BG_MODE: user_input[CONF_BG_MODE],
                CONF_BG_FOLDER: (user_input.get(CONF_BG_FOLDER) or "").strip(),
                CONF_UNSPLASH_KEY: (user_input.get(CONF_UNSPLASH_KEY) or "").strip(),
                CONF_UNSPLASH_QUERY: (user_input.get(CONF_UNSPLASH_QUERY) or DEFAULT_UNSPLASH_QUERY).strip(),
                CONF_UNSPLASH_MIX: bool(user_input[CONF_UNSPLASH_MIX]),
                CONF_PANEL_OPACITY: int(user_input[CONF_PANEL_OPACITY]),
            })
            return await self.async_step_init()
        return self.async_show_form(step_id="background", data_schema=_background_schema(self.opts))
