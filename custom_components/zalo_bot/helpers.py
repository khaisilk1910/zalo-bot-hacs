"""Shared helpers for the Zalo Bot integration."""

from __future__ import annotations

from typing import Any


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
