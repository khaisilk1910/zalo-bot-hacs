"""Các tính năng gửi tin nhắn, file, hình ảnh và video cho Zalo Bot."""
import logging
import os
from .const import DOMAIN
from .file_handling import serve_file_temporarily, serve_files_temporarily, copy_to_public, get_video_duration_ms, is_local_zalo_server
from .notification import show_result_notification

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

def _js_len(s):
    """Tính độ dài chuỗi theo UTF-16 (JavaScript style).
    Emoji và ký tự surrogate (U+10000 trở lên) tính là 2."""
    return sum(2 if ord(ch) >= 0x10000 else 1 for ch in s)


def _py_to_js_pos(text, py_pos):
    """Chuyển vị trí Python sang vị trí JavaScript (UTF-16)."""
    return _js_len(text[:py_pos])


ZALO_COLORS = {
    "red": "c_db342e",
    "orange": "c_f27806",
    "yellow": "c_f7b503",
    "green": "c_15a85f",
}

HEADING_STYLES = {
    1: "f_20,b",   # H1: rất lớn + đậm
    2: "f_18,b",   # H2: lớn + đậm
    3: "b",        # H3: đậm (bình thường)
    4: "f_13",     # H4: nhỏ
    5: "f_13",     # H5: nhỏ
    6: "f_13",     # H6: nhỏ
}


def _resolve_style_token(style_input):
    """Resolve style input to a Zalo st token.

    - "off" / "" / None -> None (just bold)
    - "red", "orange", ... -> "c_xxx,b" (color + bold)
    - "b", "i", "u", "s" -> raw token
    - "c_db342e,b" -> raw passthrough
    """
    if not style_input or style_input == "off":
        return None
    style_input = style_input.strip().lower()
    color_token = ZALO_COLORS.get(style_input)
    if color_token:
        return color_token + ",b"
    return style_input


def markdown_to_zalo_styles(text, style_override=None):
    """Chuyển đổi markdown text sang Zalo RTF format với styles.

    Args:
        text: markdown text
        style_override: style token (red/orange/yellow/green hoặc raw token như
                        "i", "u", "c_db342e,b,f_18"). None/"off" = chỉ bold.

    Returns:
        dict với "msg" (plain text) và "styles" (list of style objects)
    """
    if not text or not isinstance(text, str):
        _LOGGER.debug("[markdown_to_zalo_styles] input is None or not str: %s", type(text))
        return {"msg": text or "", "styles": []}

    _LOGGER.debug("[markdown_to_zalo_styles] INPUT len=%d first 300 chars: %s", len(text), text[:300])

    # Log all asterisk-like characters in the text
    for i, ch in enumerate(text):
        if ch == '*' or ord(ch) in (0x2217, 0xFE61, 0xFF0A, 0x204E, 0x2731, 0x2732):
            ctx = text[max(0, i - 10):i + 15]
            _LOGGER.debug("[markdown_to_zalo_styles] ASTERISK at pos=%d U+%04X ctx=%s", i, ord(ch), repr(ctx))

    # Phase 1: stack-based pair matching
    # Stack entries: (marker_str, open_pos_in_original, token)
    matched = []
    stack = []
    i = 0

    while i < len(text):
        # Link: [text](url) - keep URL, strip text
        if text[i] == '[':
            close_br = text.find('](', i)
            if close_br != -1:
                close_pr = text.find(')', close_br + 2)
                if close_pr != -1:
                    url = text[close_br + 2:close_pr]
                    _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d LINK url=%s",
                                  i, repr(url[:50]))
                    matched.append((i, close_pr + 1, url, ""))
                    i = close_pr + 1
                    continue

        # Bold+Italic combo: ***text***
        if i + 2 < len(text) and text[i:i + 3] == '***':
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d found '***' stack=%s", i, [(s[2], s[1]) for s in stack])
            if stack and stack[-1][2] == 'bi':
                _, open_pos, _ = stack.pop()
                content = text[open_pos + 3:i]
                _LOGGER.debug("[markdown_to_zalo_styles]   -> CLOSE bold+italic: open=%d close=%d content=%s", open_pos, i + 3, repr(content))
                matched.append((open_pos, i + 3, content, 'b,i'))
            else:
                _LOGGER.debug("[markdown_to_zalo_styles]   -> OPEN bold+italic at pos=%d", i)
                stack.append(('***', i, 'bi'))
            i += 3
            continue

        # Markdown heading: # ## ### etc at line start
        if text[i] == '#' and (i == 0 or text[i - 1] == '\n'):
            level = 0
            j = i
            while j < len(text) and text[j] == '#':
                level += 1
                j += 1
            if j < len(text) and text[j] == ' ':
                j += 1
            end = text.find('\n', j)
            if end == -1:
                end = len(text)
            heading_style = HEADING_STYLES.get(level, "i")
            content = text[j:end]
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d HEADING H%d style=%s content=%s",
                         i, level, heading_style, repr(content[:50]))
            matched.append((i, end, content, heading_style))
            i = end
            continue

        # Blockquote: > at line start
        if text[i] == '>' and (i == 0 or text[i - 1] == '\n'):
            j = i + 1
            if j < len(text) and text[j] == ' ':
                j += 1
            end = text.find('\n', j)
            if end == -1:
                end = len(text)
            content = text[j:end]
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d BLOCKQUOTE style=i content=%s",
                         i, repr(content[:50]))
            matched.append((i, end, content, "i"))
            i = end
            continue

        # Inline code: `text`
        if text[i] == '`':
            j = text.find('`', i + 1)
            if j != -1:
                content = text[i + 1:j]
                _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d INLINE CODE style=i content=%s",
                             i, repr(content[:50]))
                matched.append((i, j + 1, content, "i"))
                i = j + 1
                continue

        if i + 1 < len(text) and text[i:i + 2] == '**':
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d found '**' stack=%s", i, [(s[2], s[1]) for s in stack])
            if stack and stack[-1][2] == 'b':
                _, open_pos, _ = stack.pop()
                content = text[open_pos + 2:i]
                _LOGGER.debug("[markdown_to_zalo_styles]   -> CLOSE bold: open=%d close=%d content=%s", open_pos, i + 2, repr(content))
                matched.append((open_pos, i + 2, content, 'b'))
            else:
                _LOGGER.debug("[markdown_to_zalo_styles]   -> OPEN bold at pos=%d", i)
                stack.append(('**', i, 'b'))
            i += 2
        elif i + 1 < len(text) and text[i:i + 2] == '~~':
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d found '~~' stack=%s", i, [(s[2], s[1]) for s in stack])
            if stack and stack[-1][2] == 's':
                _, open_pos, _ = stack.pop()
                content = text[open_pos + 2:i]
                _LOGGER.debug("[markdown_to_zalo_styles]   -> CLOSE strike: open=%d close=%d content=%s", open_pos, i + 2, repr(content))
                matched.append((open_pos, i + 2, content, 's'))
            else:
                _LOGGER.debug("[markdown_to_zalo_styles]   -> OPEN strike at pos=%d", i)
                stack.append(('~~', i, 's'))
            i += 2
        elif i + 1 < len(text) and text[i:i + 2] == '__':
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d found '__' stack=%s", i, [(s[2], s[1]) for s in stack])
            if stack and stack[-1][2] == 'u':
                _, open_pos, _ = stack.pop()
                content = text[open_pos + 2:i]
                _LOGGER.debug("[markdown_to_zalo_styles]   -> CLOSE underline: open=%d close=%d content=%s", open_pos, i + 2, repr(content))
                matched.append((open_pos, i + 2, content, 'u'))
            else:
                _LOGGER.debug("[markdown_to_zalo_styles]   -> OPEN underline at pos=%d", i)
                stack.append(('__', i, 'u'))
            i += 2
        elif text[i] == '*':
            _LOGGER.debug("[markdown_to_zalo_styles]   pos=%d found '*' stack=%s", i, [(s[2], s[1]) for s in stack])
            if stack and stack[-1][2] == 'i':
                _, open_pos, _ = stack.pop()
                content = text[open_pos + 1:i]
                _LOGGER.debug("[markdown_to_zalo_styles]   -> CLOSE italic: open=%d close=%d content=%s", open_pos, i + 1, repr(content))
                matched.append((open_pos, i + 1, content, 'i'))
            else:
                _LOGGER.debug("[markdown_to_zalo_styles]   -> OPEN italic at pos=%d", i)
                stack.append(('*', i, 'i'))
            i += 1
        else:
            i += 1

    _LOGGER.debug("[markdown_to_zalo_styles] DONE scanning: matched=%d unclosed=%d", len(matched), len(stack))
    if stack:
        _LOGGER.debug("[markdown_to_zalo_styles] Unclosed markers: %s", [(s[2], s[1]) for s in stack])

    if not matched:
        _LOGGER.debug("[markdown_to_zalo_styles] OUTPUT: no styles, msg same as input")
        return {"msg": text, "styles": []}

    matched.sort(key=lambda m: m[0])

    # Phase 2: build output by stripping markers
    result_parts = []
    styles = []
    offset = 0
    last_end = 0

    for orig_start, orig_end, content, token in matched:
        result_parts.append(text[last_end:orig_start])
        out_start = orig_start - offset
        styles.append({
            "start": out_start,  # Python position, will convert below
            "len": len(content),
            "st": token,
        })
        result_parts.append(content)
        offset += (orig_end - orig_start) - len(content)
        last_end = orig_end

    result_parts.append(text[last_end:])
    final_msg = "".join(result_parts)

    # Convert Python positions to JavaScript/UTF-16 positions
    for s in styles:
        content = final_msg[s["start"]:s["start"] + s["len"]]
        s["start"] = _py_to_js_pos(final_msg, s["start"])
        s["len"] = _js_len(content)

    # Apply style_override to all bold styles (including heading bold)
    override_token = _resolve_style_token(style_override)
    if override_token:
        count = 0
        for s in styles:
            tokens = s["st"].split(",")
            if "b" in tokens:
                # Replace 'b' with the override (e.g. 'f_20,b' -> 'f_20,c_db342e,b')
                new_tokens = [override_token if t == "b" else t for t in tokens]
                s["st"] = ",".join(new_tokens)
                count += 1
        _LOGGER.debug("[markdown_to_zalo_styles] style_override=%s -> token=%s applied to %d bold styles",
                     style_override, override_token, count)

    # Filter out no-style entries (links, etc.)
    styles = [s for s in styles if s["st"] != ""]

    # Log final styles with the text they apply to
    for s in styles:
        highlighted = final_msg[s["start"]:s["start"] + s["len"]]
        _LOGGER.debug("[markdown_to_zalo_styles] STYLE [%d:%d] st=%s text=%s", s["start"], s["start"] + s["len"], s["st"], repr(highlighted))

    _LOGGER.debug("[markdown_to_zalo_styles] OUTPUT: msg len=%d styles=%d", len(final_msg), len(styles))

    return {"msg": final_msg, "styles": styles}

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
            parsed = markdown_to_zalo_styles(raw_message, style)

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
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": 1 if msg_type == "1" else 0
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
                return
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, file_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy tệp đến thư mục public"
                        await show_result_notification(hass, "gửi file", None, error=error_msg)
                        return
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
                return
        if not public_url:
            await show_result_notification(hass, "gửi file", None, error="Không thể tạo URL công khai cho tệp.")
            return
        payload = {
            "fileUrl": public_url,
            "message": call.data.get("message", ""),
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": "group" if msg_type == "1" else "user",
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
                return
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh", None, error=error_msg)
                        return
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
                return
        payload = {
            "imagePath": public_url,
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "type": "group" if msg_type == "1" else "user",
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
                return
            try:
                _LOGGER.debug(f"Sử dụng máy chủ HTTP tạm thời để phục vụ tệp video: {video_path}")
                public_url = await hass.async_add_executor_job(
                    serve_file_temporarily, video_path, 90
                )
            except Exception as e:
                error_msg = f"Lỗi khi xử lý tệp video: {str(e)}"
                _LOGGER.error(error_msg)
                await show_result_notification(hass, "gửi video", None, error=error_msg)
                return
        if not public_url:
            await show_result_notification(hass, "gửi video", None, error="Không thể tạo URL công khai cho video.")
            return
        thumbnail_url = call.data.get("thumbnail_url", public_url)
        if thumbnail_url and not (thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://")):

            if await _async_is_file(hass, thumbnail_url):
                try:
                    thumbnail_url = await hass.async_add_executor_job(
                        serve_file_temporarily, thumbnail_url, 90
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
        thread_type_num = 1 if msg_type == "1" else 0
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
        resp = await hass.async_add_executor_job(
            lambda: session.post(url, json=payload)
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
            "accountSelection": call.data["account_selection"],
            "threadId": call.data["thread_id"],
            "sticker": sticker,
            "type": 1 if msg_type == "1" else 0
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
        payload = {
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
            "options": {
                "voiceUrl": voice_url
            }
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
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"]
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
                return
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh cho người dùng", None, error=error_msg)
                        return
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
                return
        payload = {
            "imagePath": public_url,
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"]
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
                return
            try:
                is_local_server = is_local_zalo_server(zalo_server)
                if is_local_server:
                    public_url = await hass.async_add_executor_job(copy_to_public, image_path, zalo_server)
                    if not public_url:
                        error_msg = "Không thể copy ảnh đến thư mục public"
                        await show_result_notification(hass, "gửi ảnh cho nhóm", None, error=error_msg)
                        return
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
                return
        payload = {
            "imagePath": public_url,
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"]
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
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
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
            "threadId": call.data["thread_id"],
            "accountSelection": call.data["account_selection"],
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

