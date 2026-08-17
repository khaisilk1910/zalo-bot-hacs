"""Zalo Bot button entities."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from . import get_device_info

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Thiết lập các button từ config entry."""
    async_add_entities([ZaloBotLoginQRButton(hass, config_entry)])
    # Nếu muốn thêm nhiều button, có thể append vào list này

class ZaloBotLoginQRButton(ButtonEntity):
    """Button để lấy mã QR đăng nhập Zalo."""
    _attr_has_entity_name = True
    _attr_name = "Login QR"
    _attr_icon = "mdi:qrcode"
    _attr_unique_id = "login_qr_button"
    _attr_device_info = get_device_info()

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__()
        self.hass = hass
        self.config_entry = config_entry

    async def async_press(self) -> None:
        """Khi nhấn nút sẽ gọi service lấy mã QR đăng nhập."""
        await self.hass.services.async_call(
            DOMAIN,
            "get_login_qr",
            {},
            blocking=True
        )
        _LOGGER.info("Đã gọi service get_login_qr từ button.")