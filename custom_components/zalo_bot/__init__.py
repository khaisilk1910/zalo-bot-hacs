"""Zalo Bot integration for Home Assistant."""

from __future__ import annotations

import logging
import os
import threading
import time
from urllib.parse import urlsplit
from collections.abc import Callable
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

from . import (
    account_features,
    chat_features,
    file_handling,
    group_features,
    login_qr_service,
    misc_features,
    quickmsg_features,
    reminder_features,
    sticker_features,
    user_features,
)

from .helpers import normalize_zalo_json_payload

from .const import (

    CONF_ENABLE_NOTIFICATIONS,
    CONF_MARKDOWN_COLOR,
    CONF_MARKDOWN_ENABLED,
    CONF_ZALO_SERVER,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_MARKDOWN_COLOR,
    DEFAULT_MARKDOWN_ENABLED,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_PROXY_SCHEMA,
    SERVICE_REMOVE_PROXY_SCHEMA,
    SERVICE_GET_PROXIES_SCHEMA,
    SERVICE_RESET_HIDDEN_CONVERS_PIN_SCHEMA,
    SERVICE_GET_MUTE_SCHEMA,
    SERVICE_GET_PIN_CONVERSATIONS_SCHEMA,
    SERVICE_ADD_REACTION_SCHEMA,
    SERVICE_DELETE_MESSAGE_SCHEMA,
    SERVICE_FORWARD_MESSAGE_SCHEMA,
    SERVICE_PARSE_LINK_SCHEMA,
    SERVICE_SEND_CARD_SCHEMA,
    SERVICE_SEND_LINK_SCHEMA,
    SERVICE_GET_LABELS_SCHEMA,
    SERVICE_BLOCK_VIEW_FEED_SCHEMA,
    SERVICE_CHANGE_ACCOUNT_AVATAR_SCHEMA,
    SERVICE_SEND_MESSAGE_SCHEMA,
    SERVICE_SEND_FILE_SCHEMA,
    SERVICE_SEND_IMAGE_SCHEMA,
    SERVICE_SEND_VIDEO_SCHEMA,
    SERVICE_GET_LOGGED_ACCOUNTS_SCHEMA,
    SERVICE_GET_ACCOUNT_DETAILS_SCHEMA,
    SERVICE_FIND_USER_SCHEMA,
    SERVICE_GET_USER_INFO_SCHEMA,
    SERVICE_SEND_FRIEND_REQUEST_SCHEMA,
    SERVICE_CREATE_GROUP_SCHEMA,
    SERVICE_GET_GROUP_INFO_SCHEMA,
    SERVICE_ADD_USER_TO_GROUP_SCHEMA,
    SERVICE_REMOVE_USER_FROM_GROUP_SCHEMA,
    SERVICE_SEND_IMAGE_TO_USER_SCHEMA,
    SERVICE_SEND_IMAGE_TO_GROUP_SCHEMA,
    SERVICE_UPDATE_HIDDEN_CONVERS_PIN_SCHEMA,
    SERVICE_GET_STICKERS_SCHEMA,
    SERVICE_GET_STICKERS_DETAIL_SCHEMA,
    SERVICE_CREATE_NOTE_GROUP_SCHEMA,
    SERVICE_EDIT_NOTE_GROUP_SCHEMA,
    SERVICE_GET_LIST_BOARD_SCHEMA,
    SERVICE_CREATE_POLL_SCHEMA,
    SERVICE_GET_POLL_DETAIL_SCHEMA,
    SERVICE_LOCK_POLL_SCHEMA,
    SERVICE_EDIT_REMINDER_SCHEMA,
    SERVICE_GET_REMINDER_SCHEMA,
    SERVICE_GET_LIST_REMINDER_SCHEMA,
    SERVICE_GET_REMINDER_RESPONSES_SCHEMA,
    SERVICE_ADD_QUICK_MESSAGE_SCHEMA,
    SERVICE_GET_QUICK_MESSAGE_SCHEMA,
    SERVICE_REMOVE_QUICK_MESSAGE_SCHEMA,
    SERVICE_UPDATE_QUICK_MESSAGE_SCHEMA,
    SERVICE_GET_AVATAR_LIST_SCHEMA,
    SERVICE_LAST_ONLINE_SCHEMA,
    SERVICE_SEND_TYPING_EVENT_SCHEMA,
    SERVICE_SEND_IMAGES_TO_USER_SCHEMA,
    SERVICE_SEND_IMAGES_TO_GROUP_SCHEMA,
    SERVICE_GET_ACCOUNT_WEBHOOKS_SCHEMA,
    SERVICE_GET_ACCOUNT_WEBHOOK_SCHEMA,
    SERVICE_SET_ACCOUNT_WEBHOOK_SCHEMA,
    SERVICE_DELETE_ACCOUNT_WEBHOOK_SCHEMA,
    SERVICE_ACCEPT_FRIEND_REQUEST_SCHEMA,
    SERVICE_BLOCK_USER_SCHEMA,
    SERVICE_UNBLOCK_USER_SCHEMA,
    SERVICE_SEND_STICKER_SCHEMA,
    SERVICE_UNDO_MESSAGE_SCHEMA,
    SERVICE_CREATE_REMINDER_SCHEMA,
    SERVICE_REMOVE_REMINDER_SCHEMA,
    SERVICE_CHANGE_GROUP_NAME_SCHEMA,
    SERVICE_CHANGE_GROUP_AVATAR_SCHEMA,
    SERVICE_SEND_VOICE_SCHEMA,
    SERVICE_GET_ALL_FRIENDS_SCHEMA,
    SERVICE_GET_RECEIVED_FRIEND_REQUESTS_SCHEMA,
    SERVICE_GET_SENT_FRIEND_REQUESTS_SCHEMA,
    SERVICE_UNDO_FRIEND_REQUEST_SCHEMA,
    SERVICE_REMOVE_FRIEND_SCHEMA,
    SERVICE_CHANGE_FRIEND_ALIAS_SCHEMA,
    SERVICE_REMOVE_FRIEND_ALIAS_SCHEMA,
    SERVICE_GET_ALL_GROUPS_SCHEMA,
    SERVICE_GET_GROUP_CHAT_HISTORY_SCHEMA,
    SERVICE_ADD_GROUP_DEPUTY_SCHEMA,
    SERVICE_REMOVE_GROUP_DEPUTY_SCHEMA,
    SERVICE_CHANGE_GROUP_OWNER_SCHEMA,
    SERVICE_DISPERSE_GROUP_SCHEMA,
    SERVICE_ENABLE_GROUP_LINK_SCHEMA,
    SERVICE_DISABLE_GROUP_LINK_SCHEMA,
    SERVICE_JOIN_GROUP_SCHEMA,
    SERVICE_LEAVE_GROUP_SCHEMA,
    SERVICE_UPDATE_PROFILE_SCHEMA,
    SERVICE_UPDATE_SETTINGS_SCHEMA,
    SERVICE_SET_MUTE_SCHEMA,
    SERVICE_SET_PINNED_CONVERSATION_SCHEMA,
    SERVICE_GET_UNREAD_MARK_SCHEMA,
    SERVICE_ADD_UNREAD_MARK_SCHEMA,
    SERVICE_REMOVE_UNREAD_MARK_SCHEMA,
    SERVICE_DELETE_CHAT_SCHEMA,
    SERVICE_GET_ARCHIVED_CHAT_LIST_SCHEMA,
    SERVICE_GET_AUTO_DELETE_CHAT_SCHEMA,
    SERVICE_UPDATE_AUTO_DELETE_CHAT_SCHEMA,
    SERVICE_GET_HIDDEN_CONVERSATIONS_SCHEMA,
    SERVICE_SET_HIDDEN_CONVERSATIONS_SCHEMA,
    SERVICE_GET_LOGIN_QR_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


class TimeoutSession(requests.Session):
    """Persistent authenticated HTTP session for Zalo Server.

    The old integration logged in before every service action. This client keeps
    the authenticated cookie, refreshes it lazily, and retries one request after
    a 401. This removes one HTTP round-trip from almost every action while still
    recovering cleanly after a Zalo Server restart/session expiry.
    """

    def __init__(self, server: str, username: str, password: str) -> None:
        super().__init__()
        self.server = server.rstrip("/")
        self.username = username
        self.password = password
        self._auth_lock = threading.RLock()
        self._authenticated_at = 0.0
        self._auth_ttl = 6 * 60 * 60
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0, pool_block=False)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def authenticate(self, force: bool = False) -> None:
        """Ensure the session has a valid Zalo Server login cookie."""
        now = time.monotonic()
        if not force and self._authenticated_at and now - self._authenticated_at < self._auth_ttl:
            return

        with self._auth_lock:
            now = time.monotonic()
            if not force and self._authenticated_at and now - self._authenticated_at < self._auth_ttl:
                return

            resp = super().request(
                "POST",
                f"{self.server}/api/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            try:
                data = resp.json()
            except ValueError as err:
                raise ConnectionError(
                    f"Zalo Server trả về dữ liệu đăng nhập không hợp lệ (HTTP {resp.status_code})"
                ) from err

            if resp.status_code != 200 or data.get("success") is not True:
                self._authenticated_at = 0.0
                raise ConnectionError(
                    f"Đăng nhập Zalo Server thất bại (HTTP {resp.status_code}): "
                    f"{data.get('message') or data.get('error') or 'unknown error'}"
                )
            self._authenticated_at = time.monotonic()

    def request(self, method, url, **kwargs):
        """Perform a request with timeout, cached login, and one 401 retry."""
        kwargs.setdefault("timeout", 60)
        target = str(url)
        is_login = target.rstrip("/") == f"{self.server}/api/login"
        target_parts = urlsplit(target)
        server_parts = urlsplit(self.server)
        is_our_server = (
            target_parts.scheme == server_parts.scheme
            and target_parts.netloc == server_parts.netloc
        )

        if is_our_server and not is_login:
            self.authenticate()

        # Zalo IDs routinely exceed JavaScript's Number.MAX_SAFE_INTEGER.
        # Force all known identifier fields to JSON strings before the request
        # reaches the Node.js server so no precision can be lost in JSON.parse.
        if is_our_server and "json" in kwargs:
            kwargs["json"] = normalize_zalo_json_payload(kwargs["json"])

        response = super().request(method, url, **kwargs)
        if is_our_server and not is_login and response.status_code == 401:
            response.close()
            self.authenticate(force=True)
            response = super().request(method, url, **kwargs)

        if response.status_code >= 400:
            detail = None
            try:
                body = response.json()
                if isinstance(body, dict):
                    detail = body.get("error") or body.get("message")
            except ValueError:
                detail = None
            if not detail:
                text = response.text.strip()
                detail = text[:500] if text else response.reason
            raise requests.HTTPError(
                f"Zalo Server HTTP {response.status_code}: {detail}",
                response=response,
            )

        return response


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

session: TimeoutSession | None = None
zalo_server: str | None = None
_admin_user: str | None = None
_admin_pass: str | None = None
WWW_DIR: str | None = None
PUBLIC_DIR: str | None = None

SERVICE_DEFINITIONS = (
    ("send_message", chat_features.async_send_message_service, SERVICE_SEND_MESSAGE_SCHEMA),
    ("send_file", chat_features.async_send_file_service, SERVICE_SEND_FILE_SCHEMA),
    ("send_image", chat_features.async_send_image_service, SERVICE_SEND_IMAGE_SCHEMA),
    ("send_video", chat_features.async_send_video_service, SERVICE_SEND_VIDEO_SCHEMA),
    ("get_logged_accounts", account_features.async_get_logged_accounts_service, SERVICE_GET_LOGGED_ACCOUNTS_SCHEMA),
    ("get_account_details", account_features.async_get_account_details_service, SERVICE_GET_ACCOUNT_DETAILS_SCHEMA),
    ("find_user", user_features.async_find_user_service, SERVICE_FIND_USER_SCHEMA),
    ("get_user_info", user_features.async_get_user_info_service, SERVICE_GET_USER_INFO_SCHEMA),
    ("send_friend_request", user_features.async_send_friend_request_service, SERVICE_SEND_FRIEND_REQUEST_SCHEMA),
    ("create_group", group_features.async_create_group_service, SERVICE_CREATE_GROUP_SCHEMA),
    ("get_group_info", group_features.async_get_group_info_service, SERVICE_GET_GROUP_INFO_SCHEMA),
    ("add_user_to_group", group_features.async_add_user_to_group_service, SERVICE_ADD_USER_TO_GROUP_SCHEMA),
    ("remove_user_from_group", group_features.async_remove_user_from_group_service, SERVICE_REMOVE_USER_FROM_GROUP_SCHEMA),
    ("send_image_to_user", chat_features.async_send_image_to_user_service, SERVICE_SEND_IMAGE_TO_USER_SCHEMA),
    ("send_image_to_group", chat_features.async_send_image_to_group_service, SERVICE_SEND_IMAGE_TO_GROUP_SCHEMA),
    ("get_proxies", account_features.async_get_proxies_service, SERVICE_GET_PROXIES_SCHEMA),
    ("add_proxy", account_features.async_add_proxy_service, SERVICE_ADD_PROXY_SCHEMA),
    ("remove_proxy", account_features.async_remove_proxy_service, SERVICE_REMOVE_PROXY_SCHEMA),
    ("accept_friend_request", user_features.async_accept_friend_request_service, SERVICE_ACCEPT_FRIEND_REQUEST_SCHEMA),
    ("block_user", user_features.async_block_user_service, SERVICE_BLOCK_USER_SCHEMA),
    ("unblock_user", user_features.async_unblock_user_service, SERVICE_UNBLOCK_USER_SCHEMA),
    ("send_sticker", chat_features.async_send_sticker_service, SERVICE_SEND_STICKER_SCHEMA),
    ("undo_message", misc_features.async_undo_message_service, SERVICE_UNDO_MESSAGE_SCHEMA),
    ("get_received_friend_requests", user_features.async_get_received_friend_requests_service, SERVICE_GET_RECEIVED_FRIEND_REQUESTS_SCHEMA),
    ("get_sent_friend_requests", user_features.async_get_sent_friend_requests_service, SERVICE_GET_SENT_FRIEND_REQUESTS_SCHEMA),
    ("undo_friend_request", user_features.async_undo_friend_request_service, SERVICE_UNDO_FRIEND_REQUEST_SCHEMA),
    ("remove_friend", user_features.async_remove_friend_service, SERVICE_REMOVE_FRIEND_SCHEMA),
    ("change_friend_alias", user_features.async_change_friend_alias_service, SERVICE_CHANGE_FRIEND_ALIAS_SCHEMA),
    ("remove_friend_alias", user_features.async_remove_friend_alias_service, SERVICE_REMOVE_FRIEND_ALIAS_SCHEMA),
    ("get_all_groups", group_features.async_get_all_groups_service, SERVICE_GET_ALL_GROUPS_SCHEMA),
    ("get_group_chat_history", group_features.async_get_group_chat_history_service, SERVICE_GET_GROUP_CHAT_HISTORY_SCHEMA),
    ("add_group_deputy", group_features.async_add_group_deputy_service, SERVICE_ADD_GROUP_DEPUTY_SCHEMA),
    ("remove_group_deputy", group_features.async_remove_group_deputy_service, SERVICE_REMOVE_GROUP_DEPUTY_SCHEMA),
    ("change_group_owner", group_features.async_change_group_owner_service, SERVICE_CHANGE_GROUP_OWNER_SCHEMA),
    ("disperse_group", group_features.async_disperse_group_service, SERVICE_DISPERSE_GROUP_SCHEMA),
    ("enable_group_link", group_features.async_enable_group_link_service, SERVICE_ENABLE_GROUP_LINK_SCHEMA),
    ("disable_group_link", group_features.async_disable_group_link_service, SERVICE_DISABLE_GROUP_LINK_SCHEMA),
    ("join_group", group_features.async_join_group_service, SERVICE_JOIN_GROUP_SCHEMA),
    ("leave_group", group_features.async_leave_group_service, SERVICE_LEAVE_GROUP_SCHEMA),
    ("update_profile", user_features.async_update_profile_service, SERVICE_UPDATE_PROFILE_SCHEMA),
    ("update_settings", misc_features.async_update_settings_service, SERVICE_UPDATE_SETTINGS_SCHEMA),
    ("set_mute", misc_features.async_set_mute_service, SERVICE_SET_MUTE_SCHEMA),
    ("set_pinned_conversation", misc_features.async_set_pinned_conversation_service, SERVICE_SET_PINNED_CONVERSATION_SCHEMA),
    ("get_unread_mark", misc_features.async_get_unread_mark_service, SERVICE_GET_UNREAD_MARK_SCHEMA),
    ("add_unread_mark", misc_features.async_add_unread_mark_service, SERVICE_ADD_UNREAD_MARK_SCHEMA),
    ("remove_unread_mark", misc_features.async_remove_unread_mark_service, SERVICE_REMOVE_UNREAD_MARK_SCHEMA),
    ("delete_chat", misc_features.async_delete_chat_service, SERVICE_DELETE_CHAT_SCHEMA),
    ("get_archived_chat_list", misc_features.async_get_archived_chat_list_service, SERVICE_GET_ARCHIVED_CHAT_LIST_SCHEMA),
    ("get_auto_delete_chat", misc_features.async_get_auto_delete_chat_service, SERVICE_GET_AUTO_DELETE_CHAT_SCHEMA),
    ("update_auto_delete_chat", misc_features.async_update_auto_delete_chat_service, SERVICE_UPDATE_AUTO_DELETE_CHAT_SCHEMA),
    ("get_hidden_conversations", misc_features.async_get_hidden_conversations_service, SERVICE_GET_HIDDEN_CONVERSATIONS_SCHEMA),
    ("set_hidden_conversations", misc_features.async_set_hidden_conversations_service, SERVICE_SET_HIDDEN_CONVERSATIONS_SCHEMA),
    ("update_hidden_convers_pin", misc_features.async_update_hidden_convers_pin_service, SERVICE_UPDATE_HIDDEN_CONVERS_PIN_SCHEMA),
    ("reset_hidden_convers_pin", misc_features.async_reset_hidden_convers_pin_service, SERVICE_RESET_HIDDEN_CONVERS_PIN_SCHEMA),
    ("get_mute", misc_features.async_get_mute_service, SERVICE_GET_MUTE_SCHEMA),
    ("get_pin_conversations", misc_features.async_get_pin_conversations_service, SERVICE_GET_PIN_CONVERSATIONS_SCHEMA),
    ("add_reaction", misc_features.async_add_reaction_service, SERVICE_ADD_REACTION_SCHEMA),
    ("delete_message", misc_features.async_delete_message_service, SERVICE_DELETE_MESSAGE_SCHEMA),
    ("forward_message", misc_features.async_forward_message_service, SERVICE_FORWARD_MESSAGE_SCHEMA),
    ("parse_link", misc_features.async_parse_link_service, SERVICE_PARSE_LINK_SCHEMA),
    ("send_card", misc_features.async_send_card_service, SERVICE_SEND_CARD_SCHEMA),
    ("send_link", misc_features.async_send_link_service, SERVICE_SEND_LINK_SCHEMA),
    ("get_stickers", sticker_features.async_get_stickers_service, SERVICE_GET_STICKERS_SCHEMA),
    ("get_stickers_detail", sticker_features.async_get_stickers_detail_service, SERVICE_GET_STICKERS_DETAIL_SCHEMA),
    ("create_note_group", group_features.async_create_note_group_service, SERVICE_CREATE_NOTE_GROUP_SCHEMA),
    ("edit_note_group", group_features.async_edit_note_group_service, SERVICE_EDIT_NOTE_GROUP_SCHEMA),
    ("get_list_board", group_features.async_get_list_board_service, SERVICE_GET_LIST_BOARD_SCHEMA),
    ("create_poll", group_features.async_create_poll_service, SERVICE_CREATE_POLL_SCHEMA),
    ("get_poll_detail", group_features.async_get_poll_detail_service, SERVICE_GET_POLL_DETAIL_SCHEMA),
    ("lock_poll", group_features.async_lock_poll_service, SERVICE_LOCK_POLL_SCHEMA),
    ("edit_reminder", reminder_features.async_edit_reminder_service, SERVICE_EDIT_REMINDER_SCHEMA),
    ("get_reminder", reminder_features.async_get_reminder_service, SERVICE_GET_REMINDER_SCHEMA),
    ("get_list_reminder", reminder_features.async_get_list_reminder_service, SERVICE_GET_LIST_REMINDER_SCHEMA),
    ("get_reminder_responses", reminder_features.async_get_reminder_responses_service, SERVICE_GET_REMINDER_RESPONSES_SCHEMA),
    ("add_quick_message", quickmsg_features.async_add_quick_message_service, SERVICE_ADD_QUICK_MESSAGE_SCHEMA),
    ("get_quick_message", quickmsg_features.async_get_quick_message_service, SERVICE_GET_QUICK_MESSAGE_SCHEMA),
    ("remove_quick_message", quickmsg_features.async_remove_quick_message_service, SERVICE_REMOVE_QUICK_MESSAGE_SCHEMA),
    ("update_quick_message", quickmsg_features.async_update_quick_message_service, SERVICE_UPDATE_QUICK_MESSAGE_SCHEMA),
    ("get_labels", misc_features.async_get_labels_service, SERVICE_GET_LABELS_SCHEMA),
    ("block_view_feed", misc_features.async_block_view_feed_service, SERVICE_BLOCK_VIEW_FEED_SCHEMA),
    ("change_account_avatar", misc_features.async_change_account_avatar_service, SERVICE_CHANGE_ACCOUNT_AVATAR_SCHEMA),
    ("get_avatar_list", user_features.async_get_avatar_list_service, SERVICE_GET_AVATAR_LIST_SCHEMA),
    ("last_online", user_features.async_last_online_service, SERVICE_LAST_ONLINE_SCHEMA),
    ("send_typing_event", chat_features.async_send_typing_event_service, SERVICE_SEND_TYPING_EVENT_SCHEMA),
    ("send_images_to_user", chat_features.async_send_images_to_user_service, SERVICE_SEND_IMAGES_TO_USER_SCHEMA),
    ("get_account_webhooks", account_features.async_get_account_webhooks_service, SERVICE_GET_ACCOUNT_WEBHOOKS_SCHEMA),
    ("get_account_webhook", account_features.async_get_account_webhook_service, SERVICE_GET_ACCOUNT_WEBHOOK_SCHEMA),
    ("set_account_webhook", account_features.async_set_account_webhook_service, SERVICE_SET_ACCOUNT_WEBHOOK_SCHEMA),
    ("delete_account_webhook", account_features.async_delete_account_webhook_service, SERVICE_DELETE_ACCOUNT_WEBHOOK_SCHEMA),
    ("send_images_to_group", chat_features.async_send_images_to_group_service, SERVICE_SEND_IMAGES_TO_GROUP_SCHEMA),
    ("create_reminder", misc_features.async_create_reminder_service, SERVICE_CREATE_REMINDER_SCHEMA),
    ("remove_reminder", misc_features.async_remove_reminder_service, SERVICE_REMOVE_REMINDER_SCHEMA),
    ("change_group_name", group_features.async_change_group_name_service, SERVICE_CHANGE_GROUP_NAME_SCHEMA),
    ("change_group_avatar", group_features.async_change_group_avatar_service, SERVICE_CHANGE_GROUP_AVATAR_SCHEMA),
    ("send_voice", chat_features.async_send_voice_service, SERVICE_SEND_VOICE_SCHEMA),
    ("get_all_friends", user_features.async_get_all_friends_service, SERVICE_GET_ALL_FRIENDS_SCHEMA),
    ("get_login_qr", login_qr_service.async_get_login_qr, SERVICE_GET_LOGIN_QR_SCHEMA),
)


def get_device_info() -> DeviceInfo:
    """Return device information shared by all Zalo Bot entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, "zalo_bot")},
        name="Zalo Bot",
        manufacturer="Smarthome Black",
        model="Zalo Bot",
        sw_version="2026.8.18.3",
    )


def _zalo_login() -> None:
    """Ensure the shared Zalo Server session is authenticated."""
    if session is None or not zalo_server:
        raise ConnectionError("Zalo Bot chưa được cấu hình hoặc config entry chưa được tải")
    session.authenticate()


def _make_service_handler(
    hass: HomeAssistant,
    handler: Callable[..., Any],
) -> Callable[[ServiceCall], Any]:
    """Wrap a feature service so services can be registered in async_setup."""

    async def _handle(call: ServiceCall):
        if not zalo_server or session is None:
            raise ServiceValidationError(
                "Zalo Bot chưa có config entry đang hoạt động. "
                "Hãy cấu hình hoặc tải lại integration Zalo Bot."
            )
        try:
            result = await handler(hass, call, _zalo_login)
        except HomeAssistantError:
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as err:
            raise HomeAssistantError(f"Không thể giao tiếp với Zalo Server: {err}") from err

        # Feature modules preserve legacy behavior by returning {"error": ...}.
        # Surface that as a real HA action failure so automations can react.
        if isinstance(result, dict):
            if result.get("error"):
                raise HomeAssistantError(str(result["error"]))
            if result.get("success") is False:
                raise HomeAssistantError(
                    str(result.get("message") or "Zalo Server báo thao tác thất bại")
                )
        return result if call.return_response else None

    return _handle


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Zalo Bot and register service actions once."""
    hass.data.setdefault(DOMAIN, {})

    for service_name, handler, schema in SERVICE_DEFINITIONS:
        if hass.services.has_service(DOMAIN, service_name):
            continue
        hass.services.async_register(
            DOMAIN,
            service_name,
            _make_service_handler(hass, handler),
            schema=schema,
            supports_response=SupportsResponse.OPTIONAL,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Zalo Bot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    config = {**entry.data, **entry.options}

    if CONF_ENABLE_NOTIFICATIONS not in config:
        config[CONF_ENABLE_NOTIFICATIONS] = DEFAULT_ENABLE_NOTIFICATIONS

    hass.data[DOMAIN][CONF_MARKDOWN_ENABLED] = DEFAULT_MARKDOWN_ENABLED
    hass.data[DOMAIN][CONF_MARKDOWN_COLOR] = DEFAULT_MARKDOWN_COLOR

    global session, zalo_server, _admin_user, _admin_pass, WWW_DIR, PUBLIC_DIR
    zalo_server = str(config.get(CONF_ZALO_SERVER) or "").rstrip("/")
    _admin_user = config.get(CONF_USERNAME, "admin")
    _admin_pass = config.get(CONF_PASSWORD, "admin")
    session = TimeoutSession(zalo_server, _admin_user, _admin_pass) if zalo_server else None

    hass.data[DOMAIN][entry.entry_id] = config
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not zalo_server:
        _LOGGER.error("Không tìm thấy URL Zalo Server. Vui lòng kiểm tra cấu hình.")
        return False

    config_dir = hass.config.path()
    WWW_DIR = os.path.join(config_dir, "www")
    # Host-side path shared with the v1.0.4+ Docker stack:
    # /opt/home-assistant/config/www/zalo-server -> /config/www/zalo_bot
    PUBLIC_DIR = os.path.join(WWW_DIR, "zalo-server")

    file_handling.PUBLIC_DIR = PUBLIC_DIR
    chat_features.set_globals(session, zalo_server)
    group_features.set_globals(session, zalo_server)
    user_features.set_globals(hass, session, zalo_server)
    account_features.set_globals(hass, session, zalo_server)
    misc_features.set_globals(session, zalo_server)
    sticker_features.set_globals(session, zalo_server)
    reminder_features.set_globals(session, zalo_server)
    quickmsg_features.set_globals(session, zalo_server)
    login_qr_service.set_globals(session, zalo_server)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    device_registry = dr.async_get(hass)
    device_info = get_device_info()
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers=device_info["identifiers"],
        manufacturer=device_info["manufacturer"],
        name=device_info["name"],
        model=device_info["model"],
        sw_version=device_info["sw_version"],
    )

    return True


async def _async_update_listener(hass: HomeAssistant, entry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry without removing globally registered services."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        global session, zalo_server, _admin_user, _admin_pass
        if session is not None:
            await hass.async_add_executor_job(session.close)
        session = None
        zalo_server = None
        _admin_user = None
        _admin_pass = None

    return unload_ok
