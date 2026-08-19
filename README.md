# Zalo Bot for Home Assistant

Custom integration cho Home Assistant kết nối tới **Zalo Bot Server** để gửi/nhận thao tác Zalo trong automation, script và Developer Tools.

> Phiên bản tài liệu này dành cho **Zalo Bot HACS v2026.8.18.3** và được rà soát trực tiếp với **Zalo Bot Server v1.2.1** (`zca-js` 2.1.2).

## Tính năng

- Config Flow qua giao diện Home Assistant.
- Kiểm tra kết nối và tài khoản quản trị Zalo Server trước khi lưu cấu hình.
- Giữ HTTP session đã xác thực để giảm số lần login và giảm độ trễ mỗi action.
- Tự login lại một lần khi session server hết hạn.
- Binary sensor trạng thái Zalo Server và trạng thái đăng nhập Zalo; lần refresh kết nối đầu chạy nền để không giữ quá trình setup/startup của Home Assistant.
- Button lấy QR đăng nhập Zalo.
- Switch bật/tắt notification và Markdown.
- Select màu mặc định cho chữ đậm Markdown; màu inline trong nội dung có độ ưu tiên cao hơn.
- 97 action cho message, media, account, friend, group, webhook, proxy, reminder, poll, quick message và conversation settings.
- Hỗ trợ file/ảnh local của Home Assistant và URL từ xa.
- Gửi nhiều ảnh giữ đúng thứ tự, URL riêng và không ghi đè ảnh trùng tên.
- Hỗ trợ rich text cho `send_message`: Markdown cũ + màu, kích thước, list và indent; offset/length được tính theo UTF-16 để không lệch format khi có emoji.
- Hỗ trợ TTL **theo từng tin nhắn** từ `1h` đến `24h`, cùng `1d`, `7d`, `14d` và `off`; Auto Delete của cả cuộc trò chuyện vẫn là action riêng.
- Hỗ trợ lấy lời mời kết bạn đã nhận và lịch sử nhóm từ cache bền vững của Zalo Server.
- Action lỗi sẽ báo `HomeAssistantError` đúng nghĩa để automation nhận biết thao tác thất bại.

## Yêu cầu

- Home Assistant **2024.3.0** trở lên; code đã được rà soát với các thay đổi developer được công bố cho Home Assistant Core 2026.8.
- HACS nếu muốn cài/cập nhật integration thuận tiện.
- Khuyến nghị dùng **Zalo Bot Server v1.2.1** đi kèm bản này (`zca-js` 2.1.2), vì bản server này tách đúng per-message TTL khỏi Auto Delete và bảo vệ Zalo ID lớn.
- Username/password quản trị của Zalo Server.

> README của integration này không chứa cấu hình Docker/Stack. Cách triển khai server và volume được tài liệu tại repo **zalo-bot-server**.

### Ghi chú tương thích với server zca-js 2.1.2

Bản `2026.8.18.1` đồng bộ payload/action với server reviewed, gồm các thay đổi quan trọng: `forward_message` gửi `threadIds` ở cấp request, `delete_chat` gửi `lastMessage`, `change_group_avatar` dùng `avatarSource`, `get_stickers_detail` dùng `stickerAlbum`, `last_online` dùng `uid`, `set_mute` dùng `threadID` + enum `action` số của zca-js 2.1.2, reminder dùng `startTime`, các action list board/reminder luôn gửi `options.page/count`, và các action liên quan conversation gửi `type` nhất quán (`0/user`, `1/group`).

`delete_chat` yêu cầu `last_message` lấy từ tin nhắn cuối của lịch sử chat. Integration chấp nhận cả bộ trường chuẩn `ownerId`, `cliMsgId`, `globalMsgId` và alias thường có trong lịch sử `uidFrom`, `cliMsgId`, `msgId`.

Bản `2026.8.18.3` bổ sung bảo vệ Zalo ID lớn ở service schema và trước khi JSON hóa request, hỗ trợ cú pháp template-safe `zalo:<id>`, đồng thời tách `ttl` của action gửi tin thành TTL của **chính tin nhắn**. Server v1.2.1 cũng trả webhook message thêm `_threadRef` và `_threadType` để automation Home Assistant có thể giữ ID ở dạng text từ đầu đến cuối.

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
| `Markdown Color` | Màu mặc định áp dụng cho các đoạn **bold** Markdown: `none`, `red`, `orange`, `yellow`, `green`. Màu inline `{red}...{/red}`... có ưu tiên cao hơn. |
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

### Lưu ý khi gửi video

Với Zalo Bot Server `1.2.2+`, video local của Home Assistant được phục vụ tạm thời chỉ để server tải nguồn; server sau đó re-upload video lên Zalo và gửi bằng URL do Zalo cấp. Cách này tránh lỗi video biến mất khi URL local hết hạn. Với Server `1.2.3+`, `thumbnail_url` có thể bỏ hẳn: server sẽ tự trích một frame JPEG từ video và upload làm thumbnail. Chỉ truyền `thumbnail_url` khi muốn dùng ảnh preview tùy chỉnh.

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

## Zalo ID lớn và `thread_id` trong automation

Zalo `threadId`, `userId`, `groupId`, `msgId`... thường lớn hơn giới hạn số nguyên an toàn của JavaScript (`2^53 - 1`). Vì vậy **ID phải được giữ ở dạng chuỗi** khi đi qua Home Assistant, JSON và Node.js. Integration v2026.8.18.3 chuẩn hóa các field ID của toàn bộ action về chuỗi **trước khi request rời Python**, nên Python integer vẫn được giữ đủ chữ số; server v1.2.1 cũng từ chối ID dạng JSON number không an toàn thay vì âm thầm dùng giá trị đã làm tròn.

Home Assistant có thể parse kết quả template chỉ gồm chữ số thành kiểu số, và giao diện trace/browser có thể hiển thị số lớn đã làm tròn. Để giữ chắc chắn là text ngay từ bước template, dùng dạng **template-safe** `zalo:<id>`. Integration/server sẽ tự bỏ tiền tố `zalo:` trước khi gọi `zca-js`.

Server v1.2.1 thêm hai field tương thích ngược vào webhook message:

- `_threadRef`: ví dụ `zalo:2036121378794772276` — an toàn khi đưa qua template Home Assistant.
- `_threadType`: `0` = User, `1` = Group — nên truyền thẳng vào action thay vì hard-code.

Ví dụ automation webhook an toàn:

```yaml
- variables:
    user_message: "{{ trigger.json.data.content }}"
    zalo_thread_ref: "{{ trigger.json._threadRef | default('zalo:' ~ trigger.json.threadId, true) }}"
    zalo_thread_type: "{{ trigger.json._threadType | default(trigger.json.type, true) }}"
    ai_conversation_id: "{{ trigger.json._threadRef | default('zalo:' ~ trigger.json.threadId, true) }}"

- action: conversation.process
  data:
    text: "{{ user_message }}"
    conversation_id: "{{ ai_conversation_id }}"
    agent_id: conversation.gemini_flash_ai_agent_tienphuoc
    language: vi
  response_variable: convo_response

- action: zalo_bot.send_message
  data:
    message: "{{ convo_response.response.speech.plain.speech }}"
    thread_id: "{{ zalo_thread_ref }}"
    type: "{{ zalo_thread_type }}"
    account_selection: "+84376861184"
```

Nếu chưa nâng server lên v1.2.1, có thể tạo giá trị an toàn trực tiếp:

```yaml
thread_id: "zalo:{{ trigger.json.threadId }}"
type: "{{ trigger.json.type }}"
```

> Không dùng `| int` hoặc `| float` cho bất kỳ Zalo ID nào. `conversation_id` của `conversation.process` cũng nên có tiền tố `zalo:` để tránh biến một ID chỉ gồm chữ số thành number trong trace/template.

> **Quan trọng với automation trong trace:** nếu webhook có `type: 0` thì đó là hội thoại User; không được hard-code `type: "1"`. Hãy dùng `_threadType`/`trigger.json.type`. Với group, `data.uidFrom` là ID người gửi; ID conversation để trả lời là `threadId` ở cấp root của webhook.

## Format text / Rich text Zalo

Format text được xử lý **chỉ khi entity `Markdown` đang bật**. Integration giữ nguyên cú pháp Markdown đã có và bổ sung các style mà `zca-js 2.1.2` hỗ trợ chính thức. Khi gửi lên server, `start` và `len` của từng style được tính theo **UTF-16 code unit giống JavaScript/Zalo**, vì vậy emoji như `😀`, `🔥`, ký tự ngoài BMP... không làm lệch vị trí format của phần text phía sau.

### Cú pháp hỗ trợ

| Cú pháp nhập | Kết quả trên Zalo | Ghi chú |
|---|---|---|
| `**nội dung**` | **Đậm** | Giữ nguyên cú pháp cũ. |
| `*nội dung*` | *Nghiêng* | Giữ nguyên cú pháp cũ. |
| `***nội dung***` | **Đậm + nghiêng** | Có thể lồng với màu/kích thước. |
| `__nội dung__` | Gạch chân | Giữ nguyên cú pháp cũ. |
| `~~nội dung~~` | Gạch ngang | Giữ nguyên cú pháp cũ. |
| `` `nội dung` `` | Nghiêng | Giữ hành vi tương thích của integration cũ. Markdown bên trong đoạn này không được parse tiếp. |
| `# Tiêu đề` | Chữ lớn + đậm | Zalo/zca-js 2.1.2 chỉ có cỡ `Big (f_18)` và `Small (f_13)`; không dùng token `f_20`. |
| `## Tiêu đề` | Chữ lớn + đậm | Kết hợp `f_18` + `b`. |
| `### Tiêu đề` | Đậm | |
| `####` đến `######` | Chữ nhỏ | Dùng `f_13`. |
| `> nội dung` | Nghiêng | Giữ hành vi blockquote cũ của integration. |
| `[nhãn](https://...)` | URL | Giữ hành vi tương thích cũ: phần hiển thị được thay bằng URL. |
| `{red}nội dung{/red}` | Chữ đỏ | Màu Zalo hỗ trợ chính thức. |
| `{orange}nội dung{/orange}` | Chữ cam | Màu Zalo hỗ trợ chính thức. |
| `{yellow}nội dung{/yellow}` | Chữ vàng | Màu Zalo hỗ trợ chính thức. |
| `{green}nội dung{/green}` | Chữ xanh lá | Màu Zalo hỗ trợ chính thức. |
| `{big}nội dung{/big}` | Chữ lớn | `f_18`. |
| `{small}nội dung{/small}` | Chữ nhỏ | `f_13`. |
| `- Mục`, `* Mục`, `+ Mục` | Danh sách bullet | Marker đầu dòng được bỏ khỏi text và chuyển thành style `lst_1`. |
| `1. Mục`, `2. Mục` | Danh sách đánh số | Cũng chấp nhận `1) Mục`; chuyển thành `lst_2`. |
| 1–8 khoảng trắng ở đầu dòng | Thụt lề | Chuyển thành `ind_$` + `indentSize`; tab được tính như 4 khoảng trắng. |

> `Markdown Color` là màu mặc định cho các đoạn **bold**. Nếu một đoạn có màu inline như `{red}...{/red}`, màu inline được ưu tiên để tránh hai màu xung đột trên cùng vùng text.

### Kết hợp nhiều format

Có thể lồng format, ví dụ:

```text
{red}**CẢNH BÁO**{/red}
{green}***Hệ thống hoạt động bình thường***{/green}
{big}**NHIỆT ĐỘ CAO 🔥**{/big}
{small}Ghi chú nhỏ{/small}
```

Danh sách và indent:

```text
- Thiết bị tầng 1
  - Phòng khách 😀
  - Phòng bếp
- Thiết bị tầng 2

1. Kiểm tra cửa
2. Kiểm tra camera
  1. Camera cổng
  2. Camera sân
```

Trong automation Home Assistant, nên dùng YAML block `|` để giữ nguyên xuống dòng và khoảng trắng đầu dòng:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "1"
  message: |
    {red}**CẢNH BÁO 🔥**{/red}
    Nhiệt độ đang cao.

    - Phòng khách
      - Cảm biến 1
      - Cảm biến 2

    {small}Tin nhắn tự động từ Home Assistant{/small}
```

### Lưu ý

- Chỉ các màu `red`, `orange`, `yellow`, `green` được dùng vì đây là các token màu được `zca-js 2.1.2` định nghĩa. Integration không tự tạo màu HEX tùy ý.
- Có thể escape tag format để gửi nguyên văn, ví dụ `\{red}` sẽ hiển thị `{red}` thay vì bắt đầu màu đỏ.
- Marker Markdown không đóng sẽ được giữ như text thường thay vì bị xóa.
- Rich text hiện áp dụng cho action `zalo_bot.send_message`. Các action media/caption có luồng API khác và không được giả định sẽ render `styles` giống tin nhắn text.
- Parser chỉ chạy khi gọi action gửi tin nhắn, được đưa qua Home Assistant executor để cả message format lớn cũng không giữ event loop; không tạo network/filesystem I/O hoặc công việc nền khi Home Assistant khởi động.

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

## TTL tin nhắn và Auto Delete cuộc trò chuyện

Hai khái niệm này **được tách riêng** trong v2026.8.18.3/v1.2.1:

1. `ttl` trên các action gửi tin/media là thời gian tự xóa của **chính tin nhắn đang gửi**.
2. `zalo_bot.update_auto_delete_chat` thay đổi **Auto Delete của cả cuộc trò chuyện**.

### TTL của từng tin nhắn

UI cung cấp các lựa chọn:

```text
off
1h, 2h, 3h, ... 24h
1d
7d
14d
```

Các action hỗ trợ gồm `send_message`, `send_file`, `send_image`, `send_image_to_user`, `send_images_to_user`, `send_image_to_group`, `send_images_to_group`, `send_video` và `send_voice`. Giá trị được chuẩn hóa thành milliseconds trước khi gửi tới `zca-js`. YAML cũng có thể truyền trực tiếp số milliseconds không âm.

Ví dụ tin nhắn tự xóa sau 6 giờ:

```yaml
action: zalo_bot.send_message
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "0"
  message: "Tin nhắn này có TTL 6 giờ"
  ttl: "6h"
```

Bỏ trường `ttl` nếu không muốn đặt TTL cho tin đang gửi. `ttl: off`/`0` gửi giá trị TTL bằng 0 cho message; nó **không** thay đổi cài đặt Auto Delete của conversation.

### Auto Delete của cả cuộc trò chuyện

Action riêng `zalo_bot.update_auto_delete_chat` chỉ dùng các mốc mà `zca-js 2.1.2` công khai cho `ChatTTL`:

```text
off / 0
1d  / 86400000
7d  / 604800000
14d / 1209600000
```

Ví dụ tắt Auto Delete của conversation:

```yaml
action: zalo_bot.update_auto_delete_chat
data:
  account_selection: "+84123456789"
  thread_id: "5841349563795164131"
  type: "0"
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

## Tương thích với Zalo Bot Server v1.2.1

Toàn bộ action hiện có đã được rà soát lại với server v1.2.1 (`zca-js` 2.1.2). Ngoài các endpoint tương thích từ các bản trước, bản này đặc biệt đồng bộ:

- `create_note_group` → `/api/createNoteByAccount`
- `edit_note_group` → `/api/editNoteByAccount`
- `get_quick_message` → `/api/getQuickMessageListByAccount`
- `undo_message` → `/api/undoByAccount`
- `get_received_friend_requests` → `/api/getReceivedFriendRequestsByAccount`
- `get_group_chat_history` → `/api/getGroupChatHistoryByAccount`
- Account webhook API.
- Proxy API.
- Per-message TTL 1h–24h/1d/7d/14d và Auto Delete conversation tách riêng.
- Zalo ID lớn luôn đi qua request ở dạng string; hỗ trợ `zalo:<id>`, `_threadRef` và `_threadType`.
- Multi-image sending giữ đúng thứ tự attachment.

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

## Phát hành bản cập nhật qua HACS

Repository dùng GitHub Release asset `zalo_bot.zip`. HACS sẽ giải nén asset này trực tiếp vào `/config/custom_components/zalo_bot`, vì vậy `manifest.json` và `__init__.py` nằm ngay ở root của ZIP phát hành.

### Cách khuyến nghị: chạy workflow thủ công

Vào **GitHub → Actions → Build and Publish HACS Release → Run workflow**, nhập version không có chữ `v`, ví dụ `2026.08.19.0900`. Workflow sẽ tự cập nhật `manifest.json`, commit lên `main`, tạo tag `v2026.08.19.0900`, kiểm tra cấu trúc/compile, tạo `zalo_bot.zip` và tạo GitHub Release.

### Nếu tự tạo tag bằng Git

Trước khi tạo tag, bắt buộc `custom_components/zalo_bot/manifest.json` đã có version trùng với tag (bỏ chữ `v`). Ví dụ tag `v2026.08.19.0900` phải đi cùng `"version": "2026.08.19.0900"`. Workflow sẽ dừng và không publish release nếu hai giá trị lệch nhau.

Không sửa hoặc force-move một tag sau khi Release đã được publish. Khi cần sửa, hãy tạo một version/tag mới.
