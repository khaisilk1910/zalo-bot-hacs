"""Config flow for the Zalo Bot integration."""

from __future__ import annotations

from typing import Any

import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_ENABLE_NOTIFICATIONS,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_ZALO_SERVER,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DOMAIN,
)

REQUEST_TIMEOUT = 10


def _normalize_server_url(value: str) -> str:
    """Normalize the configured Zalo Server URL."""
    value = value.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    return value


def _validate_connection(server: str, username: str, password: str) -> None:
    """Validate that Zalo Server is reachable and credentials are accepted."""
    try:
        response = requests.post(
            f"{server}/api/login",
            json={"username": username, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as err:
        raise CannotConnect from err

    if response.status_code in (401, 403):
        raise InvalidAuth

    if response.status_code >= 400:
        raise CannotConnect

    try:
        data = response.json()
    except ValueError as err:
        raise CannotConnect from err

    if not data.get("success"):
        raise InvalidAuth


class CannotConnect(Exception):
    """Error to indicate we cannot connect to Zalo Server."""


class InvalidAuth(Exception):
    """Error to indicate invalid authentication."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zalo Bot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            server = _normalize_server_url(user_input[CONF_ZALO_SERVER])
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                await self.hass.async_add_executor_job(
                    _validate_connection, server, username, password
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                data = dict(user_input)
                data[CONF_ZALO_SERVER] = server
                return self.async_create_entry(title="Zalo Bot", data=data)

        defaults = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ZALO_SERVER,
                        default=defaults.get(CONF_ZALO_SERVER, "http://127.0.0.1:3000"),
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=defaults.get(CONF_USERNAME, "admin"),
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=defaults.get(CONF_PASSWORD, "admin"),
                    ): str,
                    vol.Optional(
                        CONF_ENABLE_NOTIFICATIONS,
                        default=defaults.get(
                            CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS
                        ),
                    ): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Zalo Bot options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            server = _normalize_server_url(user_input[CONF_ZALO_SERVER])
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                await self.hass.async_add_executor_job(
                    _validate_connection, server, username, password
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                data = dict(user_input)
                data[CONF_ZALO_SERVER] = server
                return self.async_create_entry(title="", data=data)

        values = user_input or current
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ZALO_SERVER,
                        default=values.get(CONF_ZALO_SERVER, "http://127.0.0.1:3000"),
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=values.get(CONF_USERNAME, "admin"),
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=values.get(CONF_PASSWORD, "admin"),
                    ): str,
                    vol.Optional(
                        CONF_ENABLE_NOTIFICATIONS,
                        default=values.get(
                            CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS
                        ),
                    ): bool,
                }
            ),
            errors=errors,
        )
