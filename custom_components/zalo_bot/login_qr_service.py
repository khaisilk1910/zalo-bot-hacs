"""Service helper for requesting a Zalo login QR code."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

session = None
zalo_server = None


def set_globals(sess, server):
    global session, zalo_server
    session = sess
    zalo_server = server


async def async_get_login_qr(hass, call, zalo_login):
    """Request a QR code and show it in a persistent notification."""
    try:
        url = f"{zalo_server}/zalo-login"
        resp = await hass.async_add_executor_job(session.post, url)
        if resp.status_code >= 400:
            return {"error": f"Zalo Server trả HTTP {resp.status_code}: {resp.text[:300]}"}
        try:
            data = resp.json()
        except ValueError:
            return {"error": "Zalo Server không trả JSON hợp lệ khi lấy mã QR"}

        qr_data = data.get("qrCodeImage")
        if not (isinstance(qr_data, str) and qr_data.startswith("data:image")):
            return {"error": data.get("error") or "Không lấy được mã QR đăng nhập"}

        message = f'<b>Quét mã QR để đăng nhập Zalo:</b><br><img src="{qr_data}" width="300">'
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "message": message,
                "title": "Zalo Bot - Đăng nhập Zalo",
                "notification_id": "zalo_bot_login_qr",
            },
        )
        _LOGGER.debug("Đã lấy mã QR đăng nhập Zalo thành công")
        return {"success": True, "message": "Đã tạo mã QR đăng nhập"}
    except Exception as err:
        _LOGGER.error("Lỗi khi lấy mã QR: %s", err, exc_info=True)
        return {"error": str(err)}
