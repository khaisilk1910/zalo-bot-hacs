"""Các tính năng liên quan đến sticker cho Zalo Bot."""
import logging
from .notification import show_result_notification

_LOGGER = logging.getLogger(__name__)

session = None
zalo_server = None

def set_globals(sess, server):
    """Cập nhật các biến toàn cục."""
    global session, zalo_server
    session = sess
    zalo_server = server

async def async_get_stickers_service(hass, call, zalo_login):
    """Tìm kiếm sticker."""
    _LOGGER.debug("Dịch vụ async_get_stickers được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "query": call.data["query"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getStickersByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi tìm kiếm sticker: %s", resp.text)
        await show_result_notification(hass, "tìm kiếm sticker", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_stickers: %s", e)
        await show_result_notification(hass, "tìm kiếm sticker", None, error=e)
        return {"error": str(e)}

async def async_get_stickers_detail_service(hass, call, zalo_login):
    """Lấy chi tiết sticker."""
    _LOGGER.debug("Dịch vụ async_get_stickers_detail được gọi với: %s", call.data)
    try:
        try:
            sticker_id = int(call.data["sticker_id"])
        except ValueError:
            sticker_id = call.data["sticker_id"]
        payload = {
            "accountSelection": call.data["account_selection"],
            "stickerId": sticker_id
        }
        _LOGGER.debug("Gửi payload đến getStickersDetailByAccount: %s", payload)
        url = f"{zalo_server}/api/getStickersDetailByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi lấy chi tiết sticker: %s", resp.text)
        await show_result_notification(hass, "lấy chi tiết sticker", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_stickers_detail: %s", e)
        await show_result_notification(hass, "lấy chi tiết sticker", None, error=e)
        return {"error": str(e)}
