"""Zalo Bot select entities."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from .const import CONF_MARKDOWN_COLOR, DEFAULT_MARKDOWN_COLOR, DOMAIN
from . import get_device_info

_LOGGER = logging.getLogger(__name__)

COLOR_OPTIONS = ["none", "red", "orange", "yellow", "green"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ZaloBotMarkdownColorSelect(hass, config_entry)])


class ZaloBotMarkdownColorSelect(SelectEntity, RestoreEntity):
    """Select entity để chọn màu cho markdown bold."""

    _attr_has_entity_name = True
    _attr_name = "Markdown Color"
    _attr_icon = "mdi:palette"
    _attr_options = COLOR_OPTIONS

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__()
        self.hass = hass
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_markdown_color"
        self._attr_device_info = get_device_info()
        self._attr_current_option = DEFAULT_MARKDOWN_COLOR

    async def async_added_to_hass(self) -> None:
        """Khôi phục lựa chọn màu đã lưu sau khi restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in COLOR_OPTIONS:
            self._attr_current_option = last_state.state
        self.hass.data[DOMAIN][CONF_MARKDOWN_COLOR] = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.hass.data[DOMAIN][CONF_MARKDOWN_COLOR] = option
        self.async_write_ha_state()
        _LOGGER.info("Markdown color set to: %s", option)
