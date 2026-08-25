# -*- coding: utf-8 -*-
"""拼豆灵感库：扫描本地灵感目录 + 在线采集。

- scan():            扫描灵感目录，返回候选图列表（可含来源标注）
- record_source():   记录 {文件名: {url, keyword}} 到 sources.json
- fetch_from_web():  从 Bing 图片公开索引解析直链并限速下载
                     （含小红书/堆糖等平台的公开拼豆图，个人参考用途）

只依赖标准库 + Pillow，便于被打包。"""

import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from PIL import Image

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SOURCES_JSON = "sources.json"
_TIMEOUT = 15


def inspiration_dir():
    """灵感目录：打包版(exe)同级 /inspirations，源码版脚本同级。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "inspirations")


def data_dir():
    return inspiration_dir()


def ensure_bundled():
    """打包版首次运行时，把捆绑在 exe 里的灵感目录复制到 exe 旁可写目录。"""
    if not getattr(sys, "frozen", False):
        return
    extern = inspiration_dir()
    os.makedirs(extern, exist_ok=True)
    bundled = getattr(sys, "_MEIPASS", None)
    if not bundled:
        return
    src_dir = os.path.join(bundled, "inspirations")
    if not os.path.isdir(src_dir):
        return
    for fn in os.listdir(src_dir):
        if fn == SOURCES_JSON or fn.lower().endswith(_IMG_EXT):
            try:
                dst = os.path.join(extern, fn)
                if not os.path.exists(dst):
                    shutil.copy2(os.path.join(src_dir, fn), dst)
            except Exception:
                continue


# --------------------------------------------------------------------------
# 目录扫描与来源记录
# --------------------------------------------------------------------------

_IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")


def _sources_path(directory=None):
    return os.path.join(directory or inspiration_dir(), SOURCES_JSON)


def scan(directory=None):
    """扫描灵感目录，返回 [{name, path, source_url, keyword}, ...]。"""
    directory = directory or inspiration_dir()
    if getattr(sys, "frozen", False):
        ensure_bundled()            # 打包版：先补齐随包预置的灵感图
    src = {}
    try:
        with open(_sources_path(directory), encoding="utf-8") as f:
            src = json.load(f)          # {filename: {url, keyword}}
    except Exception:
        pass
    items = []
    if not os.path.isdir(directory):
        return items
    for fn in sorted(os.listdir(directory)):
        if not fn.lower().endswith(_IMG_EXT):
            continue
        path = os.path.join(directory, fn)
        name = os.path.splitext(fn)[0]
        meta = src.get(fn, {})
        items.append({
            "name": name,
            "path": path,
            "source_url": meta.get("url", ""),
            "keyword": meta.get("keyword", ""),
        })
    return items


def record_source(directory, filename, url, keyword):
    """把 {filename: {url, keyword}} 追加进 sources.json。"""
    path = _sources_path(directory)
    src = {}
    try:
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
    except Exception:
        pass
    src[filename] = {"url": url, "keyword": keyword}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 在线采集（Bing 图片公开索引直链解析，限速限量的个人参考用途）
# --------------------------------------------------------------------------

def _http_get(url, timeout=_TIMEOUT):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _parse_bing_murl(html):
    """从 Bing 图片页 HTML 里解析直链（实体转义形式与裸形式都要兼容）。"""
    if isinstance(html, (bytes, bytearray)):
        html = html.decode("utf-8", "ignore")
    urls = []
    # Bing 图片页实际编码：&quot;murl&quot;:&quot;https://...&quot;
    for m in re.finditer(r'murl&quot;:&quot;(https?://[^&"]+)', html):
        u = m.group(1).replace("\\/", "/").replace("&amp;", "&")
        if u.startswith("http"):
            urls.append(u)
    for m in re.finditer(r'"murl":"([^"]+)"', html):
        u = m.group(1).replace("\\/", "/").replace("&amp;", "&")
        if u.startswith("http"):
            urls.append(u)
    # 去重保序
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _encode_url(url):
    """清洗 URL：IDNA 域名编码 + 非 ASCII 路径/查询 quote，避免 http.client 报错。"""
    try:
        o = urllib.parse.urlsplit(url)
        net = o.netloc.encode("idna").decode("ascii")
        safe = "/:@!$&'()*+,;=~-._%"
        path = urllib.parse.quote(o.path, safe=safe)
        query = urllib.parse.quote(o.query, safe=safe + "?")
        return urllib.parse.urlunsplit((o.scheme, net, path, query, o.fragment))
    except Exception:
        return url


def _download_image(url, save_path, timeout=_TIMEOUT):
    url = _encode_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://cn.bing.com/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if len(data) < 2000:
        return False
    with open(save_path, "wb") as f:
        f.write(data)
    # 完整性校验：能打开且尺寸合理才算成功
    try:
        with Image.open(save_path) as im:
            im.verify()
        with Image.open(save_path) as im:
            w, h = im.size
    except Exception:
        try:
            os.remove(save_path)
        except Exception:
            pass
        return False
    if w < 180 or h < 180:
        try:
            os.remove(save_path)
        except Exception:
            pass
        return False
    return True


def _save_name(url, kw, seq):
    """由 URL 探测图片扩展名（兼容 .jpg.1 / 无扩展名），生成保存文件名。"""
    m = re.search(r'\.(jpg|jpeg|png|webp|gif|bmp)(?:[#?&]|$)', url, re.I)
    ext = ("." + m.group(1).lower()) if m else ".jpg"
    base = re.sub(r'[\\/:*?"<>|\s]+', "_", kw)[:12]
    return "灵感_%s_%02d%s" % (base, seq, ext)


def fetch_from_web(keywords, target_dir=None, limit=8, delay=0.6):
    """从 Bing 图片索引抓取关键词图片直链并限速下载。

    keywords: 关键词列表（逐个查询，汇总去重）
    limit: 本次最多下载张数
    返回 [(name, path, source_url, keyword), ...]（成功下载的）。
    注意：批量小范围、限速，只用于个人拼豆灵感参考。
    """
    target_dir = target_dir or inspiration_dir()
    os.makedirs(target_dir, exist_ok=True)
    pool = []          # (url, keyword)
    for kw in keywords:
        try:
            q = urllib.parse.quote(kw)
            url = ("https://cn.bing.com/images/search?q=%s&form=HDRSC2&first=0"
                   % q)
            html = _http_get(url)
            for u in _parse_bing_murl(html):
                pool.append((u, kw))
            time.sleep(0.4)
        except Exception:
            continue
    # 去重
    seen, uniq = set(), []
    for u, kw in pool:
        if u not in seen:
            seen.add(u)
            uniq.append((u, kw))
    downloaded = []
    n = 0
    for url, kw in uniq:
        if n >= limit:
            break
        save = os.path.join(target_dir, _save_name(url, kw, n + 1))
        if _download_image(url, save):
            filename = os.path.basename(save)
            record_source(target_dir, filename, url, kw)
            downloaded.append((os.path.splitext(filename)[0], save, url, kw))
            n += 1
            time.sleep(delay)
    return downloaded


if __name__ == "__main__":
    items = scan()
    print("灵感库条目：", len(items))
    for it in items:
        print(" -", it["name"], it["source_url"] or "本地")