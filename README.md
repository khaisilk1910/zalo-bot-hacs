# Zalo Bot for Home Assistant

Custom integration Home Assistant kết nối tới **Zalo Server** để gửi tin nhắn, ảnh, file, video, sticker, quản lý tài khoản/nhóm/bạn bè và sử dụng các action Zalo trong automation.

> Bản này đã được rà soát để tương thích và tối ưu cho **Zalo Server v1.0.6**.

## Yêu cầu

- Home Assistant 2024.3.0 trở lên.
- HACS nếu muốn cài đặt/cập nhật tự động.
- Zalo Server v1.0.6 trở lên đang chạy và Home Assistant truy cập được.
- Nếu gửi file/ảnh local theo cơ chế shared volume, dùng cùng cấu trúc volume với Zalo Server.

Stack Zalo Server khuyến nghị:

```yaml
services:
  zalobot:
    image: ghcr.io/khaisilk1910/zalo-bot-server:v1.0.6
    container_name: zalo-server
    restart: unless-stopped
    network_mode: host
    environment:
      - TZ=Asia/Ho_Chi_Minh
      - PORT=3000
    volumes:
      - /opt/home-assistant/config/zalo-server:/app/data
      - /opt/home-assistant/config/www/zalo-server:/config/www/zalo_bot
```

Có thể đổi `PORT=3000` sang port khác, ví dụ `PORT=3100`.

## Cài đặt qua HACS

### Thêm custom repository

1. Mở HACS trong Home Assistant.
2. Chọn menu ba chấm ở góc trên bên phải.
3. Chọn **Custom repositories**.
4. Repository:
   `https://github.com/khaisilk1910/zalo-bot-hacs`
5. Type: **Integration**.
6. Chọn **Add**.
7. Mở repository **Zalo Bot** trong HACS và chọn **Download**.
8. Khởi động lại Home Assistant.

Sau khi restart:

1. Vào **Settings → Devices & services**.
2. Chọn **Add Integration**.
3. Tìm **Zalo Bot**.
4. Nhập:
   - Zalo Server URL, ví dụ `http://192.168.1.10:3000` hoặc `http://192.168.1.10:3100`.
   - Username/password quản trị của Zalo Server.
   - Tùy chọn thông báo kết quả.
5. Config flow sẽ kiểm tra kết nối và thông tin đăng nhập trước khi lưu.

## Cài đặt thủ công

Sao chép:

```text
custom_components/zalo_bot
```

vào:

```text
/config/custom_components/zalo_bot
```

sau đó restart Home Assistant và thêm integration từ **Settings → Devices & services**.

## Tương thích với Zalo Server v1.0.6

Các thay đổi quan trọng trong bản integration này:

- `create_note_group` dùng endpoint `/api/createNoteByAccount`.
- `edit_note_group` dùng endpoint `/api/editNoteByAccount`.
- `get_quick_message` dùng `/api/getQuickMessageListByAccount`.
- `undo_message` dùng `/api/undoByAccount` và yêu cầu cả `msg_id` + `cli_msg_id`.
- Proxy API dùng `/proxies` thay vì `/api/proxies`.
- Khôi phục `get_received_friend_requests` qua `/api/getReceivedFriendRequestsByAccount`.
- Khôi phục `get_group_chat_history` qua `/api/getGroupChatHistoryByAccount`. Vì Zalo đã gỡ API history gốc, Cơ chế được giới thiệu từ Zalo Server v1.0.4 và tiếp tục có trong v1.0.6: server lưu lịch sử nhóm cục bộ trong `/app/data/history/groups` từ các message listener quan sát được.
- Thư mục file dùng chung trên Home Assistant đổi thành:
  `/config/www/zalo-server`
- Các action gửi tin nhắn/file/ảnh **không tự gửi `ttl=0`** nữa. Nếu không chọn TTL, integration không thay đổi Auto Delete của cuộc trò chuyện.
- TTL hỗ trợ theo Zalo Server v1.0.6:
  - `off`
  - `1d`
  - `7d`
  - `14d`
- Gửi video không còn gửi TTL per-message vì cơ chế đó không đáng tin cậy; nếu cần hãy dùng action `zalo_bot.update_auto_delete_chat`.
- `get_group_chat_history` trả tối đa 200 tin gần nhất từ cache bền vững của server. Lịch sử bắt đầu được thu thập từ khi chạy Zalo Server v1.0.4 trở lên; không thể tải ngược các tin cũ trước thời điểm đó vì endpoint history phía Zalo hiện đã bị gỡ.

### Lưu ý về Auto Delete

`ttl` trên Zalo Server v1.0.6 là cài đặt **Auto Delete của cuộc trò chuyện**, không phải bộ đếm tự hủy riêng cho một message.

Ví dụ:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "123456789"
  type: "1"
  message: "Tin nhắn nhóm"
  ttl: "1d"
```

Nếu không muốn thay đổi Auto Delete, bỏ hẳn trường `ttl`.

Để tắt Auto Delete:

```yaml
action: zalo_bot.update_auto_delete_chat
data:
  account_selection: "+84123456789"
  thread_id: "123456789"
  type: "1"
  ttl: "off"
```

## Ví dụ gửi tin nhắn

Gửi cho user:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "0"
  message: "Xin chào từ Home Assistant"
```

Gửi vào group:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "1"
  message: "Thông báo từ Home Assistant"
```

## Thu hồi tin nhắn

Zalo Server yêu cầu cả `msgId` và `cliMsgId`:

```yaml
action: zalo_bot.undo_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "1"
  msg_id: "123456"
  cli_msg_id: "987654"
```

## Gửi ảnh/file local

Integration sử dụng:

```text
/config/www/zalo-server
```

và stack Zalo Server cần mount cùng thư mục host:

```yaml
- /opt/home-assistant/config/www/zalo-server:/config/www/zalo_bot
```

Đường dẫn bên trong container Zalo Server vẫn là `/config/www/zalo_bot` vì source server hiện sử dụng đường dẫn này.

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
│       ├── manifest.json
│       ├── services.yaml
│       └── ...
├── hacs.json
├── CHANGELOG.md
└── README.md
```

## Release

Integration sử dụng CalVer. Release đầu tiên của fork này:

```text
v2026.8.17.3
```

Mỗi lần phát hành, cập nhật `version` trong `custom_components/zalo_bot/manifest.json`, tạo tag và **GitHub Release** tương ứng.

## Kiểm tra CI

Repository có sẵn:

- HACS validation.
- Home Assistant Hassfest validation.

Sau khi push lên GitHub, kiểm tra tab **Actions** và chỉ publish release khi hai workflow đều xanh.

## Nguồn và trách nhiệm sử dụng

Integration giao tiếp với Zalo Server và các API Zalo không chính thức. Hãy sử dụng tài khoản và hệ thống của bạn theo các điều khoản áp dụng và tự kiểm tra các thay đổi API khi nâng phiên bản server.

## Hai action được khôi phục trong v2026.8.17.1

### `zalo_bot.get_received_friend_requests`

```yaml
action: zalo_bot.get_received_friend_requests
data:
  account_selection: "+84123456789"
response_variable: received_friend_requests
```

Kết quả trả về chỉ gồm các mục lời mời kết bạn đã nhận đang chờ xử lý.

### `zalo_bot.get_group_chat_history`

```yaml
action: zalo_bot.get_group_chat_history
data:
  account_selection: "+84123456789"
  group_id: "123456789"
  count: 50
response_variable: group_history
```

Zalo hiện không còn cung cấp endpoint history nhóm mà `zca-js` từng sử dụng. Vì vậy từ Zalo Server v1.0.4 (bao gồm v1.0.6), server lưu các message nhóm mà listener quan sát được vào volume `/app/data/history/groups` và action này đọc từ cache bền vững đó. Cache tồn tại qua restart container, nhưng không thể khôi phục các tin nhắn cũ trước thời điểm bạn cài v1.0.4.
