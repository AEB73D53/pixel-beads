# -*- coding: utf-8 -*-
"""生成本地兑换码表（JSON），再导入到 Cloudflare KV。

用法：
    # 生成 10 张月卡、5 张年卡，到期时间从今天算起
    python server/gen_codes.py --secret <你的SECRET> --month 10 --year 5 --prefix VIP

    # 指定到期时间（覆盖自动计算）
    python server/gen_codes.py --secret <SECRET> --codes VIP2026A,2027-08-28T00:00:00,VIP2026B,2027-08-28T00:00:00

输出 codes.json（当前目录），然后用 import_kv.py 或 Worker 的 /admin/import 灌进去。
"""
import argparse
import hashlib
import json
import os
import string
from datetime import datetime, timedelta, timezone


def hmac_key(secret: str, code: str) -> str:
    import hmac
    return hmac.new(secret.encode(), code.upper().encode(), hashlib.sha256).hexdigest()[:16]


def random_code(prefix: str, n: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(chars[i % len(chars)] for i in range(n))
    # 上面用确定性写法避免 random 不可控；实际每次不同因为 prefix 不变——改用随机：


def _rand(n: int) -> str:
    import secrets
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(n))


def make_code(prefix: str) -> str:
    return prefix + _rand(6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret", required=True)
    ap.add_argument("--prefix", default="VIP")
    ap.add_argument("--month", type=int, default=0, help="生成多少张月卡")
    ap.add_argument("--year", type=int, default=0, help="生成多少张年卡")
    ap.add_argument("--codes", help="逗号分隔：code,expire_at,code,expire_at...")
    ap.add_argument("--out", default="server/codes.json")
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

    # 计算每个码对应的 KV key（仅本地预览用，真正 key 由 Worker 用同一 secret 算）
    for e in entries:
        e["kv_key"] = hmac_key(args.secret, e["code"])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"generated {len(entries)} codes -> {args.out}")
    for e in entries:
        print(f"  {e['code']}  expires {e['expire_at'][:10]}")


if __name__ == "__main__":
    main()
