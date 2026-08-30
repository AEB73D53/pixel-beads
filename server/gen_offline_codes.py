# -*- coding: utf-8 -*-
"""生成离线会员兑换码表（打包进 exe，纯本地校验）。

用法：
    # 生成 20 个月卡、10 个年卡（到期时间自动算）
    python server/gen_offline_codes.py --secret <你的SECRET> --month 20 --year 10

    # 指定到期时间
    python server/gen_offline_codes.py --secret <SECRET> --codes VIP2026A,2027-08-28T00:00:00,VIP2026B,2027-08-28T00:00:00

输出：
    server/offline_codes.json  —— 加密后的码表，打包进 exe
    server/codes.txt           —— 明文兑换码清单（你自己保管，发给用户用）

安全说明：
    - 码表的 key 是 HMAC-SHA256(secret, code) 的前 16 位，KV 里存不到原始码。
    - SECRET 存在脚本里（不入库），丢了就没法生成匹配的码。
    - 这是纯离线校验，码可被反编译获取；前期量少够用，量大后换联网校验。
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import string
from datetime import datetime, timedelta, timezone


def _rand(n: int) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(n))


_XOR_KEY = "pixel-beads-2026-mem-secret-v1"


def make_code(prefix: str) -> str:
    return prefix + _rand(6)


def hmac_key(secret: str, code: str) -> str:
    return hmac.new(secret.encode(), code.upper().encode(), hashlib.sha256).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret", required=True)
    ap.add_argument("--prefix", default="VIP")
    ap.add_argument("--month", type=int, default=0, help="月卡数量")
    ap.add_argument("--year", type=int, default=0, help="年卡数量")
    ap.add_argument("--codes", help="逗号分隔：code,expire_at,code,expire_at...")
    ap.add_argument("--out_encrypted", default="server/offline_codes.json")
    ap.add_argument("--out-plaintext", default="server/codes.txt")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    entries = []

    if args.codes:
        parts = [c.strip() for c in args.codes.split(",") if c.strip()]
        for i in range(0, len(parts), 2):
            entries.append({
                "code": parts[i].upper(),
                "expire_at": parts[i + 1] if i + 1 < len(parts) else "",
            })

    for _ in range(args.month):
        entries.append({
            "code": make_code(args.prefix),
            "expire_at": (now + timedelta(days=30)).isoformat(),
        })
    for _ in range(args.year):
        entries.append({
            "code": make_code(args.prefix),
            "expire_at": (now + timedelta(days=365)).isoformat(),
        })

    # 加密后的码表（打包进 exe）
    encrypted = {
        "v": 1,
        "entries": [
            {"key": hmac_key(args.secret, e["code"]),
             "expire_at": e["expire_at"]}
            for e in entries
        ],
    }
    # XOR + base64 两层，防直接 cat 看到
    raw_bytes = json.dumps(encrypted, ensure_ascii=False).encode("utf-8")
    xored = bytes(b ^ _XOR_KEY.encode("utf-8")[i % len(_XOR_KEY)]
                  for i, b in enumerate(raw_bytes))
    blob = base64.b64encode(xored).decode()
    with open(args.out_encrypted, "w", encoding="utf-8") as f:
        f.write(blob)
    print(f"encrypted table -> {args.out_encrypted} ({os.path.getsize(args.out_encrypted)} bytes)")

    # 明文清单（你自己保管）
    with open(args.out_plaintext, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(f"{e['code']}  expires {e['expire_at'][:10]}\n")
    print(f"plaintext codes -> {args.out_plaintext} ({len(entries)} codes)")


if __name__ == "__main__":
    main()
