# Zalo Bot for Home Assistant

Custom integration cho Home Assistant kết nối tới **Zalo Bot Server** để gửi/nhận thao tác Zalo trong automation, script và Developer Tools.

> Phiên bản tài liệu này dành cho **Zalo Bot HACS v2026.8.18.1** và được rà soát trực tiếp với **zalo-bot-server-zcajs-2.1.2-reviewed** (server package 1.1.0, `zca-js` 2.1.2).

## Tính năng

- Config Flow qua giao diện Home Assistant.
- Kiểm tra kết nối và tài khoản quản trị Zalo Server trước khi lưu cấu hình.
- Giữ HTTP session đã xác thực để giảm số lần login và giảm độ trễ mỗi action.
- Tự login lại một lần khi session server hết hạn.
- Binary sensor trạng thái Zalo Server và trạng thái đăng nhập Zalo; lần refresh kết nối đầu chạy nền để không giữ quá trình setup/startup của Home Assistant.
- Button lấy QR đăng nhập Zalo.
- Switch bật/tắt notification và Markdown.
- Select màu Markdown.
- 97 action cho message, media, account, friend, group, webhook, proxy, reminder, poll, quick message và conversation settings.
- Hỗ trợ file/ảnh local của Home Assistant và URL từ xa.
- Gửi nhiều ảnh giữ đúng thứ tự, URL riêng và không ghi đè ảnh trùng tên.
- Hỗ trợ Auto Delete `off`, `1d`, `7d`, `14d` theo Zalo Server.
- Hỗ trợ lấy lời mời kết bạn đã nhận và lịch sử nhóm từ cache bền vững của Zalo Server.
- Action lỗi sẽ báo `HomeAssistantError` đúng nghĩa để automation nhận biết thao tác thất bại.

## Yêu cầu

- Home Assistant **2024.3.0** trở lên.
- HACS nếu muốn cài/cập nhật integration thuận tiện.
- Khuyến nghị dùng đúng **zalo-bot-server-zcajs-2.1.2-reviewed** (server package 1.1.0, `zca-js` 2.1.2) hoặc bản server mới hơn có cùng API contract.
- Username/password quản trị của Zalo Server.

> README của integration này không chứa cấu hình Docker/Stack. Cách triển khai server và volume được tài liệu tại repo **zalo-bot-server**.

### Ghi chú tương thích với server zca-js 2.1.2

Bản `2026.8.18.1` đồng bộ payload/action với server reviewed, gồm các thay đổi quan trọng: `forward_message` gửi `threadIds` ở cấp request, `delete_chat` gửi `lastMessage`, `change_group_avatar` dùng `avatarSource`, `get_stickers_detail` dùng `stickerAlbum`, `last_online` dùng `uid`, `set_mute` dùng `threadID` + enum `action` số của zca-js 2.1.2, reminder dùng `startTime`, các action list board/reminder luôn gửi `options.page/count`, và các action liên quan conversation gửi `type` nhất quán (`0/user`, `1/group`).

`delete_chat` yêu cầu `last_message` lấy từ tin nhắn cuối của lịch sử chat. Integration chấp nhận cả bộ trường chuẩn `ownerId`, `cliMsgId`, `globalMsgId` và alias thường có trong lịch sử `uidFrom`, `cliMsgId`, `msgId`.

## Cài đặt qua HACS

### 1. Thêm Custom Repository

Trong Home Assistant:

1. Mở **HACS**.
2. Chọn menu **⋮ → Custom repositories**.
3. Repository:

```text
https://github.com/khaisilk1910/zalo-bot-hacs
```

4. Type: **Integration**.
5. Chọn **Add**.
6. Mở **Zalo Bot** trong HACS và chọn **Download**.
7. Restart Home Assistant.

### 2. Thêm integration

Sau khi restart:

1. Vào **Settings → Devices & services**.
2. Chọn **Add Integration**.
3. Tìm **Zalo Bot**.
4. Nhập:
   - **Zalo Server URL**, ví dụ `http://192.168.1.10:3000`.
   - **Username** quản trị Zalo Server.
   - **Password** quản trị Zalo Server.
   - Tùy chọn notification nếu cần.
5. Integration sẽ gọi `/api/login` để xác minh server và credential trước khi tạo config entry.

Có thể dùng port tùy chỉnh, ví dụ:

```text
http://192.168.1.10:3100
```

## Cài đặt thủ công

Sao chép thư mục:

```text
custom_components/zalo_bot
```

vào:

```text
/config/custom_components/zalo_bot
```

Restart Home Assistant rồi thêm **Zalo Bot** từ **Settings → Devices & services**.

## Entity được tạo

Integration tạo một device **Zalo Bot** với các entity chính:

| Entity | Chức năng |
|---|---|
| `Zalo Server` | Binary sensor kiểm tra Zalo Server có reachable hay không. |
| `Zalo Login` | Binary sensor trạng thái đăng nhập/kết nối Zalo. |
| `Thông báo` | Bật/tắt notification kết quả từ integration. |
| `Markdown` | Bật/tắt xử lý Markdown. |
| `Markdown Color` | Chọn màu Markdown: `none`, `red`, `orange`, `yellow`, `green`. |
| `Login QR` | Button gọi action lấy QR đăng nhập Zalo. |

Tên entity ID thực tế do Home Assistant tạo và có thể khác tùy ngôn ngữ/đổi tên của người dùng.

## Action

Tất cả action dùng domain:

```text
zalo_bot
```

Ví dụ:

```text
zalo_bot.send_message
zalo_bot.get_all_groups
zalo_bot.get_login_qr
```

### Message và media

- `send_message`
- `send_file`
- `send_image`
- `send_image_to_user`
- `send_images_to_user`
- `send_image_to_group`
- `send_images_to_group`
- `send_sticker`
- `get_stickers`
- `get_stickers_detail`
- `send_voice`
- `send_video`
- `send_card`
- `send_link`
- `send_typing_event`
- `add_reaction`
- `undo_message`
- `delete_message`
- `forward_message`
- `parse_link`

### Account

- `get_logged_accounts`
- `get_account_details`
- `change_account_avatar`
- `get_avatar_list`
- `update_profile`
- `update_settings`
- `last_online`
- `get_login_qr`

### User và bạn bè

- `find_user`
- `get_user_info`
- `send_friend_request`
- `accept_friend_request`
- `get_all_friends`
- `get_received_friend_requests`
- `get_sent_friend_requests`
- `undo_friend_request`
- `remove_friend`
- `change_friend_alias`
- `remove_friend_alias`
- `block_user`
- `unblock_user`
- `block_view_feed`

### Group

- `create_group`
- `get_group_info`
- `get_all_groups`
- `get_group_chat_history`
- `add_user_to_group`
- `remove_user_from_group`
- `add_group_deputy`
- `remove_group_deputy`
- `change_group_owner`
- `change_group_name`
- `change_group_avatar`
- `disperse_group`
- `enable_group_link`
- `disable_group_link`
- `join_group`
- `leave_group`
- `create_note_group`
- `edit_note_group`
- `get_list_board`
- `create_poll`
- `get_poll_detail`
- `lock_poll`

### Conversation settings

- `set_mute`
- `get_mute`
- `set_pinned_conversation`
- `get_pin_conversations`
- `get_unread_mark`
- `add_unread_mark`
- `remove_unread_mark`
- `delete_chat`
- `get_archived_chat_list`
- `get_auto_delete_chat`
- `update_auto_delete_chat`
- `get_hidden_conversations`
- `set_hidden_conversations`
- `update_hidden_convers_pin`
- `reset_hidden_convers_pin`

### Reminder

- `create_reminder`
- `edit_reminder`
- `remove_reminder`
- `get_reminder`
- `get_list_reminder`
- `get_reminder_responses`

### Quick Message

- `add_quick_message`
- `get_quick_message`
- `remove_quick_message`
- `update_quick_message`

### Webhook

- `get_account_webhooks`
- `get_account_webhook`
- `set_account_webhook`
- `delete_account_webhook`

### Proxy

- `get_proxies`
- `add_proxy`
- `remove_proxy`

### Khác

- `get_labels`

Tổng cộng: **97 action**.

## Gửi tin nhắn

### Gửi cho user

`type: "0"` là user.

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "0"
  message: "Xin chào từ Home Assistant"
```

### Gửi vào group

`type: "1"` là group.

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "1"
  message: "Thông báo từ Home Assistant"
```

## Gửi nhiều ảnh

Ví dụ gửi nhiều ảnh tới group:

```yaml
action: zalo_bot.send_images_to_group
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  image_paths: >-
    /config/www/camera/front.jpg,
    /config/www/camera/gate.jpg,
    /config/www/camera/garage.jpg
```

Integration tạo URL/file bridge riêng cho từng ảnh và giữ đúng thứ tự. Zalo Server từ v1.0.5+ cũng dùng file tạm UUID riêng cho từng attachment nên không còn lỗi ảnh cuối bị gửi lặp lại cho toàn bộ danh sách.

## File và ảnh local

Integration sử dụng thư mục Home Assistant:

```text
/config/www/zalo-server
```

để bridge/copy file local khi cần gửi cho Zalo Server.

Zalo Server phải được triển khai sao cho nó đọc được cùng dữ liệu đó tại public directory tương ứng. Cấu hình Docker/volume cụ thể nằm trong README của **zalo-bot-server**, không nằm trong README HACS này.

Ngoài file local, nhiều action cũng có thể nhận URL HTTP/HTTPS tùy loại media.

## Auto Delete

`ttl` hiện được xử lý như **Auto Delete của cuộc trò chuyện**, không phải timer tự hủy riêng cho một message.

Giá trị hỗ trợ:

```text
off
1d
7d
14d
```

Ví dụ đặt Auto Delete 1 ngày khi gửi message:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "123456789"
  type: "1"
  message: "Tin nhắn nhóm"
  ttl: "1d"
```

Nếu không muốn thay đổi Auto Delete hiện tại, **bỏ hẳn trường `ttl`**.

Để tắt Auto Delete:

```yaml
action: zalo_bot.update_auto_delete_chat
data:
  account_selection: "+84123456789"
  thread_id: "123456789"
  type: "1"
  ttl: "off"
```

## Thu hồi tin nhắn

Action `undo_message` cần cả `msg_id` và `cli_msg_id`:

```yaml
action: zalo_bot.undo_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "1"
  msg_id: "123456"
  cli_msg_id: "987654"
```

## Lời mời kết bạn đã nhận

```yaml
action: zalo_bot.get_received_friend_requests
data:
  account_selection: "+84123456789"
response_variable: received_friend_requests
```

Dùng kết quả trong template/automation tiếp theo:

```jinja2
{{ received_friend_requests }}
```

Server chỉ trả các mục lời mời kết bạn đã nhận đang chờ xử lý.

## Lịch sử nhóm

```yaml
action: zalo_bot.get_group_chat_history
data:
  account_selection: "+84123456789"
  group_id: "123456789"
  count: 50
response_variable: group_history
```

Zalo Server lưu lịch sử nhóm từ message listener vào cache bền vững. Vì endpoint history gốc phía Zalo không còn đáng tin cậy nên action này có các giới hạn:

- Chỉ có message mà server đã quan sát kể từ khi cơ chế history được bật.
- Không thể lấy ngược toàn bộ message trước thời điểm đó.
- Cache được giữ qua restart nếu data directory của server được persist.
- `count` tối đa 200.

## Response variable

Các action đọc dữ liệu có thể dùng `response_variable`, ví dụ:

```yaml
action: zalo_bot.get_all_groups
data:
  account_selection: "+84123456789"
response_variable: groups
```

Sau đó:

```jinja2
{{ groups }}
```

Nếu Zalo Server trả lỗi hoặc request thất bại, integration phát sinh lỗi action thay vì trả một response giả thành công.

## QR đăng nhập Zalo

Có thể dùng button **Login QR** hoặc action:

```yaml
action: zalo_bot.get_login_qr
response_variable: qr_result
```

QR được lấy từ Zalo Server. Sau khi account login thành công, server chịu trách nhiệm lưu cookie/session Zalo và tự reconnect khi connection bị ngắt.

## Trạng thái kết nối

Integration có hai binary sensor:

- **Zalo Server**: poll `/api/health` để xác nhận server reachable.
- **Zalo Login**: kiểm tra trạng thái session/account qua server.

HTTP session được tái sử dụng và được đóng khi config entry unload/reload để tránh rò socket/session trong Home Assistant.

## Tương thích với Zalo Bot Server v1.0.6

Các endpoint/action đã được rà soát đồng bộ với server v1.0.6, bao gồm:

- `create_note_group` → `/api/createNoteByAccount`
- `edit_note_group` → `/api/editNoteByAccount`
- `get_quick_message` → `/api/getQuickMessageListByAccount`
- `undo_message` → `/api/undoByAccount`
- `get_received_friend_requests` → `/api/getReceivedFriendRequestsByAccount`
- `get_group_chat_history` → `/api/getGroupChatHistoryByAccount`
- Account webhook API.
- Proxy API.
- Auto Delete/TTL mới.
- Multi-image sending.

## Cấu trúc repository

```text
.
├── .github/
│   └── workflows/
│       ├── hacs.yaml
│       └── hassfest.yaml
├── custom_components/
│   └── zalo_bot/
│       ├── brand/
│       │   └── icon.png
│       ├── translations/
│       │   ├── en.json
│       │   └── vi.json
│       ├── __init__.py
│       ├── config_flow.py
│       ├── binary_sensor.py
│       ├── switch.py
│       ├── button.py
│       ├── select.py
│       ├── services.yaml
│       └── *_features.py
├── hacs.json
├── CHANGELOG.md
└── README.md
```

## Release và cập nhật

Integration dùng version trong:

```text
custom_components/zalo_bot/manifest.json
```

Quy trình release thông thường:

```bash
git pull --rebase origin main
git add .
git commit -m "Update Zalo Bot HACS"
git push origin main
```

Sau đó tạo tag/release mới, ví dụ:

```bash
git tag -a v2026.8.18 -m "Zalo Bot HACS v2026.8.18"
git push origin v2026.8.18
```

Publish GitHub Release tương ứng để HACS nhận phiên bản mới.

## CI

Repo có workflow:

- HACS validation.
- Home Assistant Hassfest validation.

Chỉ nên publish release sau khi các workflow validation đều thành công.

## Lưu ý

- Integration này cần **Zalo Bot Server**; nó không đăng nhập trực tiếp vào Zalo từ Home Assistant.
- Không đưa password Zalo Server hoặc dữ liệu nhạy cảm vào automation public/GitHub.
- Một số chức năng phụ thuộc API Zalo không chính thức và có thể thay đổi khi Zalo thay đổi backend.
- Lịch sử nhóm là cache do server tự thu thập, không phải archive đầy đủ từ máy chủ Zalo.

## Liên kết

Zalo Bot Server:

```text
https://github.com/khaisilk1910/zalo-bot-server
```

Zalo Bot HACS:

```text
https://github.com/khaisilk1910/zalo-bot-hacs
```
