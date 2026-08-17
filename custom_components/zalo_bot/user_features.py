"""
Tiện ích quản lý người dùng cho Zalo Bot.
"""
import logging
from .notification import show_result_notification

_LOGGER = logging.getLogger(__name__)

hass = None
session = None
zalo_server = None

def set_globals(hass_instance, session_instance, zalo_server_instance):
    """Thiết lập biến toàn cục cho module."""
    global hass, session, zalo_server
    hass = hass_instance
    session = session_instance
    zalo_server = zalo_server_instance

async def async_find_user_service(hass, call, zalo_login):
    """Dịch vụ tìm kiếm người dùng trên Zalo."""
    _LOGGER.debug("Dịch vụ async_find_user được gọi với: %s", call.data)
    try:
        payload = {
            "phone": call.data["phone"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/findUserByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi tìm người dùng: %s", resp.text)
        await show_result_notification(hass, "tìm người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_find_user: %s", e)
        await show_result_notification(hass, "tìm người dùng", None, error=e)
        return {"error": str(e)}

async def async_get_user_info_service(hass, call, zalo_login):
    """Dịch vụ lấy thông tin người dùng trên Zalo."""
    _LOGGER.debug("Dịch vụ async_get_user_info được gọi với: %s", call.data)
    try:
        payload = {
            "userId": call.data["user_id"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getUserInfoByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy thông tin người dùng: %s", resp.text)
        await show_result_notification(hass, "lấy thông tin người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_user_info: %s", e)
        await show_result_notification(hass, "lấy thông tin người dùng", None, error=e)
        return {"error": str(e)}

async def async_send_friend_request_service(hass, call, zalo_login):
    """Dịch vụ gửi lời mời kết bạn trên Zalo."""
    _LOGGER.debug("Dịch vụ async_send_friend_request được gọi với: %s", call.data)
    try:
        payload = {
            "userId": call.data["user_id"],
            "message": call.data["message"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendFriendRequestByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi lời mời kết bạn: %s", resp.text)
        await show_result_notification(hass, "gửi lời mời kết bạn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_friend_request: %s", e)
        await show_result_notification(hass, "gửi lời mời kết bạn", None, error=e)
        return {"error": str(e)}

async def async_accept_friend_request_service(hass, call, zalo_login):
    """Dịch vụ chấp nhận lời mời kết bạn trên Zalo."""
    _LOGGER.debug("Dịch vụ async_accept_friend_request được gọi với: %s", call.data)
    try:
        payload = {
            "userId": call.data["user_id"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/acceptFriendRequestByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi chấp nhận lời mời kết bạn: %s", resp.text)
        await show_result_notification(hass, "chấp nhận lời mời kết bạn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_accept_friend_request: %s", e)
        await show_result_notification(hass, "chấp nhận lời mời kết bạn", None, error=e)
        return {"error": str(e)}

async def async_block_user_service(hass, call, zalo_login):
    """Dịch vụ chặn người dùng trên Zalo."""
    _LOGGER.debug("Dịch vụ async_block_user được gọi với: %s", call.data)
    try:
        payload = {
            "userId": call.data["user_id"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/blockUserByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi chặn người dùng: %s", resp.text)
        await show_result_notification(hass, "chặn người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_block_user: %s", e)
        await show_result_notification(hass, "chặn người dùng", None, error=e)
        return {"error": str(e)}

async def async_unblock_user_service(hass, call, zalo_login):
    """Dịch vụ bỏ chặn người dùng trên Zalo."""
    _LOGGER.debug("Dịch vụ async_unblock_user được gọi với: %s", call.data)
    try:
        payload = {
            "userId": call.data["user_id"],
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/unblockUserByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi bỏ chặn người dùng: %s", resp.text)
        await show_result_notification(hass, "bỏ chặn người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_unblock_user: %s", e)
        await show_result_notification(hass, "bỏ chặn người dùng", None, error=e)
        return {"error": str(e)}

async def async_get_all_friends_service(hass, call, zalo_login):
    """Dịch vụ lấy danh sách bạn bè trên Zalo."""
    _LOGGER.debug("Dịch vụ async_get_all_friends được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getAllFriendsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách bạn bè: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách bạn bè", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_all_friends: %s", e)
        await show_result_notification(hass, "lấy danh sách bạn bè", None, error=e)
        return {"error": str(e)}


async def async_get_received_friend_requests_service(hass, call, zalo_login):
    """Dịch vụ lấy danh sách lời mời kết bạn đã nhận trên Zalo."""
    _LOGGER.debug("Dịch vụ async_get_received_friend_requests được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getReceivedFriendRequestsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy lời mời kết bạn đã nhận: %s", resp.text)
        await show_result_notification(hass, "lấy lời mời kết bạn đã nhận", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_received_friend_requests: %s", e)
        await show_result_notification(hass, "lấy lời mời kết bạn đã nhận", None, error=e)
        return {"error": str(e)}

async def async_get_sent_friend_requests_service(hass, call, zalo_login):
    """Dịch vụ lấy danh sách lời mời kết bạn đã gửi trên Zalo."""
    _LOGGER.debug("Dịch vụ async_get_sent_friend_requests được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getSentFriendRequestByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy lời mời kết bạn đã gửi: %s", resp.text)
        await show_result_notification(hass, "lấy lời mời kết bạn đã gửi", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_sent_friend_requests: %s", e)
        await show_result_notification(hass, "lấy lời mời kết bạn đã gửi", None, error=e)
        return {"error": str(e)}

async def async_undo_friend_request_service(hass, call, zalo_login):
    """Dịch vụ thu hồi lời mời kết bạn trên Zalo."""
    _LOGGER.debug("Dịch vụ async_undo_friend_request được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "friendId": call.data["friend_id"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/undoFriendRequestByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi thu hồi lời mời kết bạn: %s", resp.text)
        await show_result_notification(hass, "thu hồi lời mời kết bạn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_undo_friend_request: %s", e)
        await show_result_notification(hass, "thu hồi lời mời kết bạn", None, error=e)
        return {"error": str(e)}

async def async_remove_friend_service(hass, call, zalo_login):
    """Dịch vụ hủy kết bạn trên Zalo."""
    _LOGGER.debug("Dịch vụ async_remove_friend được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "friendId": call.data["friend_id"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/removeFriendByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi hủy kết bạn: %s", resp.text)
        await show_result_notification(hass, "hủy kết bạn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_friend: %s", e)
        await show_result_notification(hass, "hủy kết bạn", None, error=e)
        return {"error": str(e)}

async def async_change_friend_alias_service(hass, call, zalo_login):
    """Dịch vụ đổi biệt danh bạn bè trên Zalo."""
    _LOGGER.debug("Dịch vụ async_change_friend_alias được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "friendId": call.data["friend_id"],
            "alias": call.data["alias"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/changeFriendAliasByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi đổi biệt danh bạn bè: %s", resp.text)
        await show_result_notification(hass, "đổi biệt danh bạn bè", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_change_friend_alias: %s", e)
        await show_result_notification(hass, "đổi biệt danh bạn bè", None, error=e)
        return {"error": str(e)}

async def async_remove_friend_alias_service(hass, call, zalo_login):
    """Dịch vụ xóa biệt danh bạn bè trên Zalo."""
    _LOGGER.debug("Dịch vụ async_remove_friend_alias được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "friendId": call.data["friend_id"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/removeFriendAliasByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi xóa biệt danh bạn bè: %s", resp.text)
        await show_result_notification(hass, "xóa biệt danh bạn bè", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_friend_alias: %s", e)
        await show_result_notification(hass, "xóa biệt danh bạn bè", None, error=e)
        return {"error": str(e)}

async def async_update_profile_service(hass, call, zalo_login):
    """Dịch vụ cập nhật thông tin cá nhân trên Zalo."""
    _LOGGER.debug("Dịch vụ async_update_profile được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        if "name" in call.data:
            payload["name"] = call.data["name"]
        if "dob" in call.data:
            payload["dob"] = call.data["dob"]
        if "gender" in call.data:
            payload["gender"] = int(call.data["gender"])

        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/updateProfileByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi cập nhật thông tin cá nhân: %s", resp.text)
        await show_result_notification(hass, "cập nhật thông tin cá nhân", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_update_profile: %s", e)
        await show_result_notification(hass, "cập nhật thông tin cá nhân", None, error=e)
        return {"error": str(e)}

async def async_get_avatar_list_service(hass, call, zalo_login):
    """Dịch vụ lấy danh sách ảnh đại diện."""
    _LOGGER.debug("Dịch vụ async_get_avatar_list được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        if "count" in call.data:
            try:
                payload["count"] = int(call.data["count"])
            except ValueError:
                payload["count"] = call.data["count"]
        if "page" in call.data:
            try:
                payload["page"] = int(call.data["page"])
            except ValueError:
                payload["page"] = call.data["page"]
        _LOGGER.debug("Gửi payload đến getAvatarListByAccount: %s", payload)
        url = f"{zalo_server}/api/getAvatarListByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách ảnh đại diện: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách ảnh đại diện", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_avatar_list: %s", e)
        await show_result_notification(hass, "lấy danh sách ảnh đại diện", None, error=e)
        return {"error": str(e)}

async def async_last_online_service(hass, call, zalo_login):
    """Dịch vụ xem thời gian hoạt động cuối của người dùng."""
    _LOGGER.debug("Dịch vụ async_last_online được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "userId": call.data["user_id"] 
        }
        _LOGGER.debug("Gửi payload đến lastOnlineByAccount: %s", payload)
        url = f"{zalo_server}/api/lastOnlineByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)

        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi xem thời gian hoạt động cuối: %s", resp.text)
        await show_result_notification(hass, "xem thời gian hoạt động cuối", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_last_online: %s", e)
        await show_result_notification(hass, "xem thời gian hoạt động cuối", None, error=e)
        return {"error": str(e)}
