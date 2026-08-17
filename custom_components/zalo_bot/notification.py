"""Các tiện ích xử lý thông báo."""
import logging
import re

_LOGGER = logging.getLogger(__name__)


def _notification_id(service_name: str, suffix: str = "result") -> str:
    """Return a stable notification id so repeated actions replace old results."""
    slug = re.sub(r"[^a-z0-9]+", "_", service_name.lower()).strip("_") or "action"
    return f"zalo_bot_{slug}_{suffix}"


async def show_result_notification(hass, service_name, resp, error=None):
    """
    Hiển thị kết quả từ server trong UI thông qua persistent_notification.
    
    :param hass: Home Assistant instance
    :param service_name: Tên dịch vụ đang thực hiện
    :param resp: Phản hồi từ server
    :param error: Lỗi nếu có
    """
    try:
        # Kiểm tra xem thông báo có được bật không
        from .const import CONF_ENABLE_NOTIFICATIONS, DOMAIN
        
        notifications_enabled = True
        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            if isinstance(entry_data, dict) and CONF_ENABLE_NOTIFICATIONS in entry_data:
                notifications_enabled = entry_data[CONF_ENABLE_NOTIFICATIONS]
                break

        # Nếu thông báo bị tắt, chỉ ghi log và không hiển thị thông báo
        if not notifications_enabled:
            if error:
                _LOGGER.debug(f"Thông báo bị tắt. Lỗi khi thực hiện {service_name}: {str(error)}")
            elif resp:
                _LOGGER.info(
                    f"Thông báo bị tắt. Kết quả {service_name}: "
                    f"{resp.text if hasattr(resp, 'text') else str(resp)}"
                )
            return

        if error:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Lỗi khi thực hiện {service_name}: {str(error)}",
                    "title": f"Zalo Bot - Lỗi {service_name}",
                    "notification_id": _notification_id(service_name, "error")
                }
            )
            return

        try:
            resp_json = resp.json()
            success = resp_json.get("success", False)

            # Lấy thông tin chi tiết từ kết quả API
            message = resp_json.get("message", "")
            data = resp_json.get("data", {})

            # Nếu có dữ liệu và không có message, tạo thông tin chi tiết hơn
            if success and data:
                details = []

                # Thông tin người dùng
                if "display_name" in data:
                    details.append(f"Tên: {data.get('display_name', '')}")
                if "zalo_name" in data:
                    details.append(f"Zalo Name: {data.get('zalo_name', '')}")
                if "uid" in data:
                    details.append(f"UID: {data.get('uid', '')}")
                if "gender" in data:
                    gender = "Nam" if data.get("gender") == 1 else "Nữ" if data.get("gender") == 2 else "Không xác định"
                    details.append(f"Giới tính: {gender}")
                if "sdob" in data:
                    details.append(f"Ngày sinh: {data.get('sdob', '')}")

                # Thông tin tài khoản sử dụng
                if "usedAccount" in resp_json and isinstance(resp_json["usedAccount"], dict):
                    acc = resp_json["usedAccount"]
                    if "phoneNumber" in acc:
                        details.append(f"SĐT Bot: {acc.get('phoneNumber', '')}")
                    if "ownId" in acc:
                        details.append(f"ID Bot: {acc.get('ownId', '')}")

                # Nếu là danh sách
                if not details and isinstance(data, list) and len(data) > 0:
                    details.append(f"Tìm thấy {len(data)} kết quả")

                # Nếu vẫn không có chi tiết cụ thể, thử lấy các giá trị đơn giản
                if not details:
                    count = 0
                    for key, value in data.items():
                        if count < 5 and isinstance(value, (str, int, float, bool)):
                            details.append(f"{key}: {value}")
                            count += 1

                message = "\n".join(details) if details else "Thành công"

            # Nếu vẫn không có message, dùng giá trị mặc định
            if not message:
                message = "Không có thông tin chi tiết"

            if success:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Thực hiện {service_name} thành công!\n\n{message}",
                        "title": f"Zalo Bot - {service_name} thành công",
                        "notification_id": _notification_id(service_name)
                    }
                )
            else:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Thực hiện {service_name} thất bại!\nLỗi: {message}",
                        "title": f"Zalo Bot - {service_name} thất bại",
                        "notification_id": _notification_id(service_name)
                    }
                )
        except Exception as e:
            _LOGGER.error("Lỗi khi tạo thông báo: %s", e)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Lỗi khi hiển thị kết quả: {str(e)}",
                    "title": "Zalo Bot - Lỗi hiển thị",
                    "notification_id": "zalo_bot_notification_error"
                }
            )
    except Exception as e:
        _LOGGER.error("Lỗi trong show_result_notification: %s", e)
