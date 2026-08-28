# pixel-beads 会员兑换码验证服务

部署在 Cloudflare Workers（免费），兑换码一次性校验 + 绑定设备，防分享复用。

## 部署步骤

### 1. 创建 Worker
- 登录 https://dash.cloudflare.com → Workers & Pages → Create application → Workers → Create Worker
- 命名随意，比如 `pixel-beads-member`
- 部署后会得到一个域名：`https://pixel-beads-member.<你的账号>.workers.dev`

### 2. 绑定 KV 存储
- 在 Worker 设置 → KV 命名空间 → Add binding
- **Variable name 必须填 `MEMBER_KV`**（和 worker.js 里一致）
- Namespace name 随便

### 3. 设置环境变量
在 Worker 设置 → Variables and Secrets 里添加：
- `SECRET` = 你自己定的一串密码（至少 32 位，比如用 `openssl rand -hex 32` 生成）。**这个丢了就没办法生成匹配的兑换码了，保管好。**
- `ADMIN_PASS` = 管理密码，`POST /admin/import` 灌码时用

### 4. 上传代码
把 `worker.js` 内容贴进 Worker 编辑器，部署。

### 5. 生成兑换码
在你本地跑（需要 Python 3.8+）：
```bash
python server/gen_codes.py --secret <你的SECRET> --prefix VIP --month 20 --year 10
```
会在 `server/codes.json` 生成兑换码表，终端也会打印每个码和到期日。

### 6. 灌入 KV
```bash
python server/import_kv.py --url https://pixel-beads-member.<你的账号>.workers.dev --admin-pass <管理密码> --codes server/codes.json
```
返回 `{"ok": true, "imported": 30}` 表示成功。

### 7. 更新客户端
打开 `member.py`，把 `VERIFY_URL` 改成你的 Worker 地址：
```python
VERIFY_URL = "https://pixel-beads-member.<你的账号>.workers.dev/api/activate"
```
重新打包 exe。

## 接口

- `POST /api/activate`  body: `{"code": "VIP2026A", "device_id": "1234..."}`
  返回：`{"ok": true, "expire_at": "2027-08-28T00:00:00+00:00"}` 或 `{"ok": false, err": "invalid|used|bound_other"}`
- `POST /admin/import`  header: `X-Admin-Pass`  body: `[{"code": "VIP2026A", "expire_at": "..."}]`

## 安全说明
- 兑换码以 HMAC-SHA256(secret, code) 的前 16 位作为 KV key，KV 里存不到原始码。
- SECRET 存在 Worker 环境变量，不入库、不进 exe。
- 每个码只能绑定一个 device_id，换设备无效。
