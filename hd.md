# Hướng dẫn gửi tin nhắn Zalo qua API

Server: `http://192.168.1.22:3000`
Tài khoản: `username / password`

---

## Đăng nhập

```
POST /api/login
```

```json
{"username": "your_username", "password": "your_password"}
```

---

## Gửi tin nhắn

```
POST /api/sendMessageByAccount
```

```json
{
  "message": {"msg": "xin chào bạn", "ttl": 0},
  "threadId": "your_thread_id",
  "accountSelection": "your_account_id",
  "type": 0
}
```

- `threadId`: ID user hoặc group nhận tin
- `accountSelection`: ownId tài khoản gửi
- `type`: `0` = user, `1` = group

---

## Ví dụ PowerShell

```powershell
# Đăng nhập
$body = @{username="your_username"; password="your_password"} | ConvertTo-Json
Invoke-RestMethod "http://192.168.1.22:3000/api/login" -Method POST -Body $body -ContentType "application/json" -SessionVariable z

# Gửi tin nhắn
$msg = @{message=@{msg="xin chào bạn"; ttl=0}; threadId="your_thread_id"; accountSelection="your_account_id"; type=0} | ConvertTo-Json -Depth 3
Invoke-RestMethod "http://192.168.1.22:3000/api/sendMessageByAccount" -Method POST -Body $msg -ContentType "application/json" -WebSession $z
```

## Ví dụ cURL

```bash
# Đăng nhập
curl -c cookie.txt -X POST http://192.168.1.22:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Gửi tin nhắn
curl -b cookie.txt -X POST http://192.168.1.22:3000/api/sendMessageByAccount \
  -H "Content-Type: application/json" \
  -d '{"message":{"msg":"xin chào bạn","ttl":0},"threadId":"your_thread_id","accountSelection":"your_account_id","type":0}'
```

## Ví dụ Python

```python
import requests
s = requests.Session()
s.post("http://192.168.1.22:3000/api/login", json={"username": "your_username", "password": "your_password"})
r = s.post("http://192.168.1.22:3000/api/sendMessageByAccount", json={
    "message": {"msg": "xin chào bạn", "ttl": 0},
    "threadId": "your_thread_id",
    "accountSelection": "your_account_id",
    "type": 0
})
print(r.json())
```

## Ví dụ Node.js

```js
const BASE = "http://192.168.1.22:3000";

// Đăng nhập
const res1 = await fetch(`${BASE}/api/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "your_username", password: "your_password" }),
});

// Gửi tin nhắn (cookie tự động gửi kèm)
const res2 = await fetch(`${BASE}/api/sendMessageByAccount`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: { msg: "xin chào bạn", ttl: 0 },
    threadId: "your_thread_id",
    accountSelection: "your_account_id",
    type: 0,
  }),
});
console.log(await res2.json());
```
