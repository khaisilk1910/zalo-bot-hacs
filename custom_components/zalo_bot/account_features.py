"""
Tiện ích quản lý tài khoản cho Zalo Bot.
"""
import logging
from .notification import show_result_notification

_LOGGER = logging.getLogger(__name__)

# Biến toàn cục
session = None
zalo_server = None
hass_instance = None

def set_globals(hass, session_instance, zalo_server_instance):
    """Thiết lập biến toàn cục."""
    global session, zalo_server, hass_instance
    session = session_instance
    zalo_server = zalo_server_instance
    hass_instance = hass
    _LOGGER.debug("Đã thiết lập biến toàn cục cho account_features.py")

async def async_get_account_details_service(hass, call, zalo_login):
    """Lấy chi tiết tài khoản Zalo."""
    _LOGGER.debug("Dịch vụ async_get_account_details được gọi với: %s", call.data)
    try:
        own_id = call.data["own_id"]
        resp = await hass.async_add_executor_job(
            lambda: session.get(f"{zalo_server}/api/accounts/{own_id}")
        )
        _LOGGER.debug("Phản hồi lấy chi tiết tài khoản: %s", resp.text)
        await show_result_notification(hass, "lấy chi tiết tài khoản", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_account_details: %s", e)
        await show_result_notification(hass, "lấy chi tiết tài khoản", None, error=e)
        return {"error": str(e)}
    
async def async_get_logged_accounts_service(hass, call, zalo_login):
    """Lấy danh sách tài khoản đã đăng nhập."""
    _LOGGER.debug("Dịch vụ async_get_logged_accounts được gọi với: %s", call.data)
    try:
        resp = await hass.async_add_executor_job(
            lambda: session.get(f"{zalo_server}/api/accounts")
        )
        _LOGGER.debug("Phản hồi lấy danh sách tài khoản: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách tài khoản", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error(
            "Lỗi trong async_get_logged_accounts: %s", e
        )
        await show_result_notification(hass, "lấy danh sách tài khoản", None, error=e)
        return {"error": str(e)}

async def async_get_account_webhooks_service(hass, call, zalo_login):
    """Lấy danh sách webhook của tài khoản."""
    _LOGGER.debug("Dịch vụ async_get_account_webhooks được gọi với: %s", call.data)
    try:
        resp = await hass.async_add_executor_job(
            lambda: session.get(f"{zalo_server}/api/account-webhooks")
        )
        _LOGGER.debug("Phản hồi lấy danh sách webhook: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách webhook", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_account_webhooks: %s", e)
        await show_result_notification(hass, "lấy danh sách webhook", None, error=str(e))
        return {"error": str(e)}
    
async def async_get_account_webhook_service(hass, call, zalo_login):
    """Lấy thông tin webhook của tài khoản."""
    _LOGGER.debug("Dịch vụ async_get_account_webhook được gọi với: %s", call.data)
    try:
        own_id = call.data["own_id"]
        resp = await hass.async_add_executor_job(
            lambda: session.get(f"{zalo_server}/api/account-webhook/{own_id}")
        )
        _LOGGER.debug("Phản hồi lấy thông tin webhook: %s", resp.text)
        await show_result_notification(hass, "lấy thông tin webhook", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_account_webhook: %s", e)
        await show_result_notification(
            hass,
            "lấy thông tin webhook",
            None,
            error=e
        )
        return {"error": str(e)}
    
async def async_set_account_webhook_service(hass, call, zalo_login):
    """Cài đặt webhook cho tài khoản."""
    _LOGGER.debug("Dịch vụ async_set_account_webhook được gọi với: %s", call.data)
    try:
        payload = {
            "ownId": call.data["own_id"],
            "messageWebhookUrl": call.data.get("message_webhook_url"),
            "groupEventWebhookUrl": call.data.get("group_event_webhook_url"),
            "reactionWebhookUrl": call.data.get("reaction_webhook_url")
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/account-webhook", json=payload)
        )
        _LOGGER.debug("Phản hồi cài đặt webhook: %s", resp.text)
        await show_result_notification(hass, "cài đặt webhook", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_set_account_webhook: %s", e)
        await show_result_notification(
            hass,
            "cài đặt webhook",
            None,
            error=e
        )
        return {"error": str(e)}
    
async def async_delete_account_webhook_service(hass, call, zalo_login):
    """Xóa webhook của tài khoản."""
    _LOGGER.debug("Dịch vụ async_delete_account_webhook được gọi với: %s", call.data)
    try:
        own_id = call.data["own_id"]
        resp = await hass.async_add_executor_job(
            lambda: session.delete(f"{zalo_server}/api/account-webhook/{own_id}")
        )
        _LOGGER.debug("Phản hồi xóa webhook: %s", resp.text)
        await show_result_notification(hass, "xóa webhook", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_delete_account_webhook: %s", e)
        await show_result_notification(
            hass,
            "xóa webhook",
            None,
            error=e
        )
        return {"error": str(e)}
    
async def async_get_proxies_service(hass, call, zalo_login):
    """Lấy danh sách proxy."""
    _LOGGER.debug("Dịch vụ async_get_proxies được gọi với: %s", call.data)
    try:
        resp = await hass.async_add_executor_job(
            lambda: session.get(f"{zalo_server}/proxies")
        )
        _LOGGER.debug("Phản hồi lấy danh sách proxy: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách proxy", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_proxies: %s", e)
        await show_result_notification(hass, "lấy danh sách proxy", None, error=e)
        return {"error": str(e)}
    
async def async_add_proxy_service(hass, call, zalo_login):
    """Thêm proxy cho tài khoản."""
    _LOGGER.debug("Dịch vụ async_add_proxy được gọi với: %s", call.data)
    try:
        payload = {
            "proxyUrl": call.data["proxy_url"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/proxies", json=payload)
        )
        _LOGGER.debug("Phản hồi thêm proxy: %s", resp.text)
        await show_result_notification(hass, "thêm proxy", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_add_proxy: %s", e)
        await show_result_notification(hass, "thêm proxy", None, error=e)
        return {"error": str(e)}
    
async def async_remove_proxy_service(hass, call, zalo_login):
    """Xóa proxy khỏi tài khoản."""
    _LOGGER.debug("Dịch vụ async_remove_proxy được gọi với: %s", call.data)
    try:
        payload = {
            "proxyUrl": call.data["proxy_url"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.delete(f"{zalo_server}/proxies", json=payload)
        )
        _LOGGER.debug("Phản hồi xóa proxy: %s", resp.text)
        await show_result_notification(hass, "xóa proxy", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
        
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_proxy: %s", e)
        await show_result_notification(hass, "xóa proxy", None, error=e)
        return {"error": str(e)}
