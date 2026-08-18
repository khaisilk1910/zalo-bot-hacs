"""Các tính năng khác và tiện ích cho Zalo Bot."""
import logging
from .notification import show_result_notification
from .helpers import normalize_thread_type

_LOGGER = logging.getLogger(__name__)

session = None
zalo_server = None

def set_globals(sess, server):
    """Cập nhật các biến toàn cục."""
    global session, zalo_server
    session = sess
    zalo_server = server

async def async_undo_message_service(hass, call, zalo_login):
    """Thu hồi tin nhắn đã gửi."""
    _LOGGER.debug("Dịch vụ async_undo_message được gọi với: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        payload = {
            "payload": {
                "msgId": call.data["msg_id"],
                "cliMsgId": call.data["cli_msg_id"],
            },
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": normalize_thread_type(msg_type),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/undoByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi thu hồi tin nhắn: %s", resp.text)
        await show_result_notification(hass, "thu hồi tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_undo_message: %s", e)
        await show_result_notification(hass, "thu hồi tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_create_reminder_service(hass, call, zalo_login):
    """Tạo lời nhắc."""
    _LOGGER.debug("Dịch vụ async_create_reminder được gọi với: %s", call.data)
    try:
        start_time = int(call.data["remind_time"])
        if start_time <= 0:
            raise ValueError("remind_time phải là timestamp mili-giây dương")
        payload = {
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": normalize_thread_type(call.data.get("type", "0")),
            "options": {
                "title": call.data["title"],
                "startTime": start_time,
            },
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/createReminderByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi tạo lời nhắc: %s", resp.text)
        await show_result_notification(hass, "tạo lời nhắc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_create_reminder: %s", e)
        await show_result_notification(hass, "tạo lời nhắc", None, error=e)
        return {"error": str(e)}

async def async_remove_reminder_service(hass, call, zalo_login):
    """Xóa lời nhắc."""
    _LOGGER.debug("Dịch vụ async_remove_reminder được gọi với: %s", call.data)
    try:
        payload = {
            "reminderId": call.data["reminder_id"],
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": normalize_thread_type(call.data.get("type", "0"))
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/removeReminderByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi xóa lời nhắc: %s", resp.text)
        await show_result_notification(hass, "xóa lời nhắc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_reminder: %s", e)
        await show_result_notification(hass, "xóa lời nhắc", None, error=e)
        return {"error": str(e)}

async def async_update_settings_service(hass, call, zalo_login):
    """Cập nhật cài đặt."""
    _LOGGER.debug("Dịch vụ async_update_settings được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "type": call.data["setting_type"],
            "status": int(call.data["status"])
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/updateSettingsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi cập nhật cài đặt: %s", resp.text)
        await show_result_notification(hass, "cập nhật cài đặt", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_update_settings: %s", e)
        await show_result_notification(hass, "cập nhật cài đặt", None, error=e)
        return {"error": str(e)}

async def async_set_mute_service(hass, call, zalo_login):
    """Thiết lập trạng thái tắt thông báo."""
    _LOGGER.debug("Dịch vụ async_set_mute được gọi với: %s", call.data)
    try:
        duration = int(call.data.get("duration", 0))
        # zca-js 2.1.2 uses MuteAction.MUTE=1 and MuteAction.UNMUTE=3.
        # Preserve the service UI convention: 0=unmute, -1=mute forever.
        if duration == 0:
            action = 3
            zca_duration = -1
        elif duration == -1 or duration > 0:
            action = 1
            zca_duration = duration
        else:
            raise ValueError("duration không hợp lệ; dùng 0, -1 hoặc số giây dương")
        mute_type = call.data.get("type", "0")
        mute_type_num = normalize_thread_type(mute_type)
        payload = {
            "params": {
                "action": action,
                "duration": zca_duration,
            },
            "threadID": call.data["thread_id"],
            "type": mute_type_num,
            "accountSelection": call.data["account_selection"]
        }
        _LOGGER.debug("Gửi payload đến setMuteByAccount: %s", payload)
        url = f"{zalo_server}/api/setMuteByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi cài đặt tắt thông báo: %s", resp.text)
        await show_result_notification(hass, "cài đặt tắt thông báo", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_set_mute: %s", e)
        await show_result_notification(hass, "cài đặt tắt thông báo", None, error=e)
        return {"error": str(e)}

async def async_set_pinned_conversation_service(hass, call, zalo_login):
    """Thiết lập ghim cuộc trò chuyện."""
    _LOGGER.debug("Dịch vụ async_set_pinned_conversation được gọi với: %s", call.data)
    try:
        pinned_str = str(call.data.get("pinned", "true")).lower()
        pinned = pinned_str == "true" or pinned_str == "1" or pinned_str == "yes"
        conv_type = call.data.get("type", "0")
        conv_type_num = normalize_thread_type(conv_type)
        payload = {
            "accountSelection": call.data["account_selection"],
            "pinned": pinned,
            "threadId": call.data["thread_id"],
            "type": conv_type_num
        }
        _LOGGER.debug("Gửi payload đến setPinnedConversationsByAccount: %s", payload)
        url = f"{zalo_server}/api/setPinnedConversationsByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi ghim/bỏ ghim cuộc trò chuyện: %s", resp.text)
        await show_result_notification(hass, "ghim/bỏ ghim cuộc trò chuyện", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_set_pinned_conversation: %s", e)
        await show_result_notification(hass, "ghim/bỏ ghim cuộc trò chuyện", None, error=e)
        return {"error": str(e)}

async def async_get_unread_mark_service(hass, call, zalo_login):
    """Lấy danh sách cuộc trò chuyện chưa đọc."""
    _LOGGER.debug("Dịch vụ async_get_unread_mark được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getUnreadMarkByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách cuộc trò chuyện chưa đọc: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện chưa đọc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_unread_mark: %s", e)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện chưa đọc", None, error=e)
        return {"error": str(e)}

async def async_add_unread_mark_service(hass, call, zalo_login):
    """Đánh dấu cuộc trò chuyện chưa đọc."""
    _LOGGER.debug("Dịch vụ async_add_unread_mark được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/addUnreadMarkByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi đánh dấu chưa đọc: %s", resp.text)
        await show_result_notification(hass, "đánh dấu chưa đọc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_add_unread_mark: %s", e)
        await show_result_notification(hass, "đánh dấu chưa đọc", None, error=e)
        return {"error": str(e)}

async def async_remove_unread_mark_service(hass, call, zalo_login):
    """Bỏ đánh dấu chưa đọc cho cuộc trò chuyện."""
    _LOGGER.debug("Dịch vụ async_remove_unread_mark được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/removeUnreadMarkByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi bỏ đánh dấu chưa đọc: %s", resp.text)
        await show_result_notification(hass, "bỏ đánh dấu chưa đọc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_remove_unread_mark: %s", e)
        await show_result_notification(hass, "bỏ đánh dấu chưa đọc", None, error=e)
        return {"error": str(e)}

async def async_delete_chat_service(hass, call, zalo_login):
    """Xóa cuộc trò chuyện."""
    _LOGGER.debug("Dịch vụ async_delete_chat được gọi với: %s", call.data)
    try:
        raw_last_message = call.data["last_message"]
        owner_id = raw_last_message.get("ownerId") or raw_last_message.get("uidFrom")
        cli_msg_id = raw_last_message.get("cliMsgId")
        global_msg_id = raw_last_message.get("globalMsgId") or raw_last_message.get("msgId")
        missing = [
            name
            for name, value in (
                ("ownerId/uidFrom", owner_id),
                ("cliMsgId", cli_msg_id),
                ("globalMsgId/msgId", global_msg_id),
            )
            if value in (None, "")
        ]
        if missing:
            raise ValueError(
                "last_message thiếu trường bắt buộc: " + ", ".join(missing)
            )

        payload = {
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "lastMessage": {
                "ownerId": str(owner_id),
                "cliMsgId": str(cli_msg_id),
                "globalMsgId": str(global_msg_id),
            },
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/deleteChatByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi xóa cuộc trò chuyện: %s", resp.text)
        await show_result_notification(hass, "xóa cuộc trò chuyện", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_delete_chat: %s", e)
        await show_result_notification(hass, "xóa cuộc trò chuyện", None, error=e)
        return {"error": str(e)}

async def async_get_archived_chat_list_service(hass, call, zalo_login):
    """Lấy danh sách cuộc trò chuyện đã lưu trữ."""
    _LOGGER.debug("Dịch vụ async_get_archived_chat_list được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getArchivedChatListByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách cuộc trò chuyện lưu trữ: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện lưu trữ", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_archived_chat_list: %s", e)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện lưu trữ", None, error=e)
        return {"error": str(e)}

async def async_get_auto_delete_chat_service(hass, call, zalo_login):
    """Lấy cài đặt tự động xóa cuộc trò chuyện."""
    _LOGGER.debug("Dịch vụ async_get_auto_delete_chat được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getAutoDeleteChatByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách tự động xóa tin nhắn: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách tự động xóa tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_auto_delete_chat: %s", e)
        await show_result_notification(hass, "lấy danh sách tự động xóa tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_update_auto_delete_chat_service(hass, call, zalo_login):
    """Cập nhật tự động xóa tin nhắn."""
    _LOGGER.debug("Dịch vụ async_update_auto_delete_chat được gọi với: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        payload = {
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "ttl": call.data["ttl"],
            "type": normalize_thread_type(msg_type),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/updateAutoDeleteChatByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi cập nhật tự động xóa tin nhắn: %s", resp.text)
        await show_result_notification(hass, "cập nhật tự động xóa tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_update_auto_delete_chat: %s", e)
        await show_result_notification(hass, "cập nhật tự động xóa tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_get_hidden_conversations_service(hass, call, zalo_login):
    """Lấy danh sách cuộc trò chuyện ẩn."""
    _LOGGER.debug("Dịch vụ async_get_hidden_conversations được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getHiddenConversationsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách cuộc trò chuyện ẩn: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện ẩn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_hidden_conversations: %s", e)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện ẩn", None, error=e)
        return {"error": str(e)}

async def async_set_hidden_conversations_service(hass, call, zalo_login):
    """Thiết lập trạng thái ẩn cho cuộc trò chuyện."""
    _LOGGER.debug("Dịch vụ async_set_hidden_conversations được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "hidden": bool(call.data["hidden"]),
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/setHiddenConversationsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi thiết lập trạng thái ẩn cuộc trò chuyện: %s", resp.text)
        await show_result_notification(hass, "thiết lập trạng thái ẩn cuộc trò chuyện", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_set_hidden_conversations: %s", e)
        await show_result_notification(hass, "thiết lập trạng thái ẩn cuộc trò chuyện", None, error=e)
        return {"error": str(e)}

async def async_update_hidden_convers_pin_service(hass, call, zalo_login):
    """Cập nhật mã PIN cho cuộc trò chuyện ẩn."""
    _LOGGER.debug("Dịch vụ async_update_hidden_convers_pin được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "pin": call.data["pin"],
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/updateHiddenConversPinByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi cập nhật mã PIN cuộc trò chuyện ẩn: %s", resp.text)
        await show_result_notification(hass, "cập nhật mã PIN cuộc trò chuyện ẩn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_update_hidden_convers_pin: %s", e)
        await show_result_notification(hass, "cập nhật mã PIN cuộc trò chuyện ẩn", None, error=e)
        return {"error": str(e)}

async def async_reset_hidden_convers_pin_service(hass, call, zalo_login):
    """Đặt lại mã PIN cho cuộc trò chuyện ẩn."""
    _LOGGER.debug("Dịch vụ async_reset_hidden_convers_pin được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/resetHiddenConversPinByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi đặt lại mã PIN cuộc trò chuyện ẩn: %s", resp.text)
        await show_result_notification(hass, "đặt lại mã PIN cuộc trò chuyện ẩn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_reset_hidden_convers_pin: %s", e)
        await show_result_notification(hass, "đặt lại mã PIN cuộc trò chuyện ẩn", None, error=e)
        return {"error": str(e)}

async def async_get_mute_service(hass, call, zalo_login):
    """Lấy danh sách cuộc trò chuyện tắt thông báo."""
    _LOGGER.debug("Dịch vụ async_get_mute được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getMuteByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách cuộc trò chuyện tắt thông báo: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện tắt thông báo", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_mute: %s", e)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện tắt thông báo", None, error=e)
        return {"error": str(e)}

async def async_get_pin_conversations_service(hass, call, zalo_login):
    """Lấy danh sách cuộc trò chuyện ghim."""
    _LOGGER.debug("Dịch vụ async_get_pin_conversations được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getPinConversationsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách cuộc trò chuyện ghim: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện ghim", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_pin_conversations: %s", e)
        await show_result_notification(hass, "lấy danh sách cuộc trò chuyện ghim", None, error=e)
        return {"error": str(e)}

async def async_add_reaction_service(hass, call, zalo_login):
    """Thêm cảm xúc cho tin nhắn."""
    _LOGGER.debug("Dịch vụ async_add_reaction được gọi với: %s", call.data)
    try:
        try:
            msg_id = int(call.data["msg_id"])
            cli_msg_id = int(call.data["cli_msg_id"])
        except ValueError:
            msg_id = call.data["msg_id"]
            cli_msg_id = call.data["cli_msg_id"]
        reaction_type = normalize_thread_type(call.data["type"])
        reaction_icon = call.data["icon"].lower()
        reaction_map = {
            "like": "/-strong",
            "heart": "/-heart",
            "haha": ":>",
            "wow": ":o",
            "cry": ":-((",
            "angry": ":-h",
            "kiss": ":-*",
            "tears_of_joy": ":')",
            "shit": "/-shit",
            "rose": "/-rose",
            "broken_heart": "/-break",
            "dislike": "/-weak",
            "love": ";xx",
            "confused": ";-/",
            "wink": ";-)",
            "fade": "/-fade",
            "sun": "/-li",
            "birthday": "/-bd",
            "bomb": "/-bome",
            "ok": "/-ok",
            "peace": "/-v",
            "thanks": "/-thanks",
            "punch": "/-punch",
            "share": "/-share",
            "pray": "_()_",
            "no": "/-no",
            "bad": "/-bad",
            "love_you": "/-loveu",
            "sad": "--b"
        }
        icon_value = reaction_map.get(reaction_icon, reaction_icon)
        payload = {
            "accountSelection": call.data["account_selection"],
            "icon": icon_value,
            "dest": {
                "threadId": call.data["thread_id"],
                "type": reaction_type,
                "data": {
                    "msgId": msg_id,
                    "cliMsgId": cli_msg_id
                }
            }
        }
        _LOGGER.debug("Gửi payload đến addReactionByAccount: %s", payload)
        url = f"{zalo_server}/api/addReactionByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi thêm cảm xúc: %s", resp.text)
        if resp.status_code != 200:
            _LOGGER.error("Lỗi HTTP khi gọi addReactionByAccount: %s - %s", resp.status_code, resp.reason)
        await show_result_notification(hass, "thêm cảm xúc", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_add_reaction: %s", e)
        await show_result_notification(hass, "thêm cảm xúc", None, error=e)
        return {"error": str(e)}

async def async_delete_message_service(hass, call, zalo_login):
    """Xóa tin nhắn."""
    _LOGGER.debug("Dịch vụ async_delete_message được gọi với: %s", call.data)
    try:
        message_type = normalize_thread_type(call.data["type"])
        payload = {
            "accountSelection": call.data["account_selection"],
            "dest": {
                "threadId": call.data["thread_id"],
                "type": message_type,
                "data": {
                    "msgId": call.data["msg_id"],
                    "cliMsgId": call.data["cli_msg_id"],
                    "uidFrom": call.data["uid_from"]
                }
            },
            "onlyMe": call.data.get("only_me", True)
        }
        url = f"{zalo_server}/api/deleteMessageByAccount"
        _LOGGER.debug("Gửi payload đến deleteMessageByAccount: %s", payload)
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi xóa tin nhắn: %s", resp.text)
        await show_result_notification(hass, "xóa tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_delete_message: %s", e)
        await show_result_notification(hass, "xóa tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_forward_message_service(hass, call, zalo_login):
    """Chuyển tiếp tin nhắn."""
    _LOGGER.debug("Dịch vụ async_forward_message được gọi với: %s", call.data)
    try:
        thread_ids = [
            tid.strip()
            for tid in call.data["thread_ids"].split(",")
            if tid.strip()
        ]
        if not thread_ids:
            raise ValueError("thread_ids phải chứa ít nhất một ID đích")
        msg_type = call.data.get("type", "0")
        msg_type_num = normalize_thread_type(msg_type)
        payload = {
            "accountSelection": call.data["account_selection"],
            "params": {"message": call.data["message"]},
            "threadIds": thread_ids,
            "type": msg_type_num,
        }
        _LOGGER.debug("Gửi payload đến forwardMessageByAccount: %s", payload)
        url = f"{zalo_server}/api/forwardMessageByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
        )
        _LOGGER.debug("Phản hồi chuyển tiếp tin nhắn: %s", resp.text)
        await show_result_notification(hass, "chuyển tiếp tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error("Lỗi trong async_forward_message: %s", e)
        await show_result_notification(hass, "chuyển tiếp tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_parse_link_service(hass, call, zalo_login):
    """Phân tích liên kết."""
    _LOGGER.debug("Dịch vụ async_parse_link được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "link": call.data["link"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/parseLinkByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi phân tích link: %s", resp.text)
        await show_result_notification(hass, "phân tích link", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_parse_link: %s", e)
        await show_result_notification(hass, "phân tích link", None, error=e)
        return {"error": str(e)}

async def async_send_card_service(hass, call, zalo_login):
    """Gửi danh thiếp."""
    _LOGGER.debug("Dịch vụ async_send_card được gọi với: %s", call.data)
    try:
        payload = {
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "options": {"userId": call.data["user_id"]},
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendCardByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi danh thiếp: %s", resp.text)
        await show_result_notification(hass, "gửi danh thiếp", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_card: %s", e)
        await show_result_notification(hass, "gửi danh thiếp", None, error=e)
        return {"error": str(e)}

async def async_send_link_service(hass, call, zalo_login):
    """Gửi liên kết."""
    _LOGGER.debug("Dịch vụ async_send_link được gọi với: %s", call.data)
    try:
        options = {
            "link": call.data["link"],
            "msg": call.data.get("message", "")
        }

        if call.data.get("thumbnail"):
            options["thumbnail"] = call.data["thumbnail"]

        payload = {
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "options": options,
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendLinkByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi link: %s", resp.text)
        await show_result_notification(hass, "gửi link", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_link: %s", e)
        await show_result_notification(hass, "gửi link", None, error=e)
        return {"error": str(e)}

async def async_get_labels_service(hass, call, zalo_login):
    """Lấy danh sách nhãn."""
    _LOGGER.debug("Dịch vụ async_get_labels được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/getLabelsByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi lấy danh sách nhãn: %s", resp.text)
        await show_result_notification(hass, "lấy danh sách nhãn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_get_labels: %s", e)
        await show_result_notification(hass, "lấy danh sách nhãn", None, error=e)
        return {"error": str(e)}

async def async_block_view_feed_service(hass, call, zalo_login):
    """Chặn/bỏ chặn xem nhật ký."""
    _LOGGER.debug("Dịch vụ async_block_view_feed được gọi với: %s", call.data)
    try:
        is_block_str = str(call.data["is_block_feed"]).lower()
        is_block = is_block_str == "true" or is_block_str == "1" or is_block_str == "yes"
        payload = {
            "accountSelection": call.data["account_selection"],
            "userId": call.data["user_id"],
            "isBlockFeed": is_block
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/blockViewFeedByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi chặn/bỏ chặn xem nhật ký: %s", resp.text)
        await show_result_notification(hass, "chặn/bỏ chặn xem nhật ký", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_block_view_feed: %s", e)
        await show_result_notification(hass, "chặn/bỏ chặn xem nhật ký", None, error=e)
        return {"error": str(e)}

async def async_change_account_avatar_service(hass, call, zalo_login):
    """Thay đổi ảnh đại diện tài khoản."""
    _LOGGER.debug("Dịch vụ async_change_account_avatar được gọi với: %s", call.data)
    try:
        payload = {
            "accountSelection": call.data["account_selection"],
            "avatarSource": call.data["avatar_source"]
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/changeAccountAvatarByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi thay đổi ảnh đại diện: %s", resp.text)
        await show_result_notification(hass, "thay đổi ảnh đại diện", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_change_account_avatar: %s", e)
        await show_result_notification(hass, "thay đổi ảnh đại diện", None, error=e)
        return {"error": str(e)}
