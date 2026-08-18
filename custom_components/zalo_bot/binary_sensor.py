"""Binary sensors for Zalo Bot server and account connectivity."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import get_device_info
from .const import CONF_PASSWORD, CONF_USERNAME, CONF_ZALO_SERVER, DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Zalo Bot connectivity sensors."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    coordinator = ZaloLoginCoordinator(
        hass,
        str(config.get(CONF_ZALO_SERVER) or "").rstrip("/"),
        config.get(CONF_USERNAME),
        config.get(CONF_PASSWORD),
    )
    entry.async_on_unload(coordinator.async_close)
    async_add_entities(
        [
            ZaloLoginBinarySensor(coordinator, entry),
            ZaloServerBinarySensor(coordinator, entry),
        ]
    )

    # Do not make Home Assistant startup wait for Zalo Server/network I/O.
    # The config-entry-owned task is cancelled automatically on unload.
    entry.async_create_background_task(
        hass,
        coordinator.async_refresh(),
        "Zalo Bot initial connectivity refresh",
    )


class ZaloLoginCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll lightweight server/account state without logging in every minute."""

    def __init__(
        self, hass: HomeAssistant, zalo_server: str, username: str, password: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Zalo Login",
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )
        self.zalo_server = zalo_server
        self.username = username
        self.password = password
        # A dedicated session is required because Zalo Server authentication uses
        # cookies. It is explicitly closed on config-entry unload/reload.
        self.session = async_create_clientsession(
            hass,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            timeout=aiohttp.ClientTimeout(total=10),
        )
        self.data = {"logged_in": False, "total": 0, "accounts": []}
        self.server_reachable = False
        self.login_success = False

    async def async_close(self) -> None:
        """Close the dedicated cookie-preserving HTTP session on unload."""
        if not self.session.closed:
            await self.session.close()

    async def _async_login(self) -> bool:
        try:
            async with self.session.post(
                f"{self.zalo_server}/api/login",
                json={"username": self.username, "password": self.password},
            ) as resp:
                if resp.status != 200:
                    self.login_success = False
                    return False
                data = await resp.json(content_type=None)
                self.login_success = data.get("success") is True
                return self.login_success
        except (aiohttp.ClientError, TimeoutError, ValueError):
            self.login_success = False
            return False

    async def _async_server_health(self) -> bool:
        """Use the lightweight health endpoint, with a legacy compatibility fallback."""
        try:
            async with self.session.get(f"{self.zalo_server}/api/health") as resp:
                if resp.status == 200:
                    return True
                if resp.status != 404:
                    return False
            # Older Zalo Server builds may not expose /api/health.
            async with self.session.get(self.zalo_server) as resp:
                return resp.status < 500
        except (aiohttp.ClientError, TimeoutError):
            return False

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh server reachability and logged-in Zalo account summary."""
        self.server_reachable = await self._async_server_health()
        if not self.server_reachable:
            self.login_success = False
            return {"logged_in": False, "total": 0, "accounts": []}

        if not self.login_success and not await self._async_login():
            return {"logged_in": False, "total": 0, "accounts": []}

        try:
            async with self.session.get(
                f"{self.zalo_server}/api/accounts",
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status == 401:
                    self.login_success = False
                    if not await self._async_login():
                        return {"logged_in": False, "total": 0, "accounts": []}
                    async with self.session.get(
                        f"{self.zalo_server}/api/accounts",
                        headers={"Accept": "application/json"},
                    ) as retry_resp:
                        if retry_resp.status != 200:
                            return {"logged_in": False, "total": 0, "accounts": []}
                        response = await retry_resp.json(content_type=None)
                else:
                    if resp.status != 200:
                        return {"logged_in": False, "total": 0, "accounts": []}
                    response = await resp.json(content_type=None)

            if response.get("success"):
                total = response.get("total", 0)
                return {
                    "logged_in": total > 0,
                    "total": total,
                    "accounts": response.get("data", []),
                }
        except (aiohttp.ClientError, TimeoutError, ValueError):
            # Health succeeded but this API call failed: keep server sensor truthful,
            # while marking account status unavailable/off for this cycle.
            _LOGGER.debug("Không thể cập nhật /api/accounts", exc_info=True)

        return {"logged_in": False, "total": 0, "accounts": []}


class ZaloLoginBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Whether at least one Zalo account is currently logged in."""

    _attr_has_entity_name = True
    _attr_name = "Zalo Login"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:account"

    def __init__(self, coordinator: ZaloLoginCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_login_status"
        self._attr_device_info = get_device_info()

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("logged_in", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "total_accounts": self.coordinator.data.get("total", 0),
            "accounts": self.coordinator.data.get("accounts", []),
        }


class ZaloServerBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Whether Zalo Server is reachable."""

    _attr_has_entity_name = True
    _attr_name = "Zalo Server"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:server"

    def __init__(self, coordinator: ZaloLoginCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_server_status"
        self._attr_device_info = get_device_info()

    @property
    def is_on(self) -> bool:
        return self.coordinator.server_reachable
