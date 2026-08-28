# -*- coding: utf-8 -*-
"""把 gen_codes.py 生成的 codes.json 通过 /admin/import 灌进 Worker。

用法：
    python server/import_kv.py \
        --url https://pixel-beads-member.aeb73d53.workers.dev \
        --admin-pass <管理密码> \
        --codes server/codes.json
"""
import argparse
import json
import sys
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Worker 地址（不要带路径）")
    ap.add_argument("--admin-pass", required=True)
    ap.add_argument("--codes", default="server/codes.json")
    args = ap.parse_args()

    with open(args.codes, "r", encoding="utf-8") as f:
        entries = json.load(f)

    payload = [{"code": e["code"], "expire_at": e["expire_at"]} for e in entries]
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        args.url.rstrip("/") + "/admin/import",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Admin-Pass": args.admin_pass,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP ERROR", e.code, e.read().decode("utf-8", errors="replace"))
        sys.exit(1)


if __name__ == "__main__":
    main()
