/* 拼豆助手 · 在线版核心逻辑（纯浏览器计算，无服务端）
   移植自桌面版 bead_engine.py / palettes.py */
"use strict";

/* ---------------- 色卡数据（与 palettes.py 一致） ---------------- */
const COMMON_COLORS = [
  ["白色","#FFFFFF"],["浅粉","#F8C8DC"],["粉色","#F4A7B9"],["玫红","#E75480"],
  ["大红","#E60012"],["酒红","#722F37"],["橙红","#FF4500"],["橙色","#FF8C00"],
  ["杏黄","#FBCEB1"],["金黄","#FFC20E"],["浅黄","#FFF3B0"],["柠檬黄","#F6F33C"],
  ["米色","#F5F0DC"],["浅棕","#C9A97C"],["棕色","#8B5A2B"],["深棕","#5C3A21"],
  ["咖啡","#6F4E37"],["肤色","#FDBCB4"],["浅绿","#B6E388"],["苹果绿","#98FB98"],
  ["草绿","#7FD84A"],["深绿","#2E8B57"],["墨绿","#1F5934"],["青绿","#40E0D0"],
  ["薄荷绿","#98FF98"],["浅蓝","#ADD8E6"],["天蓝","#6CB4EE"],["宝蓝","#1E50A2"],
  ["藏青","#2E3A59"],["深蓝","#0A2463"],["浅紫","#D8BFD8"],["紫色","#7B5EA7"],
  ["紫罗兰","#8A2BE2"],["蓝紫","#6A5ACD"],["灰色","#808080"],["浅灰","#C0C0C0"],
  ["中灰","#A9A9A9"],["深灰","#555555"],["黑色","#1C1C1C"],["墨灰","#3D3D3D"],
];
const MORE_COLORS = [
  ["乳白","#FFFDF5"],["奶油","#FFFDD0"],["米黄","#F5DEB3"],["沙色","#D8C3A5"],
  ["驼色","#A0797B"],["巧克力","#7B3F00"],["栗色","#954535"],["焦糖","#C58F5D"],
  ["粉白","#FFF0F5"],["蔷薇粉","#F7B5C8"],["珊瑚粉","#F88379"],["桃粉","#FADADD"],
  ["绯红","#DC143C"],["铁锈红","#B7410E"],["藕荷","#F0D3C5"],
  ["橘黄","#FFA500"],["南瓜橙","#FF7518"],["琥珀","#FFBF00"],["奶茶色","#D2B48C"],
  ["芥末黄","#C5A52F"],["青柠","#BFFF00"],
  ["橄榄绿","#556B2F"],["松石绿","#40E0D0"],["湖蓝","#4FB3D9"],["雾蓝","#A2C8DB"],
  ["黛蓝","#1E3F66"],["电光蓝","#2D5FDB"],
  ["香芋紫","#C8A2C8"],["藕紫","#C7A6C5"],["霓虹紫","#9B5DE5"],
  ["水泥灰","#D3D3D3"],["烟灰","#6B6B6B"],["炭黑","#2B2B2B"],
  ["浅银","#E5E4E2"],["深银","#6E6E6E"],["原木","#C19A6B"],["乳酪","#FFF5C3"],
  ["樱花","#FFC9DE"],["薰衣草","#B57EDC"],
];
const PALETTES = {
  "常用40色（泛品牌）": COMMON_COLORS,
  "进阶78色（泛品牌）": COMMON_COLORS.concat(MORE_COLORS),
};

/* ---------------- 颜色工具 ---------------- */
function hex2rgb(hex) {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16),
          parseInt(h.slice(4, 6), 16)];
}
function rgb2hex(rgb) {
  return "#" + rgb.map(v => Math.max(0, Math.min(255, Math.round(v)))
    .toString(16).padStart(2, "0")).join("").toUpperCase();
}
function srgbToLinear(c) { c /= 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
/* RGB(0-255) -> CIELAB（L∈[0,100]，a/b≈[-128,127]），ΔE≈人眼感知差 */
function rgbToLab(r, g, b) {
  let X = srgbToLinear(r) * 0.4124564 + srgbToLinear(g) * 0.3575761 + srgbToLinear(b) * 0.1804375;
  let Y = srgbToLinear(r) * 0.2126729 + srgbToLinear(g) * 0.7151522 + srgbToLinear(b) * 0.0721750;
  let Z = srgbToLinear(r) * 0.0193339 + srgbToLinear(g) * 0.1191920 + srgbToLinear(b) * 0.9503041;
  X /= 0.95047; Z /= 1.08883;
  const f = t => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const fx = f(X), fy = f(Y), fz = f(Z);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}
function toLabArr(rgb) { return rgb.map(p => rgbToLab(p[0], p[1], p[2])); }

/* ---------------- K-Means（随机种子，迭代 10 次） ---------------- */
function kmeans(pts, k, iters = 10) {
  const n = pts.length, d = pts[0].length;
  let centers = [];
  const first = pts[Math.floor(Math.random() * n)];
  centers.push(first.slice());
  const dist = (a, b) => { let s = 0; for (let i = 0; i < d; i++) { let t = a[i] - b[i]; s += t * t; } return s; };
  // kmeans++
  while (centers.length < k) {
    let ds = pts.map(p => Math.min(...centers.map(c => dist(p, c))));
    let tot = ds.reduce((a, b) => a + b, 0) || 1;
    let r = Math.random() * tot, acc = 0, pick = 0;
    for (let i = 0; i < n; i++) { acc += ds[i]; if (acc >= r) { pick = i; break; } }
    centers.push(pts[pick].slice());
  }
  const assign = [];
  for (let it = 0; it < iters; it++) {
    assign.length = 0;
    for (let i = 0; i < n; i++) {
      let best = 0, bd = dist(pts[i], centers[0]);
      for (let j = 1; j < k; j++) {
        let dj = dist(pts[i], centers[j]);
        if (dj < bd) { bd = dj; best = j; }
      }
      assign.push(best);
    }
    const sums = Array.from({ length: k }, () => new Array(d).fill(0));
    const cnt = new Array(k).fill(0);
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < d; j++) sums[assign[i]][j] += pts[i][j];
      cnt[assign[i]]++;
    }
    for (let j = 0; j < k; j++)
      if (cnt[j]) for (let i = 0; i < d; i++) centers[j][i] = sums[j][i] / cnt[j];
    // 空簇：重置到最远的点
    cnt.forEach((c, j) => { if (!c) { let far = 0, fi = 0;
      for (let i = 0; i < n; i++) { let dd = dist(pts[i], centers[assign[i] % k]);
        if (dd > far) { far = dd; fi = i; } } centers[j] = pts[fi].slice(); } });
  }
  return { centers, assign };
}

/* 候选色：KMeans 中心与色卡色全局贪心一对一配对（仿桌面版 _pick_candidates） */
function pickCandidates(labPts, palLab, maxColors) {
  const k = Math.max(2, Math.min(maxColors, palLab.length, labPts.length));
  const { centers } = kmeans(labPts, k, 10);
  const pairs = [];
  for (let i = 0; i < k; i++)
    for (let j = 0; j < palLab.length; j++) {
      let d = 0; for (let t = 0; t < 3; t++) { let q = centers[i][t] - palLab[j][t]; d += q * q; }
      pairs.push([d, i, j]);
    }
  pairs.sort((a, b) => a[0] - b[0]);
  const usedC = {}, usedP = {}, cand = [];
  for (const [d, i, j] of pairs) {
    if (usedC[i] || usedP[j]) continue;
    usedC[i] = 1; usedP[j] = 1; cand.push(j);
    if (cand.length >= maxColors) break;
  }
  return cand.sort((a, b) => a - b);
}

/* ---------------- 抠图：纯色背景透明化 ---------------- */
function lighten(hex, ratio) {
  const [r, g, b] = hex2rgb(hex);
  return rgb2hex([r + (255 - r) * ratio, g + (255 - g) * ratio, b + (255 - b) * ratio]);
}
function removeUniformBackground(rgba, w, h) {
  // 四周边框采样背景（CIELAB 平均与标准差）
  const m = 8;
  const smp = [];
  for (let y = 0; y < m; y++) for (let x = 0; x < w; x++)
    { let i = (y * w + x) * 4; smp.push(rgbToLab(rgba[i], rgba[i + 1], rgba[i + 2])); }
  for (let y = h - m; y < h; y++) for (let x = 0; x < w; x++)
    { let i = (y * w + x) * 4; smp.push(rgbToLab(rgba[i], rgba[i + 1], rgba[i + 2])); }
  for (let y = m; y < h - m; y++) for (let x = 0; x < m; x++)
    { let i = (y * w + x) * 4; smp.push(rgbToLab(rgba[i], rgba[i + 1], rgba[i + 2])); }
  for (let y = m; y < h - m; y++) for (let x = w - m; x < w; x++)
    { let i = (y * w + x) * 4; smp.push(rgbToLab(rgba[i], rgba[i + 1], rgba[i + 2])); }
  const mu = [0, 0, 0];
  smp.forEach(p => { mu[0] += p[0]; mu[1] += p[1]; mu[2] += p[2]; });
  mu[0] /= smp.length; mu[1] /= smp.length; mu[2] /= smp.length;
  const std = [0, 0, 0];
  smp.forEach(p => { for (let i = 0; i < 3; i++) std[i] += (p[i] - mu[i]) ** 2; });
  const stdm = Math.sqrt((std[0] + std[1] + std[2]) / 3 / smp.length);
  const tol = 0.55;
  const ramp = Math.max(6, stdm * 1.6 + 4);
  const thresh = stdm * tol + tol * 2;
  const n = w * h;
  const out = new Uint8ClampedArray(rgba);
  const px = new Uint8ClampedArray(rgba);
  for (let i = 0; i < n; i++) {
    const p = rgbToLab(px[i * 4], px[i * 4 + 1], px[i * 4 + 2]);
    const dE = Math.sqrt((p[0] - mu[0]) ** 2 + (p[1] - mu[1]) ** 2 + (p[2] - mu[2]) ** 2);
    const a01 = Math.min(1, Math.max(0, (dE - thresh) / ramp));
    out[i * 4 + 3] = Math.round(a01 * 255);
  }
  return out;
}

/* ---------------- 网格化 ---------------- */
async function gridAverage(rgba, w, h, cols, rows, onProgress) {
  const cell = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => ({ s: [0, 0, 0], aw: 0, n: 0 })));
  // 分块统计，避免一次性占用事件循环太久
  const BAND = 200;
  for (let y0 = 0; y0 < h; y0 += BAND) {
    const y1 = Math.min(h, y0 + BAND);
    for (let y = y0; y < y1; y++) {
      const rr = Math.min(rows - 1, Math.floor(y * rows / h));
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        const cc = Math.min(cols - 1, Math.floor(x * cols / w));
        const a = rgba[i + 3] / 255;
        if (a < 0.05) continue;
        const c = cell[rr][cc];
        c.aw += a; c.n++;
        c.s[0] += rgba[i] * a; c.s[1] += rgba[i + 1] * a; c.s[2] += rgba[i + 2] * a;
      }
    }
    if (onProgress) onProgress(y1 / h);
    await new Promise(r => setTimeout(r, 0));   // 让进度条动起来
  }
  return cell;
}

/* ---------------- 生成主流程 ---------------- */
async function generate(opts, onProgress) {
  // opts: {data, w, h, cols, rows, palette, maxColors, fillBlank, crop:[x0,y0,x1,y1]|null, removeBg}
  const { w, h } = opts;
  let rgba = opts.data;
  if (opts.removeBg) {
    rgba = removeUniformBackground(rgba, w, h);
  }
  const grid = await gridAverage(rgba, w, h, opts.cols, opts.rows,
    p => onProgress(0, p));

  const pal = opts.palette.map(c => ({ name: c[0], hex: c[1] }));
  const palLab = toLabArr(pal.map(p => hex2rgb(p.hex)));

  // 样本 + 候选色（颜色数超限时降维）
  const sample = [];
  for (let r = 0; r < opts.rows; r++)
    for (let c = 0; c < opts.cols; c++) {
      const g = grid[r][c];
      if (g.n) sample.push([g.s[0] / g.aw, g.s[1] / g.aw, g.s[2] / g.aw]);
    }
  const fullColors = palLab.map((lab, i) => i);
  let candIdx = fullColors;
  if (pal.length > opts.maxColors && sample.length > 4) {
    const labPts = toLabArr(sample);
    candIdx = pickCandidates(labPts, palLab, opts.maxColors);
  }
  const candPal = candIdx.map(i => pal[i]);
  const candLab = candIdx.map(i => palLab[i]);

  // 每格平均色 -> 最近候选色（CIELAB）
  const cellsLab = toLabArr(sample);
  const mapped = Array.from({ length: opts.rows }, () => new Array(opts.cols).fill(null));
  const used = {};   // name -> count
  let si = 0;
  for (let r = 0; r < opts.rows; r++)
    for (let c = 0; c < opts.cols; c++) {
      const g = grid[r][c];
      if (!g.n) {
        if (opts.fillBlank && pal.some(p => p.name === "白色")) {
          mapped[r][c] = { name: "白色", hex: "#FFFFFF", raw: null };
          used["白色"] = (used["白色"] || 0) + 1;
        }
        continue;
      }
      let best = 0, bd = Infinity;
      for (let i = 0; i < candLab.length; i++) {
        let d = 0; for (let t = 0; t < 3; t++) { let q = cellsLab[si][t] - candLab[i][t]; d += q * q; }
        if (d < bd) { bd = d; best = i; }
      }
      const col = candPal[best];
      mapped[r][c] = { name: col.name, hex: col.hex, raw: null };
      used[col.name] = (used[col.name] || 0) + 1;
      si++;
    }
  onProgress(1, 0.9);
  const ordered = Object.entries(used).sort((a, b) => b[1] - a[1])
    .map(([name, cnt]) => ({ name, hex: pal.find(p => p.name === name).hex, cnt }));
  return { mapped, used: ordered, extra: null };
}

/* ---------------- 渲染与导出 ---------------- */
function drawPattern(mapped, cols, rows, cell, withGrid, numberMode, nameToNum) {
  const cv = document.createElement("canvas");
  cv.width = cols * cell; cv.height = rows * cell;
  const ctx = cv.getContext("2d");
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const v = mapped[r][c];
      ctx.fillStyle = v ? lighten(v.hex, 0) : "#EEEEEE";
      ctx.fillRect(c * cell, r * cell, cell, cell);
    }
  if (numberMode) {
    ctx.font = `bold ${Math.max(9, Math.floor(cell * 0.5))}px Arial`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (let r = 0; r < rows; r++)
      for (let c = 0; c < cols; c++) {
        const v = mapped[r][c];
        if (!v) continue;
        const num = nameToNum[v.name];
        ctx.fillStyle = "#E8EAEE";
        ctx.fillRect(c * cell, r * cell, cell, cell);
        ctx.fillStyle = lighten(v.hex, 0.85);
        ctx.fillRect(c * cell, r * cell, cell, cell);
        ctx.fillStyle = "#1E2228";
        ctx.fillText(String(num), c * cell + cell / 2, r * cell + cell / 2);
      }
  }
  if (withGrid) {
    ctx.strokeStyle = "#3C4450"; ctx.lineWidth = 1;
    for (let i = 0; i <= cols; i++) {
      ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, rows * cell); ctx.stroke();
    }
    for (let i = 0; i <= rows; i++) {
      ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(cols * cell, i * cell); ctx.stroke();
    }
  }
  return cv;
}

function drawSheet(mapped, cols, rows, used, mode, cell = 26) {
  const nameToNum = {};
  used.forEach((u, i) => nameToNum[u.name] = i + 1);
  const grid = drawPattern(mapped, cols, rows, cell * 1.2, true,
    mode === "number", nameToNum);
  // 图例
  const lh = 56 + Math.ceil(used.length / 2) * 40;
  const cv = document.createElement("canvas");
  cv.width = Math.max(grid.width, 560);
  cv.height = grid.height + lh;
  const ctx = cv.getContext("2d");
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.drawImage(grid, 0, 0);
  ctx.fillStyle = "#282E36";
  ctx.font = "14px 'Microsoft YaHei', sans-serif";
  const title = mode === "number" ? "编号图（数字=颜色编号，对照下方图例）"
                                 : "拼豆图纸（数字=每色所需颗数）";
  ctx.fillText(title, 8, grid.height + 20);
  const colsL = Math.ceil(used.length / 2);
  for (let i = 0; i < used.length; i++) {
    const u = used[i];
    const r = i % 2, c = Math.floor(i / 2);
    const x = 12 + c * ((cv.width - 24) / colsL);
    const y = grid.height + 34 + r * 40;
    ctx.fillStyle = u.hex; ctx.fillRect(x, y, 24, 24);
    ctx.strokeStyle = "#999"; ctx.strokeRect(x, y, 24, 24);
    ctx.fillStyle = "#333";
    ctx.font = "13px 'Microsoft YaHei', sans-serif";
    const label = mode === "number" ? `${nameToNum[u.name]}. ${u.name}  ×${u.cnt}`
                                    : `${u.name}  ×${u.cnt}  ${u.hex}`;
    ctx.fillText(label, x + 30, y + 17);
  }
  return cv;
}

function downloadCanvas(cv, filename) {
  cv.toBlob(blob => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }, "image/png");
}

function downloadList(used, cols, rows) {
  const total = used.reduce((s, u) => s + u.cnt, 0);
  const lines = [`拼豆耗材清单　图纸 ${cols}×${rows}`,
                 `用色 ${used.length} 种，共 ${total} 颗\n`];
  used.forEach((u, i) => lines.push(
    `${String(i + 1).padStart(2)}. ${u.name.padEnd(6)} ${u.hex}  需要 ${String(u.cnt).padStart(5)} 颗`));
  lines.push("\n提示：留空格已跳过，不占用耗材。");
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `拼豆耗材清单_${cols}x${rows}.txt`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}