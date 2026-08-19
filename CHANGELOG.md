# Changelog

## 2026.8.18.3

### Zalo ID precision / webhook safety
- Thêm `ZALO_ID_SCHEMA` cho các ID đơn của service; Python integer từ template được chuyển sang string trước khi request đi qua JSON/JavaScript, giữ nguyên toàn bộ chữ số.
- Hỗ trợ dạng template-safe `zalo:<id>`; integration tự bỏ prefix trước khi gửi server.
- Chuẩn hóa đệ quy các field ID/ID list trong JSON request về string, bao gồm cả ID lồng trong quote/message payload.
- Các ID có contract dạng số của SDK (Poll ID và Quick Message item ID) được loại khỏi cơ chế ép chuỗi chung và chuẩn hóa riêng về `int`, tránh regression cho các action poll/quick-message.
- `add_reaction` giữ `threadId`/`msgId`/`cliMsgId` dạng string đúng contract zca-js 2.1.2, bỏ round-trip qua Python `int`.
- README thêm mẫu automation dùng webhook `_threadRef`/`_threadType`; không hard-code `type` và không dùng Zalo ID thuần số làm `conversation_id`.

### Per-message TTL
- Tách hoàn toàn TTL của message khỏi Auto Delete conversation.
- Thêm lựa chọn `1h` đến `24h`, giữ `1d`, `7d`, `14d`, `off`; schema chuẩn hóa sang milliseconds.
- TTL áp dụng cho text, file, ảnh đơn/nhiều ảnh, video và voice.
- `update_auto_delete_chat` vẫn là action riêng với các mốc `off/1d/7d/14d`.

### Reliability
- TimeoutSession tiếp tục tái sử dụng connection/session, chạy blocking HTTP qua executor và hiện trả chi tiết lỗi JSON của server trong `HomeAssistantError`.
- Không thêm I/O mạng/filesystem vào `async_setup_entry`; startup behavior giữ như v2026.8.18.2.
- Rà soát Options Flow với Home Assistant 2026.8: tiếp tục dùng update listener + `OptionsFlow.async_create_entry` (không dùng các config-flow helper tự reload), nên không rơi vào trường hợp double-reload/race bị deprecated từ Core 2026.6 và vẫn giữ tương thích các bản HA cũ mà integration đã công bố.

## 2026.8.18.2

### Rich text / Markdown
- Giữ nguyên parser Markdown cũ cho `**bold**`, `*italic*`, `***bold+italic***`, `__underline__`, `~~strike~~`, heading, blockquote, inline code và link.
- Bổ sung format inline `{red}`, `{orange}`, `{yellow}`, `{green}`, `{big}`, `{small}` theo đúng `TextStyle` của zca-js 2.1.2.
- Bổ sung Markdown unordered list (`-`, `*`, `+`), ordered list (`1.`/`1)`) và indent đầu dòng bằng `ind_$` + `indentSize`.
- Sửa heading H1 không còn dùng token không được zca-js 2.1.2 công bố `f_20`; H1/H2 dùng hai style atomic `f_18` + `b`.
- Hỗ trợ lồng màu/kích thước với Markdown; màu inline có ưu tiên hơn entity `Markdown Color`.
- Payload style được tách thành từng `TextStyle` atomic đúng type công khai của zca-js 2.1.2; không phụ thuộc chuỗi token ghép không được type định nghĩa.
- Tất cả `start`/`len` style được tính theo UTF-16 code unit để emoji/ký tự ngoài BMP không làm lệch format.
- Bổ sung escape cho tag inline, ví dụ `\{red}` để gửi literal `{red}`.
- Tách parser rich text sang `text_formatting.py` thuần xử lý chuỗi và chạy parser qua Home Assistant executor khi gửi tin, nên message format lớn không giữ event loop và không ảnh hưởng startup.

### Home Assistant compatibility / verification
- Không thêm network/filesystem I/O vào `async_setup_entry`; binary sensor vẫn refresh lần đầu bằng config-entry background task.
- Rà soát thay đổi device registry công bố cho Home Assistant Core 2026.8: integration chỉ tạo một device thuộc đúng config entry và không dùng device/subentry API bị loại bỏ.
- Giữ đăng ký action trong `async_setup`, `async_forward_entry_setups`/`async_unload_platforms`, config-flow network validation trong executor và HTTP action I/O trong executor.
- README bổ sung bảng format, ví dụ kết hợp màu/kích thước/list/indent và lưu ý UTF-16/emoji.

## 2026.8.18.1

### Zalo Server / zca-js 2.1.2 compatibility
- Rà soát trực tiếp toàn bộ endpoint action đang dùng với `zalo-bot-server-zcajs-2.1.2-reviewed`.
- Sửa `change_group_avatar`: `imagePath` -> `avatarSource`.
- Sửa `forward_message` theo breaking change zca-js 2.x: `threadIds` chuyển ra cấp request, tách khỏi `params`.
- Sửa `get_stickers_detail`: dùng `stickerAlbum` và chuyển một/nhiều ID từ UI sang `number`/`number[]`.
- Sửa `last_online`: `userId` -> `uid`.
- Sửa `set_mute`: `threadId` -> `threadID`, đồng thời đổi `action` sang enum số đúng zca-js 2.1.2 (`MUTE=1`, `UNMUTE=3`).
- Bổ sung/chuẩn hóa `type` cho unread mark, hidden conversation, card, link, voice, typing, reminder và các action conversation liên quan.
- Sửa `create_reminder` dùng `options.startTime` dạng timestamp mili-giây thay cho payload cũ `content/remindTime`; vẫn chấp nhận field `content` cũ trong schema để automation cũ không bị reject.
- Sửa `get_list_board` và `get_list_reminder` luôn gửi `options.page/count` (mặc định 1/20), tránh lỗi `options` bị `undefined` trong zca-js 2.1.2.
- Lọc option rỗng và yêu cầu tối thiểu 2 lựa chọn khi `create_poll`.
- Sửa `delete_chat`: bắt buộc `last_message`, chuẩn hóa `ownerId`, `cliMsgId`, `globalMsgId`; chấp nhận alias `uidFrom`/`msgId` từ dữ liệu lịch sử.
- Sửa PIN hidden conversation dùng đúng trường `pin`; bỏ lệch schema/handler `old_pin`/`new_pin`.
- Chuẩn hóa thread type để chấp nhận tương thích cả `0/1` và `user/group`.

### Home Assistant reliability
- Không chờ network refresh của binary sensor trong `async_setup_entry`; refresh đầu chạy bằng config-entry background task và tự hủy khi unload.
- Giữ HTTP blocking I/O trong executor và tái sử dụng pooled authenticated session để không chặn event loop.
- Với `SupportsResponse.OPTIONAL`, chỉ trả response khi action được gọi với response data; vẫn chuyển lỗi API thành `HomeAssistantError`.
- HTTP 4xx/5xx từ Zalo Server và lỗi xử lý file/ảnh/video local được chuyển thành action failure thay vì có thể bị hiểu nhầm là thành công.
- Đóng `requests.Session` qua executor khi unload để tránh thao tác blocking trong event loop.
- Sửa schema `get_avatar_list` để cho phép đúng `count`/`page` đã có trong UI service.
- Đồng bộ field của `services.yaml` với schema và translations EN/VI.

### Verification
- Python compile toàn bộ custom component: pass.
- Parse `services.yaml`, `manifest.json`, `hacs.json`, translations EN/VI: pass.
- Đối chiếu đăng ký service/schema với `services.yaml`: 97/97 khớp field.
- Đối chiếu endpoint HACS với server reviewed: toàn bộ endpoint được integration sử dụng đều có route tương ứng (bao gồm route động account/webhook).

## 2026.8.17

### Compatibility
- Rà soát và đồng bộ endpoint với Zalo Server v1.0.3.
- Sửa endpoint note nhóm: `createNoteByAccount`, `editNoteByAccount`.
- Sửa Quick Message list endpoint: `getQuickMessageListByAccount`.
- Sửa Proxy API từ `/api/proxies` sang `/proxies`.
- Sửa `undo_message` để gửi `msgId` và `cliMsgId` tới `/api/undoByAccount`.
- Bỏ các action chưa có endpoint server v1.0.3: `get_group_chat_history`, `get_received_friend_requests`.

### Auto Delete
- Không còn tự gửi `ttl=0` trong các action gửi tin nhắn/file/ảnh.
- Chỉ gửi TTL khi người dùng thực sự chọn.
- Hỗ trợ `off`, `1d`, `7d`, `14d`.
- Thêm TTL cho các action gửi ảnh user/group tương thích server v1.0.3.
- Bỏ TTL khỏi gửi video per-message.

### Home Assistant / HACS
- Thêm manifest metadata phù hợp HACS; yêu cầu Home Assistant tối thiểu 2024.3 vì dùng `single_config_entry`.
- Thêm brand icon local.
- Thêm `translations/en.json` và `translations/vi.json`, bao gồm config flow và toàn bộ service action/field.
- Config flow kiểm tra kết nối và credentials trước khi tạo entry.
- Options flow kiểm tra kết nối và reload entry khi thay đổi.
- Đăng ký service action một lần trong `async_setup`.
- Sửa lỗi `get_sent_friend_requests` trước đây bị trỏ nhầm sang handler `create_reminder`.
- Đổi `supports_response` sang `SupportsResponse.OPTIONAL`.
- Thêm timeout mặc định cho HTTP session.
- Đóng session HTTP khi unload.
- Dọn session riêng của binary sensor khi config entry unload.
- Thêm HACS và Hassfest GitHub Actions.

### Files
- Đổi shared public directory Home Assistant sang `/config/www/zalo-server` để khớp stack mới.

## 2026.8.17.1
- Restore `get_received_friend_requests` using `zalo-server v1.0.4 /api/getReceivedFriendRequestsByAccount`.
- Restore `get_group_chat_history` using the persistent local group-history cache added in `zalo-server v1.0.4`.
- Add validation for group history `count` (1-200) and service translations in English/Vietnamese.
- Requires `zalo-server v1.0.4` or newer for these two restored actions.

## 2026.8.17.2
- Sửa gửi nhiều ảnh: file được copy sang `/config/www/zalo-server` với tên duy nhất để tránh ghi đè/cached URL khi ảnh trùng basename.
- Đồng bộ với Zalo Server v1.0.5 để mỗi attachment giữ đúng ảnh nguồn.

## 2026.8.17.3
- Giảm HTTP round-trip: tái sử dụng session đăng nhập và chỉ đăng nhập lại khi hết phiên/HTTP 401; bỏ bước login executor dư trước mỗi action.
- Binary sensor dùng `/api/health` nhẹ, tái sử dụng aiohttp session và đóng session ngay khi config entry unload/reload.
- Chuyển `ffprobe` và filesystem checks sang executor để không block Home Assistant event loop.
- Chuẩn hóa lỗi action thành `HomeAssistantError` khi HTTP/API thất bại hoặc `success=false`.
- So sánh Zalo Server URL theo đúng origin (scheme + host + port), tránh nhận nhầm URL có prefix tương tự.
- Giữ nguyên 97 action/service và schema để automation hiện tại không phải đổi YAML.
- Đổi `iot_class` sang `local_polling` để phản ánh đúng coordinator polling trạng thái server/account.
- Temporary file bridge bind trực tiếp port 0 do OS cấp để loại race condition khi nhiều action gửi file/ảnh đồng thời; nhận diện loopback theo hostname chính xác.
- Chuẩn hóa nhận diện loopback cho mọi action file/ảnh/avatar; không còn kiểm tra substring `localhost` có thể nhận nhầm hostname.
- Yêu cầu/recommend Zalo Server v1.0.6 để nhận đầy đủ các bản vá reliability, security và webhook API.

## 2026.08.19.0900

- Sửa quy trình phát hành HACS: version trong `manifest.json` phải khớp chính xác với tag trước khi Release được tạo.
- Bỏ cơ chế sửa `manifest.json` sau khi Release đã published và không còn force-move tag sau phát hành.
- Chuyển sang HACS `zip_release` với asset cố định `zalo_bot.zip`.
- Workflow release tự kiểm tra cấu trúc, compile Python, đóng ZIP với `manifest.json` ở root và upload asset vào GitHub Release.
- Thêm kiểm tra metadata để phát hiện sớm version/tag hoặc cấu hình HACS sai.
