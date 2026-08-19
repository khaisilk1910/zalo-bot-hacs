"""Các tính năng gửi tin nhắn, file, hình ảnh và video cho Zalo Bot."""
import logging
import os
from .const import DOMAIN
from .file_handling import serve_file_temporarily, serve_files_temporarily, copy_to_public, get_video_duration_ms, is_local_zalo_server
from .notification import show_result_notification
from .helpers import normalize_thread_type
from .text_formatting import markdown_to_zalo_styles

_LOGGER = logging.getLogger(__name__)

# Biến toàn cục
session = None
zalo_server = None

def set_globals(sess, server):
    """Cập nhật các biến toàn cục."""
    global session, zalo_server
    session = sess
    zalo_server = server


async def _async_is_file(hass, path):
    """Run filesystem stat checks outside Home Assistant's event loop."""
    return await hass.async_add_executor_job(os.path.isfile, path)


async def async_send_message_service(hass, call, zalo_login):
    """Dịch vụ gửi tin nhắn văn bản."""
    _LOGGER.debug("Dịch vụ async_send_message_service được gọi với dữ liệu: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        quote_in = call.data.get("quote")
        quote = None
        if isinstance(quote_in, dict):
            import time, json as _json
            q = dict(quote_in)
            content = q.get("content") or q.get("attach")
            if isinstance(content, dict):
                content = dict(content)
                if "params" in content and not isinstance(content["params"], str):
                    try:
                        content["params"] = _json.dumps(content["params"])
                    except Exception:
                        content["params"] = str(content["params"])
            msg_type_quote = q.get("msgType") or q.get("msg_type")
            uid_from = q.get("uidFrom") or q.get("uid_from")
            cli_msg_id = q.get("cliMsgId") or str(int(time.time() * 1000))
            if content and uid_from:
                quote = {
                    "content": content,
                    "uidFrom": str(uid_from),
                    "cliMsgId": str(cli_msg_id)
                }
                if msg_type_quote:
                    quote["msgType"] = msg_type_quote

        raw_message = call.data["message"]

        # Read markdown config from HA entities
        enabled = hass.data.get(DOMAIN, {}).get("markdown_enabled", True)
        color = hass.data.get(DOMAIN, {}).get("markdown_color", "none")

        _LOGGER.debug("[send_message] RAW message (len=%d) markdown=%s color=%s: %s",
                     len(raw_message), enabled, color, raw_message[:500])

        if not enabled:
            parsed = {"msg": raw_message, "styles": []}
        else:
            style = None if color == "none" else color
            # Keep even unusually large formatting jobs off Home Assistant's
            # event loop. The parser is pure CPU/string processing.
            parsed = await hass.async_add_executor_job(
                markdown_to_zalo_styles, raw_message, style
            )

        msg_obj = {
            "msg": parsed["msg"],
        }
        if parsed["styles"]:
            msg_obj["styles"] = parsed["styles"]
            _LOGGER.debug("[send_message] Including %d styles in payload", len(parsed["styles"]))
        else:
            _LOGGER.debug("[send_message] No styles detected, sending plain text")
        if quote:
            msg_obj["quote"] = quote

        payload = {
            "message": msg_obj,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "type": normalize_thread_type(msg_type)
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        _LOGGER.debug("[send_message] PAYLOAD message keys: %s", list(msg_obj.keys()))
        _LOGGER.debug("[send_message] PAYLOAD threadId=%s type=%s accountSelection=%s",
                     payload["threadId"], payload["type"], payload["accountSelection"])
        _LOGGER.debug("Gửi POST đến %s/api/sendMessageByAccount với payload: %s",
                    zalo_server, payload)
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendMessageByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi tin nhắn: %s", resp.text)
        await show_result_notification(hass, "gửi tin nhắn", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error("Exception trong async_send_message_service: %s", e, exc_info=True)
        await show_result_notification(hass, "gửi tin nhắn", None, error=e)
        return {"error": str(e)}

async def async_send_file_service(hass, call, zalo_login):
    """Dịch vụ gửi file."""
    _LOGGER.debug("Dịch vụ async_send_file_service được gọi với dữ liệu: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        file_path = call.data["file_path_or_url"]
        public_url = None
        if file_path.startswith("http://") or file_path.startswith("https://"):
            public_url = file_path
        else:
            if not await _async_is_file(hass, file_path):
                error_msg = f"Không tìm thấy tệp: {file_path}"
                await show_result_notification(hass, "gửi file", None, error=error_msg)
                return {"error": error_msg}
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, file_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy tệp đến thư mục public"
                        await show_result_notification(hass, "gửi file", None, error=error_msg)
                        return {"error": error_msg}
                    if public_url.startswith("/local/"):
                        filename = os.path.basename(file_path)
                        public_url = f"{zalo_server}/{filename}"
                else:
                    _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ tệp: {file_path}")
                    public_url = await hass.async_add_executor_job(
                        serve_file_temporarily, file_path, 90
                    )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý tệp: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi file", None, error=error_msg)
                return {"error": error_msg}
        if not public_url:
            error_msg = "Không thể tạo URL công khai cho tệp."
            await show_result_notification(hass, "gửi file", None, error=error_msg)
            return {"error": error_msg}
        payload = {
            "fileUrl": public_url,
            "message": call.data.get("message", ""),
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "type": normalize_thread_type(msg_type),
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        _LOGGER.debug("Gửi POST đến %s/api/sendFileByAccount với payload: %s",
                    zalo_server, payload)
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendFileByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi file: %s", resp.text)
        await show_result_notification(hass, "gửi file", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Exception trong async_send_file_service: %s", e, exc_info=True)
        await show_result_notification(hass, "gửi file", None, error=e)
        return {"error": str(e)}

async def async_send_image_service(hass, call, zalo_login):
    """Dịch vụ gửi hình ảnh."""
    _LOGGER.debug("Dịch vụ async_send_image_service được gọi với dữ liệu: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        image_path = call.data["image_path"]

        if image_path.startswith("http://") or image_path.startswith("https://"):
            public_url = image_path
        else:
            if not await _async_is_file(hass, image_path):
                error_msg = f"Không tìm thấy tệp ảnh: {image_path}"
                await show_result_notification(hass, "gửi ảnh", None, error=error_msg)
                return {"error": error_msg}
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh", None, error=error_msg)
                        return {"error": error_msg}
                    if public_url.startswith("/local/"):
                        filename = os.path.basename(image_path)
                        public_url = f"{zalo_server}/{filename}"
                else:
                    _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ ảnh: {image_path}")
                    public_url = await hass.async_add_executor_job(
                        serve_file_temporarily, image_path, 90
                    )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý ảnh: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi ảnh", None, error=error_msg)
                return {"error": error_msg}
        payload = {
            "imagePath": public_url,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "type": normalize_thread_type(msg_type),
            "message": call.data.get("message", ""),
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        _LOGGER.debug("Gửi POST đến %s/api/sendImageByAccount với payload: %s",
                    zalo_server, payload)
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendImageByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi ảnh: %s", resp.text)
        await show_result_notification(hass, "gửi ảnh", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Exception trong async_send_image_service: %s", e, exc_info=True)
        await show_result_notification(hass, "gửi ảnh", None, error=e)
        return {"error": str(e)}

async def async_send_video_service(hass, call, zalo_login):
    """Dịch vụ gửi video."""
    _LOGGER.debug("Dịch vụ async_send_video được gọi với: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        video_path = call.data["video_path_or_url"]
        public_url = None
        if video_path.startswith("http://") or video_path.startswith("https://"):
            public_url = video_path
        else:
            if not await _async_is_file(hass, video_path):
                error_msg = f"Không tìm thấy tệp video: {video_path}"
                await show_result_notification(hass, "gửi video", None, error=error_msg)
                return {"error": error_msg}
            try:
                _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ tệp video: {video_path}")
                public_url = await hass.async_add_executor_job(
                    serve_file_temporarily, video_path, 300
                )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý tệp video: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi video", None, error=error_msg)
                return {"error": error_msg}
        if not public_url:
            error_msg = "Không thể tạo URL công khai cho video."
            await show_result_notification(hass, "gửi video", None, error=error_msg)
            return {"error": error_msg}
        thumbnail_url = call.data.get("thumbnail_url", public_url)
        if thumbnail_url and not (thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://")):

            if await _async_is_file(hass, thumbnail_url):
                try:
                    thumbnail_url = await hass.async_add_executor_job(
                        serve_file_temporarily, thumbnail_url, 300
                    )
                except Exception as e:
                    _LOGGER.warning("Không thể xử lý thumbnail file local: %s, dùng URL video làm thumbnail", e)
                    thumbnail_url = public_url
            else:
                _LOGGER.warning("Không tìm thấy thumbnail file: %s, dùng URL video làm thumbnail", thumbnail_url)
                thumbnail_url = public_url

        if video_path.startswith("http://") or video_path.startswith("https://"):
            duration = 10000
        else:
            try:
                duration = await hass.async_add_executor_job(get_video_duration_ms, video_path)
                _LOGGER.debug(f"Auto-detect video duration: {duration}ms từ file {video_path}")
            except Exception as e:
                _LOGGER.warning(f"Không thể auto-detect duration từ {video_path}: {e}, dùng 10000ms")
                duration = 10000
        options = {
            "videoUrl": public_url,
            "thumbnailUrl": thumbnail_url,
            "msg": call.data.get("message", ""),
            "duration": int(duration),
            "width": int(call.data.get("width", 1280)),
            "height": int(call.data.get("height", 720)),
        }
        if "ttl" in call.data:
            options["ttl"] = call.data["ttl"]
        thread_type_num = normalize_thread_type(msg_type)
        payload = {
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "options": options,
            "type": thread_type_num 
        }
        _LOGGER.debug("Video URL để gửi: %s", public_url)
        _LOGGER.debug("Thumbnail URL để gửi: %s", thumbnail_url)
        _LOGGER.debug("Options đầy đủ: %s", options)
        _LOGGER.debug("Gửi payload đến sendVideoByAccount: %s", payload)
        url = f"{zalo_server}/api/sendVideoByAccount"
        _LOGGER.debug("URL đầy đủ: %s", url)
        # Video now goes through download -> Zalo upload -> sendVideo on the backend.
        # Allow enough time for that durable upload while keeping the blocking
        # requests call off Home Assistant's event loop.
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload, timeout=240)
        )
        _LOGGER.debug("Response status: %s", resp.status_code)
        _LOGGER.debug("Response headers: %s", dict(resp.headers))
        _LOGGER.debug("Response text: %s", resp.text)
        try:
            response_json = resp.json()
            _LOGGER.debug("Response JSON: %s", response_json)
            if not response_json.get('success', False):
                error_detail = response_json.get('error', 'Unknown error')
                _LOGGER.error("Backend trả về lỗi: %s", error_detail)
        except Exception as json_error:
            _LOGGER.error("Không thể parse JSON response: %s", json_error)
        await show_result_notification(hass, "gửi video", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_video: %s", e)
        await show_result_notification(hass, "gửi video", None, error=e)
        return {"error": str(e)}

async def async_send_sticker_service(hass, call, zalo_login):
    """Dịch vụ gửi sticker."""
    _LOGGER.debug("Dịch vụ async_send_sticker được gọi với: %s", call.data)
    try:
        msg_type = call.data.get("type", "0")
        sticker_id = int(call.data["sticker_id"])
        sticker = {
            "id": sticker_id,
            "cateId": 526,
            "type": 1
        }
        payload = {
            "accountSelection": str(call.data["account_selection"]),
            "threadId": str(call.data["thread_id"]),
            "sticker": sticker,
            "type": normalize_thread_type(msg_type)
        }
        _LOGGER.debug("Gửi payload đến sendStickerByAccount: %s", payload)
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendStickerByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi sticker: %s", resp.text)
        await show_result_notification(hass, "gửi sticker", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_sticker: %s", e)
        await show_result_notification(hass, "gửi sticker", None, error=e)
        return {"error": str(e)}

async def async_send_voice_service(hass, call, zalo_login):
    """Dịch vụ gửi tin nhắn thoại."""
    _LOGGER.debug("Dịch vụ async_send_voice được gọi với: %s", call.data)
    try:
        voice_path = call.data["voice_path"]
        voice_url = voice_path
        if not voice_path.startswith(("http://", "https://")):
            if await _async_is_file(hass, voice_path):
                voice_url = await hass.async_add_executor_job(
                    serve_file_temporarily, voice_path
                )
            else:
                raise Exception(f"Không tìm thấy file âm thanh: {voice_path}")
        options = {"voiceUrl": voice_url}
        if "ttl" in call.data:
            options["ttl"] = call.data["ttl"]
        payload = {
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "options": options,
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendVoiceByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi tin nhắn thoại: %s", resp.text)
        await show_result_notification(hass, "gửi tin nhắn thoại", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_voice: %s", e)
        await show_result_notification(hass, "gửi tin nhắn thoại", None, error=e)
        return {"error": str(e)}

async def async_send_typing_event_service(hass, call, zalo_login):
    """Dịch vụ gửi thông báo đang nhập tin nhắn."""
    _LOGGER.debug("Dịch vụ async_send_typing_event được gọi với: %s", call.data)
    try:
        payload = {
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
            "type": normalize_thread_type(call.data.get("type", "0")),
        }
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendTypingEventByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi thông báo typing: %s", resp.text)
        await show_result_notification(hass, "gửi thông báo typing", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_typing_event: %s", e)
        await show_result_notification(hass, "gửi thông báo typing", None, error=e)
        return {"error": str(e)}

async def async_send_image_to_user_service(hass, call, zalo_login):
    """Dịch vụ gửi ảnh cho người dùng."""
    _LOGGER.debug("Dịch vụ async_send_image_to_user được gọi với: %s", call.data)
    try:
        image_path = call.data["image_path"]

        if image_path.startswith("http"):
            public_url = image_path
        else:
            if not await _async_is_file(hass, image_path):
                error_msg = f"Không tìm thấy tệp ảnh: {image_path}"
                await show_result_notification(hass, "gửi ảnh cho người dùng", None, error=error_msg)
                return {"error": error_msg}
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh cho người dùng", None, error=error_msg)
                        return {"error": error_msg}
                    if public_url.startswith("/local/"):
                        public_url = f"{zalo_server}{public_url.replace('/local', '')}"
                else:
                    _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ ảnh: {image_path}")
                    public_url = await hass.async_add_executor_job(
                        serve_file_temporarily, image_path, 90  # 90 giây là đủ để gửi
                    )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý ảnh: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi ảnh cho người dùng", None, error=error_msg)
                return {"error": error_msg}
        payload = {
            "imagePath": public_url,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"])
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendImageToUserByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi ảnh cho người dùng: %s", resp.text)
        await show_result_notification(hass, "gửi ảnh cho người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}

    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_image_to_user: %s", e)
        await show_result_notification(hass, "gửi ảnh cho người dùng", None, error=str(e))
        return {"error": str(e)}

async def async_send_image_to_group_service(hass, call, zalo_login):
    """Dịch vụ gửi ảnh cho nhóm."""
    _LOGGER.debug("Dịch vụ async_send_image_to_group được gọi với: %s", call.data)
    try:
        image_path = call.data["image_path"]
        if image_path.startswith("http"):
            public_url = image_path
        else:
            if not await _async_is_file(hass, image_path):
                error_msg = f"Không tìm thấy tệp ảnh: {image_path}"
                await show_result_notification(hass, "gửi ảnh cho nhóm", None, error=error_msg)
                return {"error": error_msg}
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh cho nhóm", None, error=error_msg)
                        return {"error": error_msg}
                    if public_url.startswith("/local/"):
                        public_url = f"{zalo_server}{public_url.replace('/local', '')}"
                else:
                    _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ ảnh: {image_path}")
                    public_url = await hass.async_add_executor_job(
                        serve_file_temporarily, image_path, 90  # 90 giây là đủ để gửi
                    )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý ảnh: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi ảnh cho nhóm", None, error=error_msg)
                return {"error": error_msg}
        payload = {
            "imagePath": public_url,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"])
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendImageToGroupByAccount", json=payload)
        )
        _LOGGER.debug("Phản hồi gửi ảnh cho nhóm: %s", resp.text)
        await show_result_notification(hass, "gửi ảnh cho nhóm", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as e:
        _LOGGER.error("Lỗi trong async_send_image_to_group: %s", e)
        await show_result_notification(hass, "gửi ảnh cho nhóm", None, error=str(e))
        return {"error": str(e)}

async def _prepare_multi_image_urls(hass, image_paths):
    """Prepare multi-image URLs efficiently while preserving input order."""
    items = [item.strip() for item in image_paths if item and item.strip()]
    if not items:
        return []

    is_local_server = is_local_zalo_server(zalo_server)
    if is_local_server:
        result = []
        for image_path in items:
            if image_path.startswith(("http://", "https://")):
                result.append(image_path)
                continue
            if not await _async_is_file(hass, image_path):
                _LOGGER.warning("Không tìm thấy tệp ảnh: %s, bỏ qua", image_path)
                continue
            public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
            if public_url:
                result.append(public_url)
        return result

    # Remote Zalo Server: serve every local image from ONE temporary HTTP server.
    # This avoids opening N ports + 2N threads for an N-image action.
    result = [None] * len(items)
    local_positions = []
    local_files = []
    for index, image_path in enumerate(items):
        if image_path.startswith(("http://", "https://")):
            result[index] = image_path
        elif await _async_is_file(hass, image_path):
            local_positions.append(index)
            local_files.append(image_path)
        else:
            _LOGGER.warning("Không tìm thấy tệp ảnh: %s, bỏ qua", image_path)

    if local_files:
        urls = await hass.async_add_executor_job(serve_files_temporarily, local_files, 120)
        for index, url in zip(local_positions, urls, strict=False):
            result[index] = url

    return [url for url in result if url]


async def async_send_images_to_user_service(hass, call, zalo_login):
    """Dịch vụ gửi nhiều ảnh cho người dùng."""
    _LOGGER.debug("Dịch vụ async_send_images_to_user được gọi với: %s", call.data)
    try:
        processed_paths = await _prepare_multi_image_urls(
            hass, call.data["image_paths"].split(",")
        )
        if not processed_paths:
            error_msg = "Không có ảnh nào được xử lý thành công"
            await show_result_notification(hass, "gửi nhiều ảnh cho người dùng", None, error=error_msg)
            return {"error": error_msg}

        payload = {
            "imagePaths": processed_paths,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendImagesToUserByAccount", json=payload)
        )
        await show_result_notification(hass, "gửi nhiều ảnh cho người dùng", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as err:
        _LOGGER.error("Lỗi trong async_send_images_to_user: %s", err, exc_info=True)
        await show_result_notification(hass, "gửi nhiều ảnh cho người dùng", None, error=str(err))
        return {"error": str(err)}


async def async_send_images_to_group_service(hass, call, zalo_login):
    """Dịch vụ gửi nhiều ảnh cho nhóm."""
    _LOGGER.debug("Dịch vụ async_send_images_to_group được gọi với: %s", call.data)
    try:
        processed_paths = await _prepare_multi_image_urls(
            hass, call.data["image_paths"].split(",")
        )
        if not processed_paths:
            error_msg = "Không có ảnh nào được xử lý thành công"
            await show_result_notification(hass, "gửi nhiều ảnh cho nhóm", None, error=error_msg)
            return {"error": error_msg}

        payload = {
            "imagePaths": processed_paths,
            "threadId": str(call.data["thread_id"]),
            "accountSelection": str(call.data["account_selection"]),
        }
        if "ttl" in call.data:
            payload["ttl"] = call.data["ttl"]
        resp = await hass.async_add_executor_job(
            lambda: session.post(f"{zalo_server}/api/sendImagesToGroupByAccount", json=payload)
        )
        await show_result_notification(hass, "gửi nhiều ảnh cho nhóm", resp)
        try:
            return resp.json()
        except ValueError:
            return {"text": resp.text}
    except Exception as err:
        _LOGGER.error("Lỗi trong async_send_images_to_group: %s", err, exc_info=True)
        await show_result_notification(hass, "gửi nhiều ảnh cho nhóm", None, error=str(err))
        return {"error": str(err)}

