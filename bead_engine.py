# -*- coding: utf-8 -*-
"""拼豆图纸生成引擎：抠图 -> 网格化 -> 色卡映射 -> 图纸渲染。
仅依赖 Pillow / numpy / cv2，可离线运行，可被 PyInstaller 打包。"""

import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import palettes


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------

def _cv2img(image: Image.Image) -> np.ndarray:
    """PIL -> BGR ndarray（带 alpha 时返回 BGRA）"""
    arr = np.asarray(image.convert("RGBA") if image.mode != "RGBA" else image)
    if arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _pil(arr: np.ndarray, mode: str = "RGB") -> Image.Image:
    if mode == "RGBA" and arr.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA), "RGBA")
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB), "RGB")


def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    return "#%02X%02X%02X" % (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def _load_font(size: int, bold=False):
    """按优先级尝试中文字体，找不到则退回默认字体（英文可读）。"""
    paths = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyhbd.ttf",
             r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.ttf",
             r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc",
             r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\msjhbd.ttc"]
    if not bold:
        paths = [p for p in paths if "bd" not in p.lower() and "bold" not in p.lower()]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _lighten_color(hx: str, ratio: float = 0.15) -> str:
    """将 hex 颜色提亮（与白色混合），ratio 控制原色保留比例。"""
    r, g, b = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
    r = int(r * ratio + 255 * (1 - ratio))
    g = int(g * ratio + 255 * (1 - ratio))
    b = int(b * ratio + 255 * (1 - ratio))
    return "#%02X%02X%02X" % (r, g, b)


# --------------------------------------------------------------------------
# 步骤一：读图 & 抠图
# --------------------------------------------------------------------------

def load_image(path: str) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    img.thumbnail((1600, 1600))  # 限制尺寸，加速处理
    return img


def remove_uniform_background(image: Image.Image, tol: float = 0.55,
                              clean_edges: bool = True) -> Image.Image:
    """自研自动抠图：把“接近四周边框平均色”的像素置为透明。

    适合纯色/近似纯色背景（桌面、墙壁、板面）的照片；复杂背景请改用“手动指定区域”。
    tol: 0~1 的色差容差，越大去得越激进。
    """
    bgr = _cv2img(image)
    if bgr.shape[2] == 3:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    # 转到“真实”CIELAB 尺度：L∈[0,100]，a,b∈[-128,127]，ΔE 才是人眼感知差。
    lab_u8 = cv2.cvtColor(bgr[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    lab = np.empty_like(lab_u8)
    lab[..., 0] = lab_u8[..., 0] * 100.0 / 255.0
    lab[..., 1:] = lab_u8[..., 1:] - 128.0

    h, w = lab.shape[:2]
    m = 8
    border = np.concatenate([lab[:m].reshape(-1, 3),
                             lab[-m:].reshape(-1, 3),
                             lab[:, :m].reshape(-1, 3),
                             lab[:, -m:].reshape(-1, 3)])
    mu = border.mean(axis=0)
    std = border.std(axis=0) + 1e-6

    # ΔE 距离；背景像素的 ΔE 一般 < 5，主体底色与背景通常 > 15。
    dist = np.sqrt(((lab - mu) ** 2).sum(axis=2))
    ramp = max(6.0, std.mean() * 1.6 + 4.0)          # ≥6 起步的过渡带
    alpha01 = np.clip((dist - std.mean() * tol - tol * 2.0) / ramp, 0.0, 1.0)
    alpha = (alpha01 * 255).astype(np.uint8)

    if clean_edges:
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN,
                                 np.ones((3, 3), np.uint8))

    out = bgr.copy()
    out[:, :, 3] = alpha
    return _pil(out, "RGBA")


def apply_crop(image: Image.Image, box) -> Image.Image:
    """box: (x0, y0, x1, y1)，裁剪并保持 RGBA。"""
    return image.crop(box)


# --------------------------------------------------------------------------
# 步骤二：网格化（按目标尺寸重采样为底色 + 每格平均色）
# --------------------------------------------------------------------------

def grid_by_average(im: Image.Image, cols: int, rows: int,
                    keep_alpha: bool = True):
    """把图片网格化为 cols x rows。

    返回：
      cells   : list[list], 元素为 dict：
                {'hex': 每格平均色（近似到 8 位四舍五入）,
                 'alpha': 不透明度 0~1,
                 'raw': 平均 RGB 小数}
      bg_hex  : 若无 alpha 或整图不透明时使用整图平均色作为空底。
    """
    im = im.convert("RGBA")
    if not keep_alpha or (np.asarray(im)[:, :, 3].sum() == im.width * im.height * 255):
        im = im.convert("RGB")
        arr = np.asarray(im, dtype=np.float32)
        alpha = np.ones((arr.shape[0], arr.shape[1]), dtype=np.float32)
    else:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32)
        alpha = np.asarray(im)[:, :, 3].astype(np.float32) / 255.0

    # 切成网格，每格取区域均值（掩蔽掉透明像素）
    h, w = arr.shape[:2]
    cells = []
    for r in range(rows):
        row = []
        y0, y1 = int(round(r * h / rows)), int(round((r + 1) * h / rows))
        for c in range(cols):
            x0, x1 = int(round(c * w / cols)), int(round((c + 1) * w / cols))
            region_a = alpha[y0:y1, x0:x1]
            m = region_a.mean()
            if m < 0.05:
                row.append({'hex': "#FFFFFF", 'alpha': 0.0, 'raw': np.zeros(3)})
                continue
            region = arr[y0:y1, x0:x1]
            wgt = region_a[..., None]
            mean_rgb = (region * wgt).sum(axis=(0, 1)) / wgt.sum()
            row.append({'hex': rgb_to_hex(np.clip(mean_rgb, 0, 255)),
                        'alpha': float(m), 'raw': mean_rgb})
        cells.append(row)

    opaque = np.concatenate([np.array([cl['raw'] for cl in r]) for r in cells])
    bg_hex = rgb_to_hex(np.clip(opaque.mean(axis=0), 0, 255))
    return cells, bg_hex


# --------------------------------------------------------------------------
# 步骤二点五：按图片比例推荐图纸尺寸
# --------------------------------------------------------------------------

def suggest_sizes(img_w: int, img_h: int, max_total: int = 32400):
    """按图片宽高比推荐几组等比例的图纸尺寸。

    基准档位以”较长边”长度划分，短边按原图比例推算；
    超出 max_total 颗数（默认 32400 ≈ 180x180 级）的档位会被丢弃。
    返回 [(cols, rows, total), ...]，按总量从小到大，保证每组等比例。
    """
    if img_h <= 0 or img_w <= 0:
        return []
    ratio = img_w / img_h            # >1 横图 / <1 竖图 / ==1 方图
    out, seen = [], set()
    # 从 29 到 150 共 7 档，大图用色更丰富、细节更还原
    for base in (29, 45, 60, 80, 100, 120, 150):
        if ratio >= 1:
            cols, rows = base, max(8, round(base / ratio))
        else:
            cols, rows = max(8, round(base * ratio)), base
        total = cols * rows
        if total <= max_total and (cols, rows) not in seen:
            seen.add((cols, rows))
            out.append((cols, rows, total))
    return out


# --------------------------------------------------------------------------
# 步骤三：颜色映射到色卡
# --------------------------------------------------------------------------

def _sample_opaque_pixels(image, max_pts=20000):
    """从图中抽取不透明像素的颜色做分层抽样（兼顾速度与色彩覆盖）。
    返回 (N,3) float32 RGB；image 为空或全透明时返回 None。"""
    if image is None:
        return None
    rgba = np.asarray(image.convert("RGBA"))
    mask = rgba[..., 3] >= 128
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    stride = int(np.ceil(len(ys) / max_pts)) or 1
    return rgba[ys[::stride], xs[::stride], :3].astype(np.float32)


def _pick_candidates(pts, palette_hexes, max_colors):
    """K 均值 + 贪心一对一匹配，选出“彼此不同且贴近样本色”的候选色。

    旧实现把每个聚类中心映射到最近的色卡色后直接去重——两个聚类可能撞上
    同一个色卡色（进阶色卡里近似色对很多），候选池被吞掉，实际用色远小于
    max_colors。这里改为：聚类中心与色卡色做最小距离的一对一配对，
    保证每个候选色不重复、尽量贴近样本，最多拿满 max_colors 个。
    返回候选 hex 列表（按色卡顺序）。
    """
    rgb = np.array([hex_to_rgb(h) for h in palette_hexes], dtype=np.float32)
    n_pal = len(rgb)
    k = max(2, min(max_colors, n_pal, len(pts)))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
    _, _, centers = cv2.kmeans(np.ascontiguousarray(pts), k, None, crit, 5,
                               cv2.KMEANS_PP_CENTERS)
    # 距离矩阵 (k, n_pal)，按距离从小到大贪心配对
    D = np.linalg.norm(centers[:, None, :] - rgb[None, :, :], axis=2)
    flat = np.argsort(D.ravel())[: n_pal * k]
    ci = np.unravel_index(flat, D.shape)[0]
    pi = np.unravel_index(flat, D.shape)[1]
    used_cl, used_pal, cand = set(), set(), []
    for a, b in zip(ci, pi):
        a, b = int(a), int(b)
        if a in used_cl or b in used_pal:
            continue
        used_cl.add(a)
        used_pal.add(b)
        cand.append(b)
        if len(cand) >= max_colors:
            break
    return [palette_hexes[i] for i in sorted(cand)]


def _to_lab(rgb: np.ndarray) -> np.ndarray:
    """RGB(0~255) -> 感知均匀 CIELAB（L∈[0,100], a/b∈[-128,127]，ΔE≈人眼差）。
    兼容 (h,w,3) 与 (k,3) 两种形状。"""
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    squeeze = rgb.ndim == 2
    if squeeze:
        rgb = rgb[None, ...]                       # (k,3) -> (1,k,3)
    lab = cv2.cvtColor(rgb[..., ::-1], cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] = lab[..., 0] * 100.0 / 255.0
    lab[..., 1:] -= 128.0
    return lab[0] if squeeze else lab


def _cell_majority(image, cols, rows, cand_hexes):
    """把图按候选色量化（CIELAB 感知色差），对每格做“多数投票”取代表色。

    相比“格子平均色 -> 最近色”，多数投票能保留格子内占优的真实色
    （60%红+40%蓝 会选红而不是平均出的暗紫），对平滑渐变（肌肤/天空）
    更贴原图、用色也更接近 max_colors。返回 cols×rows 列表：
    元素为候选 hex 字符串，全透明格为 None。
    """
    cand = np.array([hex_to_rgb(h) for h in cand_hexes], dtype=np.float32)
    cand_lab = _to_lab(cand)                      # (k,3)
    rgba = np.asarray(image.convert("RGBA"))
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    hw, ww = rgb.shape[:2]
    k = len(cand_hexes)

    # 行列边界与 grid_by_average 完全一致（round 取整）
    bounds_r = np.array([round(r * hw / rows) for r in range(rows + 1)], np.int64)
    bounds_c = np.array([round(c * ww / cols) for c in range(cols + 1)], np.int64)

    counts = np.zeros((rows * cols, k), dtype=np.int64)
    band = 256
    xidx = np.arange(ww)
    cc = np.searchsorted(bounds_c, xidx, side="right") - 1     # 每像素列->格
    for y0 in range(0, hw, band):
        y1 = min(hw, y0 + band)
        lab = _to_lab(rgb[y0:y1].astype(float))
        d = np.linalg.norm(lab[:, :, None, :] - cand_lab[None, None, :, :],
                           axis=3)                             # (band,w,k)
        labv = np.argmin(d, axis=2)
        labv[alpha[y0:y1] < 128] = -1                          # 透明像素剔除
        rr = np.searchsorted(bounds_r, np.arange(y0, y1), side="right") - 1
        cell_id = rr[:, None] * cols + cc[None, :]             # 每像素的格编号
        ok = labv >= 0
        np.add.at(counts, (cell_id[ok].ravel(), labv[ok].ravel()), 1)

    res = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            h = counts[r * cols + c]
            if h.sum() == 0:
                continue                                       # 全透明 -> 留空
            res[r][c] = cand_hexes[int(np.argmax(h))]
    return res


def map_to_palette(cells, colNames, max_colors, bg_overwrite=None, image=None):
    """把每格平均色映射到最接近的色卡色。

    - 不透明格强制映射到色卡色。
    - 透明格(alpha<0.5)：若提供 bg_overwrite 则填充为背景豆色，否则跳过（留空）。
    - 当色卡颜色数 > max_colors 时，先用 K 均值+贪心配对选出候选色再映射
      （控制耗材种类）。
    - 传入 image 时：候选色在像素级抽样上选取，格子颜色用“像素多数投票”
      （CIELAB 感知色差）确定，避免平均色抹平细节，用色更接近 max_colors。
    返回 (cells_result, used_colors) ；used_colors 为按使用量排序的
    [(color_name, hex, count), ...]。
    """
    names, hexes = colNames, [palettes.rgba_hex(n) for n in colNames]

    res = [[None] * len(r) for r in cells]
    used = {}

    # 必要时先降维候选色（只影响用色种类，不影响映射逻辑）
    full = [cl for row in cells for cl in row if cl['alpha'] >= 0.5]
    cand_hexes = list(hexes)
    if len(set(hexes)) > max_colors and len(full) > 4:
        pts = _sample_opaque_pixels(image) if image is not None else None
        if pts is None:   # 拿不到像素级样本时退回格子平均色
            pts = np.array([cl['raw'] for cl in full], dtype=np.float32)
        cand = _pick_candidates(pts, list(hexes), max_colors)
        if cand:
            cand_hexes = cand

    # 每格“平均色 -> 最近候选色”（CIELAB 感知色差）映射。
    # 实测验证：多数投票/纯RGB 都劣于此组合——本图格子平均色到 40/78 色卡的
    # 映射足迹（15/24）已接近像素级上限（18/30），再激进只会把渐变集中到少数色。
    cand_lab = _to_lab(np.array([hex_to_rgb(h) for h in cand_hexes], dtype=np.float32))
    rows_n, cols_n = len(cells), len(cells[0]) if cells else 0
    raw_flat = np.array([cl['raw'] for row in cells for cl in row], dtype=np.float32)
    raw_lab = _to_lab(raw_flat).reshape(rows_n, cols_n, 3)
    for r, row in enumerate(cells):
        res_row = [None] * len(row)
        for c, cl in enumerate(row):
            if cl['alpha'] < 0.5:
                if bg_overwrite is not None and bg_overwrite in names:
                    name, hx = bg_overwrite, palettes.rgba_hex(bg_overwrite)
                    res_row[c] = (name, hx)
                    used[name] = used.get(name, 0) + 1
                else:
                    res_row[c] = None  # 留空，不占颜色
                continue
            diff = np.linalg.norm(raw_lab[r, c] - cand_lab, axis=1)
            idx = int(np.argmin(diff))
            name = names[hexes.index(cand_hexes[idx])]
            hx = palettes.rgba_hex(name)
            res_row[c] = (name, hx)
            used[name] = used.get(name, 0) + 1
        res[r] = res_row

    ordered = sorted(used.items(), key=lambda kv: (-kv[1], names.index(kv[0])))
    ordered = [(name, palettes.rgba_hex(name), cnt) for name, cnt in ordered]
    return res, ordered


# --------------------------------------------------------------------------
# 步骤四：渲染图纸
# --------------------------------------------------------------------------

def render_pattern(cells, result, used_colors, grid_cols, grid_rows,
                   cell_px=22, page_margin=18, title="拼豆图纸",
                   dpi_scale=1.0, font_seed=5):
    """渲染整张图纸（含格子主图 + 编号图 + 色卡图例 + 编号图例），返回 PIL Image。"""
    P = max(2, int(cell_px * dpi_scale))
    P_num = max(36, P)                               # 编号图格子更大，方便读数字
    n = len(used_colors)

    # ---- 计算各块像素尺寸 ----
    img_w = grid_cols * P
    img_h = grid_rows * P
    num_img_w = grid_cols * P_num
    num_img_h = grid_rows * P_num

    legend_h = 0 if n == 0 else _legend_height(n, P, font_seed)
    num_legend_h = 0 if n == 0 else _legend_height(n, P_num, font_seed)
    title_h = max(34, int(30 * dpi_scale)) if title else 0

    small_preview_w = min(img_w, int(520 * dpi_scale))
    small_preview_h = max(1, int(img_h * small_preview_w / max(1, img_w)))

    # 编号图宽高上限：超过 800×800 时缩略
    num_preview_w = min(num_img_w, int(800 * dpi_scale))
    num_preview_h = max(1, int(num_img_h * num_preview_w / max(1, num_img_w)))

    row_gap = int(18 * dpi_scale)
    sheet_w = max(img_w, num_img_w) + 2 * page_margin
    sheet_h = (int(page_margin * dpi_scale * 1.5) + title_h + row_gap
               + small_preview_h + row_gap
               + img_h + row_gap + legend_h + row_gap   # 主图 + 色卡图例
               + num_preview_h + row_gap                # 编号图缩略
               + num_img_h + row_gap + num_legend_h     # 编号图全图 + 编号图例
               + int(page_margin * dpi_scale * 1.5) + 10)
    sheet_w = max(sheet_w, small_preview_w + 2 * page_margin)

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    d = ImageDraw.Draw(sheet)

    # ---- 标题 ----
    y = int(page_margin * dpi_scale * 0.8)
    if title_h:
        f = _load_font(int(22 * dpi_scale) + 4)
        d.text((page_margin, y), title, fill=(30, 30, 30), font=f)

    # ── 第 1 节：主图（含色卡图例）──────────────────────────
    # ------------------------------------------------------------
    # ---- 小预览（整张图缩略） ----
    y += title_h + row_gap if title_h else 0
    prev = render_grid_preview(cells, result, grid_cols, grid_rows, P,
                               small_preview_w, small_preview_h, show_grid=False)
    sheet.paste(prev, (page_margin, y))
    y += small_preview_h + row_gap

    # ---- 标注格主图（带方格线） ----
    d.rectangle([(page_margin, y), (page_margin + img_w - 1, y + img_h - 1)],
                outline=(0, 0, 0), width=1)
    block = render_grid_preview(cells, result, grid_cols, grid_rows, P, None, None)
    sheet.paste(block, (page_margin, y))
    y += img_h + row_gap

    # ---- 色卡图例 ----
    if n:
        y = _draw_legend(sheet, used_colors, img_w, y, P, font_seed, page_margin)
    y += row_gap

    # ── 第 2 节：编号图（含编号图例）──────────────────────────
    # ---- 编号缩略 ----
    num_prev = render_number_map(result, grid_cols, grid_rows, used_colors,
                                 P_num, num_preview_w)
    sheet.paste(num_prev, (page_margin, y))
    y += num_preview_h + row_gap

    # ---- 编号全图 ----
    d.rectangle([(page_margin, y), (page_margin + num_img_w - 1, y + num_img_h - 1)],
                outline=(0, 0, 0), width=1)
    num_full = render_number_map(result, grid_cols, grid_rows, used_colors,
                                 P_num, None)
    sheet.paste(num_full, (page_margin, y))
    y += num_img_h + row_gap

    # ---- 编号图例 ----
    if n:
        y = _draw_number_legend(sheet, used_colors, num_img_w, y, P_num,
                                font_seed, page_margin)

    y += page_margin
    return sheet


def _legend_height(n, P, font_seed):
    # 依据行数做双列排布
    per = 2
    rows_l = math.ceil(n / per)
    return rows_l * (P + 8) + 64


def _draw_legend(sheet, used, width, y0, P, font_seed, margin):
    d = ImageDraw.Draw(sheet)
    ft = _load_font(max(12, P // 2))
    fh = ft.size
    d.text((margin, y0), "色卡图例（数字为每色所需颗数）", fill=(40, 40, 40),
           font=_load_font(max(13, P // 2)))
    y0 += int(fh * 1.6)

    per = 2 if len(used) > 10 else 1
    col_w = max((width - margin - 10) // (per or 1), 240)
    rows_c = math.ceil(len(used) / (per or 1))
    y1 = y0 + rows_c * (P + int(fh * 1.4))
    for i, (name, hx, cnt) in enumerate(used):
        r, c = i % rows_c, i // rows_c
        x = margin + c * col_w
        y = y0 + r * (P + int(fh * 1.4))
        d.rectangle([x, y, x + P - 2, y + P - 2], fill=hx, outline=(80, 80, 80))
        d.text((x + P + 6, y + max(0, (P - fh) // 2)),
               "%s  ×%d  #%s" % (name, cnt, hx.lstrip('#')), fill=(20, 20, 20), font=ft)
    return y1 + 10


def render_grid_preview(cells, result, cols, rows, cell_px=26,
                        out_w=None, out_h=None, show_grid=False,
                        highlight=None):
    """渲染网格。result[r][c] 为 (name,hex) 或 None(留空)。大小缩放到 out_w。

    highlight: 传一个颜色名时，只保留该颜色的格子为原色，其余格子淡显（灰），
    用于「单色分布视图」——拼豆时只看某一种颜色的豆子放在哪里。
    编号图（render_number_map）自带粗体数字和方格线，用于拼豆时按号找色。
    """
    FADE = "#ECEDF0"            # 淡显底色
    EMPTY = "#ECECEC"
    P = cell_px
    img = Image.new("RGBA", (cols * P, rows * P), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    for r in range(rows):
        for c in range(cols):
            v = result[r][c]
            if v is None or (isinstance(v, str)):
                d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                            fill=EMPTY)
            else:
                name, hx = v
                if highlight and name != highlight:
                    d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                                fill=FADE)
                else:
                    d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                                fill=hx)
    if show_grid and P >= 6:
        # 画 1px 深灰网格线（每格边框对齐）
        for r in range(rows + 1):
            y = r * P
            d.line([(0, y), (cols * P - 1, y)], fill=(60, 60, 60), width=1)
        for c in range(cols + 1):
            x = c * P
            d.line([(x, 0), (x, rows * P - 1)], fill=(60, 60, 60), width=1)
    img = img.convert("RGB")
    if out_w and rows and cols:
        ratio = out_h / (rows * P) if out_h else out_w / (cols * P)
        if ratio < 1:
            img = img.resize((max(1, int(cols * P * ratio)),
                              max(1, int(rows * P * ratio))), Image.NEAREST)
    return img


def render_number_map(result, cols, rows, used_colors, cell_px=36, out_w=None,
                      highlight=None):
    """渲染编号图：每格填入编号（1~N），底纹为极浅的对应色，方便客人按号拼豆。

    result[r][c] = (name, hex) or None; used_colors 按 (name, hex, count) 排序。
    highlight: 传颜色名时只突出该颜色的格子（正常底色+深色编号），
    其余格子淡显（浅灰底 + 灰编号），用于「单色分布」在编号图上的对照。
    返回 PIL Image。
    """
    FADE = "#ECEDF0"             # 淡显底色
    FADE_NUM = (176, 183, 192)   # 淡显编号颜色
    P = cell_px
    # 构建颜色名→编号映射（按使用量从高到低 1 起编号）
    name_to_num = {}
    for idx, (name, _, _) in enumerate(used_colors, 1):
        name_to_num[name] = idx

    bg_img = Image.new("RGBA", (cols * P, rows * P), (255, 255, 255, 255))
    d = ImageDraw.Draw(bg_img)
    # 画单色背景 + 编号
    for r in range(rows):
        for c in range(cols):
            v = result[r][c]
            if v is None or isinstance(v, str):
                # 留空格
                d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                            fill=(245, 245, 245))
                continue
            name, hx = v
            if highlight and name != highlight:
                d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                            fill=FADE)
                numf = FADE_NUM
            else:
                pale = _lighten_color(hx, 0.15)  # 极浅底色
                d.rectangle([c * P, r * P, c * P + P - 1, r * P + P - 1],
                            fill=pale)
                numf = (30, 30, 30)
            num = name_to_num.get(name, 0)
            if num > 0:
                txt = str(num)
                ft = _load_font(max(10, P // 2 - 1), bold=True)
                bb = d.textbbox((0, 0), txt, font=ft)
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                cx = c * P + (P - tw) // 2
                cy = r * P + (P - th) // 2 - 1
                d.text((cx, cy), txt, fill=numf, font=ft)
    # 统一画网格线（1px 深灰，确保所有格线对齐无重叠）
    for r in range(rows + 1):
        d.line([(0, r * P), (cols * P - 1, r * P)], fill=(60, 60, 60), width=1)
    for c in range(cols + 1):
        d.line([(c * P, 0), (c * P, rows * P - 1)], fill=(60, 60, 60), width=1)

    bg_img = bg_img.convert("RGB")
    if out_w and cols:
        ratio = out_w / (cols * P)
        if ratio < 1:
            bg_img = bg_img.resize(
                (max(1, int(cols * P * ratio)),
                 max(1, int(rows * P * ratio))), Image.NEAREST)
    return bg_img


def _draw_number_legend(sheet, used_colors, width, y0, P, font_seed, margin):
    """绘制编号图例：编号 → 色块 → 色名 → 需用颗数。"""
    d = ImageDraw.Draw(sheet)
    ft = _load_font(max(12, P // 2))
    fh = ft.size
    title_ft = _load_font(max(13, P // 2))
    d.text((margin, y0), "编号图例（数字对应拼豆颜色）", fill=(40, 40, 40),
           font=title_ft)
    y0 += int(fh * 1.6)

    per = 2 if len(used_colors) > 10 else 1
    col_w = max((width - margin - 10) // (per or 1), 240)
    rows_c = math.ceil(len(used_colors) / (per or 1))
    for i, (name, hx, cnt) in enumerate(used_colors):
        num = i + 1
        r, c = i % rows_c, i // rows_c
        x = margin + c * col_w
        y = y0 + r * (P + int(fh * 1.4))
        # 编号
        num_ft = _load_font(max(9, P // 3), bold=True)
        d.text((x, y + 2), f"{num:>2}", fill=(30, 30, 30), font=num_ft)
        # 色块
        sx = x + int(P * 0.7)
        d.rectangle([sx, y, sx + P - 2, y + P - 2], fill=hx, outline=(80, 80, 80))
        # 名称 + 颗数
        d.text((sx + P + 6, y + max(0, (P - fh) // 2)),
               "%s  ×%d  #%s" % (name, cnt, hx.lstrip('#')),
               fill=(20, 20, 20), font=ft)
    return y0 + rows_c * (P + int(fh * 1.4)) + 10


def flip_pattern(result, cols, rows, axis="h"):
    """镜像翻转图纸：axis='h' 左右翻转，axis='v' 上下翻转。
    result[r][c] 为 (name, hex) 或 None(留空)。翻转不改颜色集合，仅换格子位置。"""
    if axis == "h":
        return [[result[r][cols - 1 - c] for c in range(cols)] for r in range(rows)]
    return [row[:] for row in reversed(result)]


def render_number_view(result, cols, rows, used_colors, cell_px=36, margin=16,
                       highlight=None):
    """生成编号图 + 底部图例合并的一张图，适合在画布上切换预览。

    编号图每一步格子 = 粗体数字 + 极浅底色 + 1px 深灰网格线。
    highlight: 单色分布——只突出该颜色格子的编号，其余淡显。
    图例：编号 → 色块 → 色名 → 颗数，两列排布。
    """
    grid = render_number_map(result, cols, rows, used_colors, cell_px=cell_px,
                             highlight=highlight)
    gw, gh = grid.size
    # 估算图例需要的高度
    per = 2 if len(used_colors) > 10 else 1
    rows_c = math.ceil(len(used_colors) / (per or 1))
    ft = _load_font(max(12, cell_px // 2))
    lh = int(ft.size * 1.6) + (cell_px + int(ft.size * 1.4)) * rows_c + 20
    sheet = Image.new("RGB", (gw, gh + lh), (255, 255, 255))
    sheet.paste(grid, (0, 0))
    _draw_number_legend(sheet, used_colors, gw, gh + 10, cell_px, cell_px, margin)
    return sheet


# --------------------------------------------------------------------------
# 步骤五：卡通化（纯 OpenCV 算法，零 AI 模型，离线运行）
# --------------------------------------------------------------------------

def cartoonize(image, subject_detect=True, edge_size=3, smooth_level=3):
    """把照片卡通化：边缘保留平滑 + 自适应粗黑边 + 颜色量化平涂。

    Parameters
    ----------
    image : PIL.Image (RGBA)
    subject_detect : bool
        是否检测主体（通过 alpha 通道判断非透明区域占比）
    edge_size : int (1-5)
        边缘线粗细，越大越粗
    smooth_level : int (1-5)
        平滑强度，越大颜色越平

    Returns
    -------
    (pil_result, subject_found, subject_ratio)
    pil_result : PIL.Image (RGB)
        卡通化后的图
    subject_found : bool
        True = 检测到主体
    subject_ratio : float
        主体占画面比例（0~1）
    """
    # 1. RGBA → BGRA ndarray
    bgra = _cv2img(image)
    if bgra.shape[2] != 4:
        bgra = cv2.cvtColor(bgra, cv2.COLOR_BGR2BGRA)
    h, w = bgra.shape[:2]
    alpha = bgra[:, :, 3] / 255.0

    # 2. 主体检测
    subject_found = True
    subject_ratio = (alpha >= 0.5).sum() / max(1, h * w)
    if subject_ratio < 0.08:
        subject_found = False

    # 3. 用 alpha 做透明背景的白底填充（rgba 合成到白底）
    bgr = bgra[:, :, :3]
    bg_white = np.full_like(bgr, 255)
    composite = (bgr * alpha[:, :, None] + bg_white * (1 - alpha[:, :, None])).astype(np.uint8)

    # 4. 边缘保留平滑（多级双边滤波）
    smooth = composite.copy()
    for _ in range(smooth_level):
        smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=18, sigmaSpace=8)

    # 5. 颜色量化（K-Means 降色到 12-16 色，平涂感）
    reshaped = smooth.reshape(-1, 3).astype(np.float32)
    k = max(4, min(16, max(8, (h * w) // 20000)))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
    _, labels, centers = cv2.kmeans(reshaped, k, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    quantized = centers[labels.flatten()].reshape(h, w, 3).astype(np.uint8)

    # 6. 边缘检测 + 加粗黑边
    gray = cv2.cvtColor(composite, cv2.COLOR_BGR2GRAY)
    gray_smooth = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(gray_smooth, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, blockSize=9, C=2)
    # 膨胀黑边到指定粗细
    ksize = max(1, edge_size)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    edges = cv2.dilate(255 - edges, kernel)
    edges = 255 - edges

    # 7. 合并：黑边叠在色块上
    edges_3c = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(quantized, edges_3c)

    # 8. 转回 PIL
    result = _pil(cartoon, "RGB")
    return result, subject_found, subject_ratio