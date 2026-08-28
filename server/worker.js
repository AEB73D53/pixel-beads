/**
 * pixel-beads 会员兑换码验证 — Cloudflare Worker
 *
 * 部署:
 *   1. 在 Cloudflare Dashboard 创建 Worker，绑定一个 KV namespace，命名空间名填 MEMBER_KV。
 *   2. 在 Worker 环境变量里设:
 *        SECRET = 你自己定的一串密码（至少 32 位，用于 HMAC）
 *        ADMIN_PASS = 管理密码（POST /admin/import 用）
 *   3. 把下面代码贴进去，部署。
 *   4. 本地跑 `python server/gen_codes.py --secret <SECRET>` 生成兑换码表，
 *      用 `python server/import_kv.py` 或通过 /admin/import 灌进 KV。
 *
 * 接口:
 *   POST /api/activate  body: {code, device_id}  → {ok, expire_at, err}
 *   POST /admin/import  header: X-Admin-Pass  body: [{code, expire_at}]
 */

const KV_NAME = "MEMBER_KV";  // 与 Dashboard 绑定的 KV namespace 名一致

async function hmacSha256(secret, msg) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(msg));
  return Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

async function handleActivate(req, env) {
  const kv = env[KV_NAME];
  const secret = env.SECRET;
  if (!secret) return json({ ok: false, err: "server misconfigured" });

  let body;
  try { body = await req.json(); }
  catch { return json({ ok: false, err: "bad json" }); }

  const raw = (body.code || "").trim().toUpperCase();
  const deviceId = (body.device_id || "").trim();
  if (!raw || !deviceId) return json({ ok: false, err: "missing code or device_id" });

  const key = await hmacSha256(secret, raw);
  const entry = await kv.get(key, { type: "json" });

  if (!entry) {
    return json({ ok: false, err: "invalid" });
  }
  if (entry.used) {
    if (entry.bound_device === deviceId && !entry.expired) {
      return json({ ok: true, expire_at: entry.expire_at });  // 同一设备重复请求：放行
    }
    return json({ ok: false, err: entry.bound_device !== deviceId ? "bound_other" : "used" });
  }

  await kv.put(key, JSON.stringify({
    ...entry,
    used: true,
    bound_device: deviceId,
    used_at: new Date().toISOString(),
  }));

  return json({ ok: true, expire_at: entry.expire_at });
}

async function handleAdminImport(req, env) {
  const kv = env[KV_NAME];
  const pass = req.headers.get("X-Admin-Pass") || "";
  if (pass !== env.ADMIN_PASS) return json({ ok: false, err: "forbidden" });

  let body;
  try { body = await req.json(); }
  catch { return json({ ok: false, err: "bad json" }); }

  if (!Array.isArray(body)) return json({ ok: false, err: "expect array" });

  const secret = env.SECRET;
  const results = [];
  for (const item of body) {
    const raw = (item.code || "").trim().toUpperCase();
    const expireAt = item.expire_at;
    if (!raw || !expireAt) { results.push({ code: raw, err: "skip" }); continue; }
    const key = await hmacSha256(secret, raw);
    await kv.put(key, JSON.stringify({
      code: raw,
      expire_at: expireAt,
      used: false,
      bound_device: null,
    }));
    results.push({ code: raw, ok: true });
  }
  return json({ ok: true, imported: results.length });
}

async function handleRequest(request) {
  const url = new URL(request.url);
  if (url.pathname === "/api/activate" && request.method === "POST") {
    return handleActivate(request, request.env);
  }
  if (url.pathname === "/admin/import" && request.method === "POST") {
    return handleAdminImport(request, request.env);
  }
  return new Response("pixel-beads member verify", { status: 200 });
}

export default { fetch: handleRequest };

function json(obj) {
  return new Response(JSON.stringify(obj), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type, X-Admin-Pass",
    },
  });
}
