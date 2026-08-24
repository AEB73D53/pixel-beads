# -*- coding: utf-8 -*-
"""拼豆色卡数据。MVP 内置若干常用/通用拼豆色（含国产常见品牌相近似名），
真实品牌色号请参照对应品牌色卡表核对。用户可在“色卡(编辑)”中自行增改。"""

import json
import os
import sys

COLOR_FAMILIES = {
    "常用色": [
        "白色", "浅粉", "粉色", "玫红", "大红", "酒红", "橙红", "橙色", "杏黄", "金黄",
        "浅黄", "柠檬黄", "米色", "浅棕", "棕色", "深棕", "咖啡", "肤色", "浅绿", "苹果绿",
        "草绿", "深绿", "墨绿", "青绿", "薄荷绿", "浅蓝", "天蓝", "宝蓝", "藏青", "深蓝",
        "浅紫", "紫色", "紫罗兰", "蓝紫", "灰色", "浅灰", "中灰", "深灰", "黑色", "墨灰",
    ],
    "更多颜色": [
        "乳白", "奶油", "米黄", "沙色", "驼色", "巧克力", "栗色", "焦糖",
        "粉白", "蔷薇粉", "珊瑚粉", "桃粉", "绯红", "铁锈红", "藕荷",
        "橘黄", "南瓜橙", "琥珀", "奶茶色", "芥末黄", "青柠",
        "橄榄绿", "松石绿", "湖蓝", "雾蓝", "黛蓝", "电光蓝",
        "香芋紫", "藕紫", "霓虹紫", "水泥灰", "烟灰", "炭黑",
        "浅银", "深银", "原木", "乳酪", "樱花", "薰衣草",
    ],
}


def rgba_hex(color: str) -> str:
    hx = _COLOR_HEX.get(color)
    if hx is None:
        hx = _CUSTOM_HEX.get(color)
    return hx or "#888888"


# --------------------------------------------------------------------------
# 用户自定义颜色 / 色卡（持久化到 user_palettes.json，支持导入真实品牌色号）
# --------------------------------------------------------------------------

_CUSTOM_HEX = {}          # 用户新增颜色：颜色名 -> hex
_USER_PALETTES = []       # 用户色卡：[{"name": ..., "colors": [...]}]


def user_data_path() -> str:
    """用户数据文件路径：打包版(exe)放在可执行文件同级，源码版放在 palettes.py 同级。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "user_palettes.json")


def _known_colors():
    return set(_COLOR_HEX) | set(_CUSTOM_HEX)


def _clean_colors(colors):
    """去掉未知颜色与重复项。"""
    known = _known_colors()
    out = []
    for c in colors:
        c = str(c).strip()
        if c in known and c not in out:
            out.append(c)
    return out


def load_user_data(path=None):
    """从磁盘读取自定义颜色与用户色卡（幂等，可重复调用）。"""
    global _CUSTOM_HEX, _USER_PALETTES
    _CUSTOM_HEX = {}
    _USER_PALETTES = []
    p = path or user_data_path()
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return  # 无文件或损坏则静默使用内置色卡
    for k, v in (data.get("custom_colors") or {}).items():
        if isinstance(v, str) and v.startswith("#"):
            _CUSTOM_HEX[str(k)] = v
    for pal in data.get("palettes") or []:
        name = str(pal.get("name", "")).strip()
        colors = _clean_colors(pal.get("colors") or [])
        if name and colors:
            _USER_PALETTES.append({"name": name, "colors": colors})


def save_user_data(custom_hex=None, user_palettes=None, path=None):
    """保存自定义颜色与用户色卡到磁盘；不传参数则使用内存当前值。"""
    global _CUSTOM_HEX, _USER_PALETTES
    if custom_hex is not None:
        _CUSTOM_HEX = dict(custom_hex)
    if user_palettes is not None:
        _USER_PALETTES = list(user_palettes)
    data = {"custom_colors": _CUSTOM_HEX, "palettes": _USER_PALETTES}
    p = path or user_data_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_palettes():
    """供界面使用的全部色卡：内置 + 用户自定义。"""
    return BUILT_IN_PALETTES + [dict(p) for p in _USER_PALETTES]


def all_color_names():
    """全部可用颜色名（内置 + 自定义）。"""
    return sorted(_known_colors())


def custom_colors():
    """返回自定义颜色（名 -> hex）副本。"""
    return dict(_CUSTOM_HEX)


def add_custom_color(name: str, hex_value: str, path=None):
    """新增/覆盖一个自定义颜色并持久化。hex_value 形如 '#E60012'。"""
    custom = dict(_CUSTOM_HEX)
    custom[name] = hex_value
    save_user_data(custom_hex=custom, path=path)


def import_palettes_data(data, path=None) -> int:
    """导入任意结构色卡数据，返回成功导入的色卡数。

    支持：
      {"name": ..., "colors": [已有颜色名, ...]}         引用已有颜色
      {"name": ..., "hexes": {颜色名: "#RRGGBB", ...}}   自带真实色号（自动注册自定义颜色）
      {"palettes": [上述任意结构, ...]}                  批量
    未知颜色名会被忽略；导入后立即持久化。
    """
    if not isinstance(data, dict):
        return 0
    palettes_data = data.get("palettes") if "palettes" in data else [data]
    hexes = data.get("hexes") if isinstance(data.get("hexes"), dict) else None
    custom = dict(_CUSTOM_HEX)
    if hexes:
        for k, v in hexes.items():
            if isinstance(v, str) and v.startswith("#"):
                custom[str(k)] = v
    user = [q for q in _USER_PALETTES]
    unames = {q["name"] for q in user}
    added = 0
    for pal in palettes_data:
        if not isinstance(pal, dict):
            continue
        name = str(pal.get("name", "")).strip()
        if not name:
            continue
        if hexes is not None:
            colors = list(hexes.keys())
        else:
            known = _known_colors()
            colors = [str(c).strip() for c in (pal.get("colors") or [])
                      if str(c).strip() in known]
        if not colors:
            continue
        if name in unames:
            for q in user:
                if q["name"] == name:
                    q["colors"] = colors
        else:
            user.append({"name": name, "colors": colors})
            unames.add(name)
        added += 1
    if added:
        save_user_data(custom_hex=custom, user_palettes=user, path=path)
    return added


# 颜色名 -> 十六进制颜色（用于渲染与标注）。可用“色卡编辑”修改。
_COLOR_HEX = {
    "白色": "#FFFFFF", "浅粉": "#F8C8DC", "粉色": "#F4A7B9", "玫红": "#E75480",
    "大红": "#E60012", "酒红": "#722F37", "橙红": "#FF4500", "橙色": "#FF8C00",
    "杏黄": "#FBCEB1", "金黄": "#FFC20E", "浅黄": "#FFF3B0", "柠檬黄": "#F6F33C",
    "米色": "#F5F0DC", "浅棕": "#C9A97C", "棕色": "#8B5A2B", "深棕": "#5C3A21",
    "咖啡": "#6F4E37", "肤色": "#FDBCB4", "浅绿": "#B6E388", "苹果绿": "#98FB98",
    "草绿": "#7FD84A", "深绿": "#2E8B57", "墨绿": "#1F5934", "青绿": "#40E0D0",
    "薄荷绿": "#98FF98", "浅蓝": "#ADD8E6", "天蓝": "#6CB4EE", "宝蓝": "#1E50A2",
    "藏青": "#2E3A59", "深蓝": "#0A2463", "浅紫": "#D8BFD8", "紫色": "#7B5EA7",
    "紫罗兰": "#8A2BE2", "蓝紫": "#6A5ACD", "灰色": "#808080", "浅灰": "#C0C0C0",
    "中灰": "#A9A9A9", "深灰": "#555555", "黑色": "#1C1C1C", "墨灰": "#3D3D3D",
    "乳白": "#FFFDF5", "奶油": "#FFFDD0", "米黄": "#F5DEB3", "沙色": "#D8C3A5",
    "驼色": "#A0797B", "巧克力": "#7B3F00", "栗色": "#954535", "焦糖": "#C58F5D",
    "粉白": "#FFF0F5", "蔷薇粉": "#F7B5C8", "珊瑚粉": "#F88379", "桃粉": "#FADADD",
    "绯红": "#DC143C", "铁锈红": "#B7410E", "藕荷": "#F0D3C5",
    "橘黄": "#FFA500", "南瓜橙": "#FF7518", "琥珀": "#FFBF00", "奶茶色": "#D2B48C",
    "芥末黄": "#C5A52F", "青柠": "#BFFF00",
    "橄榄绿": "#556B2F", "松石绿": "#40E0D0", "湖蓝": "#4FB3D9", "雾蓝": "#A2C8DB",
    "黛蓝": "#1E3F66", "电光蓝": "#2D5FDB",
    "香芋紫": "#C8A2C8", "藕紫": "#C7A6C5", "霓虹紫": "#9B5DE5",
    "水泥灰": "#D3D3D3", "烟灰": "#6B6B6B", "炭黑": "#2B2B2B",
    "浅银": "#E5E4E2", "深银": "#6E6E6E", "原木": "#C19A6B", "乳酪": "#FFF5C3",
    "樱花": "#FFC9DE", "薰衣草": "#B57EDC",
}


BUILT_IN_PALETTES = [
    {
        "name": "常用色卡（泛品牌）",
        "desc": "40 个最常见的拼豆颜色，覆盖大多数图案需要；生成快、耗材种类少。",
        "colors": COLOR_FAMILIES["常用色"],
    },
    {
        "name": "进阶色卡（泛品牌）",
        "desc": "78 个颜色，接近照片原色的复现度更高，耗材种类也更多。",
        "colors": COLOR_FAMILIES["常用色"] + COLOR_FAMILIES["更多颜色"],
    },
]

# 启动时载入用户自定义颜色与色卡
load_user_data()