# -*- coding: utf-8 -*-
"""会员状态管理（供未来付费功能接入，现有功能不受影响）。

对外接口：
    get_device_id() -> str           本机 16 位指纹
    expire_at() -> str | None        会员到期 ISO 时间，无会员则 None
    is_active() -> bool              未过期 = True
    is_expired() -> bool             曾经开通但已过期 = True
    set_expire_at(ts: str)           写入到期时间（激活成功后调用）

会员状态存在 user_settings.json 的 "member" 字段下，永不入库、不上传。
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import uuid
from datetime import datetime, timezone

import sys

# 与服务端 /api/activate 通信的地址（部署后改成真实域名）
VERIFY_URL = "https://pixel-beads-member.aeb73d53.workers.dev/api/activate"

# 会员价格文案（展示用）
PRICE = "9.9 元/月 · 29 元/年"

# ---- 与 gui.py 共享 user_settings.json ----


def _settings_path() -> str:
    """与 gui.py 的 storage_dir() 保持一致：exe 版与 exe 同级，源码版与脚本同级。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "user_settings.json")


def _load_settings() -> dict:
    p = _settings_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(data: dict):
    p = _settings_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---- 设备指纹 ----


def _make_device_id() -> str:
    parts = [
        str(uuid.getnode()),
        platform.processor() or "",
        platform.node() or "",
        os.getenv("USERNAME") or os.getenv("USER") or "",
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_device_id() -> str:
    s = _load_settings()
    did = (s.get("member") or {}).get("device_id")
    if did:
        return did
    did = _make_device_id()
    s.setdefault("member", {})["device_id"] = did
    _save_settings(s)
    return did


# ---- 会员状态 ----


def expire_at() -> str | None:
    s = _load_settings()
    return (s.get("member") or {}).get("expire_at")


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        # 兼容带/不带时区
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def is_active() -> bool:
    ts = expire_at()
    dt = _parse(ts)
    if dt is None:
        return False
    now = datetime.now(timezone.utc) if dt.tzinfo else datetime.utcnow()
    return now < dt


def is_expired() -> bool:
    ts = expire_at()
    if not ts:
        return False  # 从没开通不算过期
    dt = _parse(ts)
    if dt is None:
        return False
    now = datetime.now(timezone.utc) if dt.tzinfo else datetime.utcnow()
    return now >= dt


def set_expire_at(ts: str) -> None:
    """激活成功后写入到期时间。"""
    s = _load_settings()
    s.setdefault("member", {})["expire_at"] = ts
    _save_settings(s)


def clear_member() -> None:
    s = _load_settings()
    s.pop("member", None)
    _save_settings(s)


# 格式化显示用
def _fmt(ts: str | None) -> str:
    dt = _parse(ts)
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d")
