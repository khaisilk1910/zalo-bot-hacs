"""Constants for the Zalo Bot integration."""
from homeassistant.const import Platform
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .helpers import normalize_message_ttl, normalize_zalo_id

DOMAIN = "zalo_bot"

# Configuration constants
CONF_ZALO_SERVER = "zalo_server"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ENABLE_NOTIFICATIONS = "enable_notifications"
DEFAULT_ENABLE_NOTIFICATIONS = True
SIGNAL_NOTIFICATION_TOGGLE = f"{DOMAIN}_notification_toggle"

# Markdown config keys
CONF_MARKDOWN_ENABLED = "markdown_enabled"
CONF_MARKDOWN_COLOR = "markdown_color"
DEFAULT_MARKDOWN_ENABLED = True
DEFAULT_MARKDOWN_COLOR = "none"

# Platforms
PLATFORMS = [Platform.SWITCH, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT]

# Per-message TTL accepted by zca-js send APIs. Friendly aliases are
# normalized to milliseconds by the schema before handlers build JSON.
MESSAGE_TTL_SCHEMA = vol.All(vol.Any(cv.string, int), normalize_message_ttl)
ZALO_ID_SCHEMA = vol.All(normalize_zalo_id)

# Conversation-wide Auto Delete is a different Zalo API with only these
# officially exposed values in zca-js 2.1.2. Keep it separate from message TTL.
CHAT_AUTO_DELETE_TTL_VALUES = ("off", "1d", "7d", "14d", 0, 86400000, 604800000, 1209600000)
CHAT_AUTO_DELETE_TTL_SCHEMA = vol.In(CHAT_AUTO_DELETE_TTL_VALUES)

# Schema cho các service
SERVICE_SEND_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("message"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
    vol.Optional("quote"): vol.Schema({
        vol.Required("content"): vol.Any(dict, cv.string),
        vol.Optional("msgType"): cv.string,
        vol.Required("uidFrom"): ZALO_ID_SCHEMA,
        vol.Required("cliMsgId"): ZALO_ID_SCHEMA,
    }),
})

SERVICE_SEND_FILE_SCHEMA = vol.Schema({
    vol.Required("file_path_or_url"): cv.string,
    vol.Optional("message"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_SEND_IMAGE_SCHEMA = vol.Schema({
    vol.Required("image_path"): cv.string,
    vol.Optional("message"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_GET_LOGGED_ACCOUNTS_SCHEMA = vol.Schema({})

SERVICE_GET_ACCOUNT_DETAILS_SCHEMA = vol.Schema({
    vol.Optional("own_id", default=""): ZALO_ID_SCHEMA,
})

SERVICE_FIND_USER_SCHEMA = vol.Schema({
    vol.Optional("phone", default=""): cv.string,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_GET_USER_INFO_SCHEMA = vol.Schema({
    vol.Optional("user_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_SEND_FRIEND_REQUEST_SCHEMA = vol.Schema({
    vol.Optional("user_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("message", default="Xin chào, hãy kết bạn với tôi!"): cv.string,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_CREATE_GROUP_SCHEMA = vol.Schema({
    vol.Optional("members", default=""): cv.string,
    vol.Optional("name", default=""): cv.string,
    vol.Optional("avatar_path", default=""): cv.string,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_GET_GROUP_INFO_SCHEMA = vol.Schema({
    vol.Optional("group_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_ADD_USER_TO_GROUP_SCHEMA = vol.Schema({
    vol.Optional("group_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("member_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_REMOVE_USER_FROM_GROUP_SCHEMA = vol.Schema({
    vol.Optional("group_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("member_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
})

SERVICE_SEND_IMAGE_TO_USER_SCHEMA = vol.Schema({
    vol.Optional("image_path", default=""): cv.string,
    vol.Optional("thread_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_SEND_IMAGES_TO_USER_SCHEMA = vol.Schema({
    vol.Optional("image_paths", default=""): cv.string,
    vol.Optional("thread_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_SEND_IMAGE_TO_GROUP_SCHEMA = vol.Schema({
    vol.Optional("image_path", default=""): cv.string,
    vol.Optional("thread_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_SEND_IMAGES_TO_GROUP_SCHEMA = vol.Schema({
    vol.Optional("image_paths", default=""): cv.string,
    vol.Optional("thread_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("account_selection", default=""): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_GET_ACCOUNT_WEBHOOKS_SCHEMA = vol.Schema({})

SERVICE_GET_ACCOUNT_WEBHOOK_SCHEMA = vol.Schema({
    vol.Optional("own_id", default=""): ZALO_ID_SCHEMA,
})

SERVICE_SET_ACCOUNT_WEBHOOK_SCHEMA = vol.Schema({
    vol.Optional("own_id", default=""): ZALO_ID_SCHEMA,
    vol.Optional("message_webhook_url", default=""): cv.string,
    vol.Optional("group_event_webhook_url", default=""): cv.string,
    vol.Optional("reaction_webhook_url", default=""): cv.string,
})

SERVICE_DELETE_ACCOUNT_WEBHOOK_SCHEMA = vol.Schema({
    vol.Optional("own_id", default=""): ZALO_ID_SCHEMA,
})

SERVICE_GET_PROXIES_SCHEMA = vol.Schema({})

SERVICE_ADD_PROXY_SCHEMA = vol.Schema({
    vol.Optional("proxy_url", default=""): cv.string,
})

SERVICE_REMOVE_PROXY_SCHEMA = vol.Schema({
    vol.Optional("proxy_url", default=""): cv.string,
})

SERVICE_ACCEPT_FRIEND_REQUEST_SCHEMA = vol.Schema({
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_BLOCK_USER_SCHEMA = vol.Schema({
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_UNBLOCK_USER_SCHEMA = vol.Schema({
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_STICKER_SCHEMA = vol.Schema({
    vol.Required("sticker_id"): ZALO_ID_SCHEMA,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
})

SERVICE_UNDO_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("msg_id"): ZALO_ID_SCHEMA,
    vol.Required("cli_msg_id"): ZALO_ID_SCHEMA,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
})

SERVICE_CREATE_REMINDER_SCHEMA = vol.Schema({
    vol.Required("title"): cv.string,
    # Legacy field kept schema-compatible with existing automations. zca-js 2.1.2
    # only exposes a single reminder title, so this field is no longer sent.
    vol.Optional("content"): cv.string,
    vol.Required("remind_time"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
})

SERVICE_REMOVE_REMINDER_SCHEMA = vol.Schema({
    vol.Required("reminder_id"): ZALO_ID_SCHEMA,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
})

SERVICE_CHANGE_GROUP_NAME_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("name"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_CHANGE_GROUP_AVATAR_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("image_path"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_VOICE_SCHEMA = vol.Schema({
    vol.Required("voice_path"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_GET_ALL_FRIENDS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_RECEIVED_FRIEND_REQUESTS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_SENT_FRIEND_REQUESTS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_UNDO_FRIEND_REQUEST_SCHEMA = vol.Schema({
    vol.Required("friend_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_REMOVE_FRIEND_SCHEMA = vol.Schema({
    vol.Required("friend_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_CHANGE_FRIEND_ALIAS_SCHEMA = vol.Schema({
    vol.Required("friend_id"): ZALO_ID_SCHEMA,
    vol.Required("alias"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_REMOVE_FRIEND_ALIAS_SCHEMA = vol.Schema({
    vol.Required("friend_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_ALL_GROUPS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_GROUP_CHAT_HISTORY_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Optional("count", default=50): vol.All(vol.Coerce(int), vol.Range(min=1, max=200)),
    vol.Required("account_selection"): cv.string,
})

SERVICE_ADD_GROUP_DEPUTY_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("member_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_REMOVE_GROUP_DEPUTY_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("member_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_CHANGE_GROUP_OWNER_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("member_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_DISPERSE_GROUP_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_ENABLE_GROUP_LINK_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_DISABLE_GROUP_LINK_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_JOIN_GROUP_SCHEMA = vol.Schema({
    vol.Required("link"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_LEAVE_GROUP_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Optional("silent", default=False): cv.boolean,
    vol.Required("account_selection"): cv.string,
})

SERVICE_UPDATE_PROFILE_SCHEMA = vol.Schema({
    vol.Optional("name"): cv.string,
    vol.Optional("dob"): cv.string,
    vol.Optional("gender", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_UPDATE_SETTINGS_SCHEMA = vol.Schema({
    vol.Required("setting_type"): cv.string,
    vol.Required("status"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SET_MUTE_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("duration"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SET_PINNED_CONVERSATION_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("pinned"): cv.boolean,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

# Các schema cho API mới bổ sung thêm
SERVICE_GET_UNREAD_MARK_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_ADD_UNREAD_MARK_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_REMOVE_UNREAD_MARK_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_DELETE_CHAT_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("last_message"): dict,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_ARCHIVED_CHAT_LIST_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_AUTO_DELETE_CHAT_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_UPDATE_AUTO_DELETE_CHAT_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("ttl"): CHAT_AUTO_DELETE_TTL_SCHEMA,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_HIDDEN_CONVERSATIONS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_SET_HIDDEN_CONVERSATIONS_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("hidden"): cv.boolean,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_UPDATE_HIDDEN_CONVERS_PIN_SCHEMA = vol.Schema({
    vol.Required("pin"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_RESET_HIDDEN_CONVERS_PIN_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_MUTE_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_PIN_CONVERSATIONS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_ADD_REACTION_SCHEMA = vol.Schema({
    vol.Required("icon"): cv.string,
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("msg_id"): ZALO_ID_SCHEMA,
    vol.Required("cli_msg_id"): ZALO_ID_SCHEMA,
    vol.Required("type"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_DELETE_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("msg_id"): ZALO_ID_SCHEMA,
    vol.Required("cli_msg_id"): ZALO_ID_SCHEMA,
    vol.Required("uid_from"): ZALO_ID_SCHEMA,
    vol.Required("type"): cv.string,
    vol.Optional("only_me", default=True): cv.boolean,
    vol.Required("account_selection"): cv.string,
})

SERVICE_FORWARD_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("message"): cv.string,
    vol.Required("thread_ids"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_PARSE_LINK_SCHEMA = vol.Schema({
    vol.Required("link"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_CARD_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_LINK_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("link"): cv.string,
    vol.Optional("message", default=""): cv.string,
    vol.Optional("thumbnail", default=""): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_STICKERS_SCHEMA = vol.Schema({
    vol.Required("query"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_STICKERS_DETAIL_SCHEMA = vol.Schema({
    vol.Required("sticker_album"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_VIDEO_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("video_path_or_url"): cv.string,
    vol.Optional("thumbnail_url", default=""): cv.string,
    vol.Optional("message", default=""): cv.string,
    vol.Optional("width", default=1280): cv.positive_int,
    vol.Optional("height", default=720): cv.positive_int,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
    vol.Optional("ttl"): MESSAGE_TTL_SCHEMA,
})

SERVICE_CREATE_NOTE_GROUP_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("title"): cv.string,
    vol.Optional("pin_act", default=True): cv.boolean,
    vol.Required("account_selection"): cv.string,
})

SERVICE_EDIT_NOTE_GROUP_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("topic_id"): ZALO_ID_SCHEMA,
    vol.Required("title"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_LIST_BOARD_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Optional("page", default=1): cv.positive_int,
    vol.Optional("count", default=20): cv.positive_int,
    vol.Required("account_selection"): cv.string,
})

SERVICE_CREATE_POLL_SCHEMA = vol.Schema({
    vol.Required("group_id"): ZALO_ID_SCHEMA,
    vol.Required("question"): cv.string,
    vol.Required("options"): cv.string,
    vol.Optional("allow_multi_choices", default=False): cv.boolean,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_POLL_DETAIL_SCHEMA = vol.Schema({
    vol.Required("poll_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_LOCK_POLL_SCHEMA = vol.Schema({
    vol.Required("poll_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_EDIT_REMINDER_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Required("topic_id"): ZALO_ID_SCHEMA,
    vol.Required("title"): cv.string,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_REMINDER_SCHEMA = vol.Schema({
    vol.Required("reminder_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_LIST_REMINDER_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Optional("page", default=1): cv.positive_int,
    vol.Optional("count", default=20): cv.positive_int,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_REMINDER_RESPONSES_SCHEMA = vol.Schema({
    vol.Required("reminder_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_ADD_QUICK_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("keyword"): cv.string,
    vol.Required("title"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_QUICK_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_REMOVE_QUICK_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("item_ids"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_UPDATE_QUICK_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("item_id"): ZALO_ID_SCHEMA,
    vol.Required("keyword"): cv.string,
    vol.Required("title"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_LABELS_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
})

SERVICE_BLOCK_VIEW_FEED_SCHEMA = vol.Schema({
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Required("is_block_feed"): cv.boolean,
    vol.Required("account_selection"): cv.string,
})

SERVICE_CHANGE_ACCOUNT_AVATAR_SCHEMA = vol.Schema({
    vol.Required("avatar_source"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_AVATAR_LIST_SCHEMA = vol.Schema({
    vol.Required("account_selection"): cv.string,
    vol.Optional("count"): cv.positive_int,
    vol.Optional("page"): cv.positive_int,
})

SERVICE_LAST_ONLINE_SCHEMA = vol.Schema({
    vol.Required("user_id"): ZALO_ID_SCHEMA,
    vol.Required("account_selection"): cv.string,
})

SERVICE_SEND_TYPING_EVENT_SCHEMA = vol.Schema({
    vol.Required("thread_id"): ZALO_ID_SCHEMA,
    vol.Optional("type", default="0"): cv.string,
    vol.Required("account_selection"): cv.string,
})

SERVICE_GET_LOGIN_QR_SCHEMA = vol.Schema({})