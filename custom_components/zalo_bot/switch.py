"""Zalo Bot switches."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import get_device_info
from .const import (
    CONF_ENABLE_NOTIFICATIONS,
    CONF_MARKDOWN_ENABLED,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_MARKDOWN_ENABLED,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zalo Bot switches."""
    async_add_entities(
        [
            ZaloBotNotificationSwitch(hass, config_entry),
            ZaloBotMarkdownSwitch(hass, config_entry),
        ]
    )


class ZaloBotNotificationSwitch(SwitchEntity, RestoreEntity):
    """Enable/disable persistent action-result notifications.

    The old implementation rewrote the config entry on every toggle. Because the
    integration has an update listener, that caused a full config-entry reload for
    a simple switch press. RestoreEntity keeps the UI state across restarts without
    reconnecting the whole Zalo integration.
    """

    _attr_has_entity_name = True
    _attr_name = "Thông báo"
    _attr_icon = "mdi:bell"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_notifications"
        self._attr_device_info = get_device_info()
        current = {**config_entry.data, **config_entry.options}
        self._is_on = current.get(CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state == "on"
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if isinstance(entry_data, dict):
            entry_data[CONF_ENABLE_NOTIFICATIONS] = self._is_on

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **_kwargs) -> None:
        self._set_state(True)

    async def async_turn_off(self, **_kwargs) -> None:
        self._set_state(False)

    def _set_state(self, enabled: bool) -> None:
        self._is_on = enabled
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if isinstance(entry_data, dict):
            entry_data[CONF_ENABLE_NOTIFICATIONS] = enabled
        self.async_write_ha_state()


class ZaloBotMarkdownSwitch(SwitchEntity, RestoreEntity):
    """Enable/disable Markdown-to-Zalo formatting."""

    _attr_has_entity_name = True
    _attr_name = "Markdown"
    _attr_icon = "mdi:language-markdown"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_markdown"
        self._attr_device_info = get_device_info()
        self._is_on = DEFAULT_MARKDOWN_ENABLED

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state == "on"
        self.hass.data[DOMAIN][CONF_MARKDOWN_ENABLED] = self._is_on

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **_kwargs) -> None:
        self._is_on = True
        self.hass.data[DOMAIN][CONF_MARKDOWN_ENABLED] = True
        self.async_write_ha_state()
        _LOGGER.debug("Markdown formatting enabled")

    async def async_turn_off(self, **_kwargs) -> None:
        self._is_on = False
        self.hass.data[DOMAIN][CONF_MARKDOWN_ENABLED] = False
        self.async_write_ha_state()
        _LOGGER.debug("Markdown formatting disabled")
