# Changelog

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
