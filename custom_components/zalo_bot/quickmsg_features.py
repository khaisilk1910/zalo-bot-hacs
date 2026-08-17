"""Các tính năng liên quan đến quick message (tin nhắn nhanh) cho Zalo Bot."""
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

async def async_add_quick_message_service(hass, call, zalo_login):
    """Thêm tin nhắn nhanh."""
    _LOGGER.debug("Dịch vụ async_add_quick_message được gọi với: %s", call.data)
    try:
        add_payload = {
            "keyword": call.data["keyword"],
            "title": call.data["title"],
            "message": {
                "title": call.data["title"],
                "params": ""
            }
        }
        payload = {
            "accountSelection": call.data["account_selection"],
            "addPayload": add_payload
        }
        _LOGGER.debug("Gửi payload đến addQuickMessageByAccount: %s", payload)
        url = f"{zalo_server}/api/addQuickMessageByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi thêm tin nhắn nhanh: %s", resp.text)
        await show_result_notification(hass, "thêm tin nhắn nhanh", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_add_quick_message: %s", e)
        await show_result_notification(hass, "thêm tin nhắn nhanh", None, error=e)
        return {"error": str(e)}

async def async_get_quick_message_service(hass, call, zalo_login):
    """Lấy danh sách tin nhắn nhanh."""
    _LOGGER.debug("Dịch vụ async_get_quick_message được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        _LOGGER.debug("Gửi payload đến getQuickMessageListByAccount: %s", payload)
        url = f"{zalo_server}/api/getQuickMessageListByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)

        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách tin nhắn nhanh: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách tin nhắn nhanh", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_quick_message: %s", e)
        await show_result_notification(hass, "lấy danh sách tin nhắn nhanh", None, error=e)
        return {"error": str(e)}

async def async_remove_quick_message_service(hass, call, zalo_login):
    """Xóa tin nhắn nhanh."""
    _LOGGER.debug("Dịch vụ async_remove_quick_message được gọi với: %s", call.data)
    try:
        item_ids = [int(item_id.strip()) for item_id in call.data["item_ids"].split(',')]
        payload = {
            "accountSelection": call.data["account_selection"],
            "itemIds": item_ids if len(item_ids) > 1 else item_ids[0]
        }
        _LOGGER.debug("Gửi payload đến removeQuickMessageByAccount: %s", payload)
        url = f"{zalo_server}/api/removeQuickMessageByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi xóa tin nhắn nhanh: %s", resp.text)
        await show_result_notification(hass, "xóa tin nhắn nhanh", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_quick_message: %s", e)
        await show_result_notification(hass, "xóa tin nhắn nhanh", None, error=e)
        return {"error": str(e)}

async def async_update_quick_message_service(hass, call, zalo_login):
    """Cập nhật tin nhắn nhanh."""
    _LOGGER.debug("Dịch vụ async_update_quick_message được gọi với: %s", call.data)
    try:
        update_payload = {
            "keyword": call.data["keyword"],
            "title": call.data["title"],
            "message": {
                "title": call.data["title"],
                "params": ""
            }
        }
        try:
            item_id = int(call.data["item_id"])
        except ValueError:
            item_id = call.data["item_id"]

        payload = {
            "accountSelection": call.data["account_selection"],
            "itemId": item_id,
            "updatePayload": update_payload
        }
        _LOGGER.debug("Gửi payload đến updateQuickMessageByAccount: %s", payload)
        url = f"{zalo_server}/api/updateQuickMessageByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)

        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi cập nhật tin nhắn nhanh: %s", resp.text)
        await show_result_notification(hass, "cập nhật tin nhắn nhanh", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_update_quick_message: %s", e)
        await show_result_notification(hass, "cập nhật tin nhắn nhanh", None, error=e)
        return {"error": str(e)}
