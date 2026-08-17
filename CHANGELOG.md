# Changelog

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
