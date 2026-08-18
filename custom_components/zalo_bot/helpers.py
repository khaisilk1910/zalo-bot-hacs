"""Shared helpers for the Zalo Bot integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


# Zalo identifiers are commonly larger than JavaScript's safe integer range.
# Keep these fields as strings when serializing requests to the Node.js server.
_ZALO_ID_KEYS = frozenset(
    {
        "threadId",
        "threadID",
        "userId",
        "uid",
        "uidFrom",
        "idTo",
        "ownId",
        "groupId",
        "memberId",
        "friendId",
        "conversationId",
        "msgId",
        "cliMsgId",
        "globalMsgId",
        "ownerId",
        "actionId",
        "reminderId",
        "topicId",
        "photoId",
    }
)

_ZALO_ID_LIST_KEYS = frozenset(
    {
        "threadIds",
        "userIds",
        "groupIds",
        "memberIds",
        "friendIds",
        "msgIds",
    }
)


ZALO_ID_PREFIX = "zalo:"


def normalize_zalo_id(value: Any) -> str:
    """Normalize a single Zalo identifier without losing precision.

    Home Assistant templates can produce Python integers for numeric-looking
    output. Python keeps those integers at arbitrary precision, so convert them
    to text *before* the request crosses the JSON/JavaScript boundary. Exact
    digit strings are preserved unchanged.

    ``zalo:<id>`` is a template-safe form: because it is not numeric-looking,
    Home Assistant/frontend JSON layers keep it as text. The prefix is removed
    before calling the Zalo Server.
    """
    if value is None:
        raise ValueError("Zalo ID không được để trống")
    if isinstance(value, bool):
        raise ValueError("Zalo ID không hợp lệ")
    if isinstance(value, int):
        return str(value)

    text = str(value).strip()
    if text.lower().startswith(ZALO_ID_PREFIX):
        text = text[len(ZALO_ID_PREFIX):].strip()
    if not text:
        return ""
    return text


def zalo_id_for_template(value: Any) -> str:
    """Return the non-numeric ``zalo:<id>`` representation for HA templates."""
    text = normalize_zalo_id(value)
    return f"{ZALO_ID_PREFIX}{text}" if text else ZALO_ID_PREFIX


_MESSAGE_TTL_ALIASES: dict[str, int] = {
    "off": 0,
    "none": 0,
    "0": 0,
    "1d": 24 * 60 * 60 * 1000,
    "7d": 7 * 24 * 60 * 60 * 1000,
    "14d": 14 * 24 * 60 * 60 * 1000,
}
for _hour in range(1, 25):
    _MESSAGE_TTL_ALIASES[f"{_hour}h"] = _hour * 60 * 60 * 1000


def normalize_thread_type(value: Any) -> int:
    """Return the zca-js thread type value (0=user, 1=group).

    Service YAML historically used both ``0``/``1`` and ``user``/``group``.
    Accept both forms so existing automations remain compatible.
    """
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        if value in (0, 1):
            return value
        raise ValueError('type không hợp lệ. Dùng 0/user hoặc 1/group.')

    normalized = str(value).strip().lower()
    if normalized in {"0", "user"}:
        return 0
    if normalized in {"1", "group"}:
        return 1
    raise ValueError('type không hợp lệ. Dùng 0/user hoặc 1/group.')


def normalize_message_ttl(value: Any) -> int:
    """Normalize a per-message TTL value to milliseconds.

    The send APIs in zca-js accept a TTL in milliseconds. Home Assistant's UI
    exposes friendly aliases (1h..24h, 1d, 7d, 14d and off), while YAML users
    may also provide an integer millisecond value directly.
    """
    if isinstance(value, bool):
        raise ValueError("ttl không hợp lệ")

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _MESSAGE_TTL_ALIASES:
            return _MESSAGE_TTL_ALIASES[normalized]
        try:
            ttl = int(normalized, 10)
        except ValueError as err:
            raise ValueError(
                "ttl không hợp lệ. Dùng off, 1h..24h, 1d, 7d, 14d hoặc milliseconds."
            ) from err
    elif isinstance(value, int):
        ttl = value
    else:
        raise ValueError(
            "ttl không hợp lệ. Dùng off, 1h..24h, 1d, 7d, 14d hoặc milliseconds."
        )

    if ttl < 0:
        raise ValueError("ttl phải lớn hơn hoặc bằng 0 milliseconds")
    return ttl


def normalize_zalo_json_payload(value: Any, *, _key: str | None = None) -> Any:
    """Return a JSON-safe copy that preserves Zalo identifiers as strings.

    Home Assistant templates may yield native numeric values. Python can retain
    arbitrarily large integers, but a Node.js JSON parser cannot safely represent
    integers above 2**53 - 1. Converting known Zalo identifier fields to strings
    before ``requests`` serializes them prevents silent precision loss.
    """
    if _key in _ZALO_ID_KEYS:
        if value is None or value == "":
            return value
        return normalize_zalo_id(value)

    if _key in _ZALO_ID_LIST_KEYS:
        if value is None:
            return value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [normalize_zalo_id(item) for item in value]
        return [normalize_zalo_id(value)]

    if isinstance(value, Mapping):
        return {
            str(key): normalize_zalo_json_payload(item, _key=str(key))
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [normalize_zalo_json_payload(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_zalo_json_payload(item) for item in value]

    return value
