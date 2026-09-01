# -*- coding: utf-8 -*-
"""中英文文案表。

设计原则：
- 文案集中在 ZH / EN 两张表里，key 就是中文原文，这样调用点写 tr("打开图片…")
  而不是 tr("OPEN_IMG")，新增文案不容易漏 key。
- 只翻译**界面文案、错误提示、导出的图纸文字**。
- 色卡的颜色名（"白色"、"玫红"…）和色卡名（"常用色卡（泛品牌）"…）是**算法数据**，
  不经过 tr()——gui.py 靠 "白色" 精确匹配来决定空白格填什么豆，
  palettes.py 里存的也是中文名。翻译它们会让导出图纸对不上号。
- tr() 永远不抛异常、永不返回空串：查不到 key 就原样返回中文。
  用户选了英文却漏了一条文案，看到的是中文，不会是空白。
"""
from __future__ import annotations

import json
import os
import sys


LANG_KEY = "lang"
DEFAULT_LANG = "zh"
VALID_LANGS = ("zh", "en")

# ---------------------------------------------------------------------------
# 文案表（key = 中文原文）
# ---------------------------------------------------------------------------

ZH = {
    # ---- 窗口与品牌 ----
    "拼豆助手": "拼豆助手",
    "拼豆助手 —— 照片变拼豆图纸": "拼豆助手 —— 照片变拼豆图纸",
    "照片 → 像素格子 → 照着拼的图纸": "照片 → 像素格子 → 照着拼的图纸",

    # ---- 顶栏 ----
    "打开图片…": "打开图片…",
    "保存图纸 PNG": "保存图纸 PNG",
    "保存耗材清单": "保存耗材清单",
    "导出 PDF": "导出 PDF",
    "拼豆灵感": "拼豆灵感",
    "编号图 ▶": "编号图 ▶",
    "◀ 颜色图": "◀ 颜色图",
    "适应画布": "适应画布",
    "⟷ 翻转": "⟷ 翻转",
    "↺ 重置": "↺ 重置",
    "⟳ 垂翻": "⟳ 垂翻",

    # ---- 画布标题 ----
    "原图": "原图",
    "拼豆图纸": "拼豆图纸",

    # ---- ① 抠图 ----
    "① 抠图": "① 抠图",
    "自动去背景（推荐 · 纯色背景）": "自动去背景（推荐 · 纯色背景）",
    "手动框选主体（点两点，右键取消）": "手动框选主体（点两点，右键取消）",
    "不抠图（整张都用）": "不抠图（整张都用）",

    # ---- ② 底板 ----
    "② 底板": "② 底板",
    "宽": "宽",
    "高": "高",
    "按图片推荐": "按图片推荐",
    "按原图比例自动调整高": "按原图比例自动调整高",
    "29×29 / 45×45=标准板；宽度决定高度（等比）":
        "29×29 / 45×45=标准板；宽度决定高度（等比）",

    # ---- ③ 色卡 ----
    "③ 色卡": "③ 色卡",
    "色卡": "色卡",
    "色卡编辑": "色卡编辑",
    "最多颜色数": "最多颜色数",
    "数字越小越省豆省事，越大越还原照片": "数字越小越省豆省事，越大越还原照片",

    # ---- ④ 空白格 ----
    "④ 空白格": "④ 空白格",
    "空白格用白色豆填满（铺满底板）": "空白格用白色豆填满（铺满底板）",

    # ---- ⑤ 卡通化 ----
    "⑤ 卡通化": "⑤ 卡通化",
    "开启卡通化（粗黑边 + 平涂色块，更适合拼豆）":
        "开启卡通化（粗黑边 + 平涂色块，更适合拼豆）",
    "边缘": "边缘",
    "平滑": "平滑",
    "检测主体": "检测主体",
    "边缘越粗线条越突出，平滑越强颜色越平": "边缘越粗线条越突出，平滑越强颜色越平",
    "AI 卡通（调用商汤 SenseNova，需联网）": "AI 卡通（调用商汤 SenseNova，需联网）",
    "保存": "保存",
    "🔑 获取 Key 教程 →（点击打开）": "🔑 获取 Key 教程 →（点击打开）",
    "风格": "风格",
    "AI 卡通化": "AI 卡通化",
    "生成卡通图后替换原图，再点「生成图纸」即可": "生成卡通图后替换原图，再点「生成图纸」即可",

    # ---- ⑥ 会员 ----
    "💎 会员": "💎 会员",
    "未开通会员": "未开通会员",
    "💳 开通 / 激活会员": "💳 开通 / 激活会员",
    "激活": "激活",
    "兑换码": "兑换码",

    # ---- 主按钮与进度 ----
    "生 成 图 纸": "生 成 图 纸",
    "生成中…": "生成中…",
    "网格化": "网格化",
    "颜色映射": "颜色映射",
    "渲染预览": "渲染预览",

    # ---- 单色分布 ----
    "单色分布": "单色分布",
    "（点开只看该色格子）": "（点开只看该色格子）",
    "生成后可在「编号图」与「颜色图」间切换预览":
        "生成后可在「编号图」与「颜色图」间切换预览",
    "全部": "全部",

    # ---- 空态 ----
    "还没有图片": "还没有图片",
    "点击左上角「打开图片…」选择一张照片\n推荐纯色背景 · 主体清晰":
        "点击左上角「打开图片…」选择一张照片\n推荐纯色背景 · 主体清晰",
    "点「生成图纸」后图纸会显示在这里\n滚轮缩放 · 按住滚轮拖动":
        "点「生成图纸」后图纸会显示在这里\n滚轮缩放 · 按住滚轮拖动",
    "打开一张照片，把它变成拼豆图纸": "打开一张照片，把它变成拼豆图纸",

    # ---- 推荐尺寸 ----
    "推荐图纸尺寸（按图片比例）": "推荐图纸尺寸（按图片比例）",
    "图片实际比例 %d × %d，按等比例推荐了下面几档尺寸：":
        "图片实际比例 %d × %d，按等比例推荐了下面几档尺寸：",
    "拼豆数量越少越省事，越多越还原照片细节。":
        "拼豆数量越少越省事，越多越还原照片细节。",
    "小图 · 省豆快拼": "小图 · 省豆快拼",
    "中图 · 均衡": "中图 · 均衡",
    "大图 · 细节丰富": "大图 · 细节丰富",
    "超大图 · 高度还原": "超大图 · 高度还原",
    "巨幅 · 精细还原": "巨幅 · 精细还原",
    "%d × %d　约 %d 颗　%s%s": "%d × %d　约 %d 颗　%s%s",
    "不动，保持当前尺寸（%d × %d）": "不动，保持当前尺寸（%d × %d）",
    "（当前": "（当前",
    "）": "）",
    "应 用": "应 用",
    "取消": "取消",
    "已应用推荐尺寸 %d×%d": "已应用推荐尺寸 %d×%d",

    # ---- 色卡管理 ----
    "色卡管理": "色卡管理",
    "自定义颜色（品牌色号）": "自定义颜色（品牌色号）",
    "颜色名": "颜色名",
    "十六进制（如 #E60012）": "十六进制（如 #E60012）",
    "新增颜色": "新增颜色",
    "删除选中": "删除选中",
    "我的色卡": "我的色卡",
    "色卡名称": "色卡名称",
    "颜色数": "颜色数",
    "新建": "新建",
    "编辑颜色": "编辑颜色",
    "重命名": "重命名",
    "删除": "删除",
    "导入 JSON": "导入 JSON",
    "导入支持两种格式：": "导入支持两种格式：",
    "· colors 列表 —— 引用已有颜色名；": "· colors 列表 —— 引用已有颜色名；",
    "· hexes 映射 —— 颜色名对应真实色号（如品牌豆精确色号）。":
        "· hexes 映射 —— 颜色名对应真实色号（如品牌豆精确色号）。",
    "所有修改点「保存」后写入 user_palettes.json。":
        "所有修改点「保存」后写入 user_palettes.json。",
    "保 存": "保 存",
    "关闭": "关闭",
    "编辑色卡颜色：%s": "编辑色卡颜色：%s",
    "勾选该色卡包含的颜色（搜索可快速过滤）：":
        "勾选该色卡包含的颜色（搜索可快速过滤）：",
    "新建色卡": "新建色卡",
    "色卡名称：": "色卡名称：",
    "确 定": "确 定",

    # ---- 状态栏与通用操作 ----
    "请先打开一张图片。": "请先打开一张图片。",
    "请先在上方填写 SenseNova API Key。\n在 platform.sensenova.cn 获取。":
        "请先在上方填写 SenseNova API Key。\n在 platform.sensenova.cn 获取。",
    "请先填写 API Key": "请先填写 API Key",
    "Key 已保存": "Key 已保存",
    "请输入 Key": "请输入 Key",
    "请输入兑换码。": "请输入兑换码。",
    "请先生成图纸，再使用翻转。": "请先生成图纸，再使用翻转。",
    "请先生成图纸。": "请先生成图纸。",
    "还没有可保存的图纸，先点「生成图纸」。": "还没有可保存的图纸，先点「生成图纸」。",
    "还没有可导出的图纸，先点「生成图纸」。": "还没有可导出的图纸，先点「生成图纸」。",
    "还没有生成结果。": "还没有生成结果。",
    "请先在下表选中一个我的色卡。": "请先在下表选中一个我的色卡。",
    "至少勾选 1 个颜色。": "至少勾选 1 个颜色。",
    "已存在同名色卡。": "已存在同名色卡。",
    "已存在同名色卡：%s": "已存在同名色卡：%s",
    "确定删除色卡「%s」？": "确定删除色卡「%s」？",
    "请填写颜色名与十六进制色值。": "请填写颜色名与十六进制色值。",
    "色值不是有效十六进制。": "色值不是有效十六进制。",
    "色值需要 6 位十六进制。": "色值需要 6 位十六进制。",
    "先在左侧选中一张灵感图。": "先在左侧选中一张灵感图。",
    "网格宽/高需在 2~400 之间": "网格宽/高需在 2~400 之间",
    "生成失败：": "生成失败：",
    "请调整参数后重试。": "请调整参数后重试。",
    "保存失败：": "保存失败：",
    "导出 Excel 失败：": "导出 Excel 失败：",
    "导出 PDF 失败：": "导出 PDF 失败：",
    "加载灵感图失败：": "加载灵感图失败：",
    "读取 JSON 失败：": "读取 JSON 失败：",
    "导入文件里没有可用的色卡内容。": "导入文件里没有可用的色卡内容。",
    "导入失败：": "导入失败：",
    "成功导入 %d 张色卡，并已持久化。": "成功导入 %d 张色卡，并已持久化。",
    "色卡已保存并持久化。": "色卡已保存并持久化。",
    "自动去背景失败（退回原图）：": "自动去背景失败（退回原图）：",
    "图片打开失败：": "图片打开失败：",
    "无法打开教程页：": "无法打开教程页：",
    "程序发生错误：": "程序发生错误：",
    "已写入《pixel-beads_错误日志.txt》。": "已写入《pixel-beads_错误日志.txt》。",
    "本机未安装 openpyxl：": "本机未安装 openpyxl：",
    "源码版请在命令行执行 pip install openpyxl 后重试。":
        "源码版请在命令行执行 pip install openpyxl 后重试。",
    "激活成功": "激活成功",
    "激活失败": "激活失败",
    "🎉 会员激活成功！\n有效期至 %s": "🎉 会员激活成功！\n有效期至 %s",
    "兑换码无效。": "兑换码无效。",
    "OK 主体已检测（%.0f%%）": "OK 主体已检测（%.0f%%）",
    "主体不明显（%.0f%%），建议手动框选": "主体不明显（%.0f%%），建议手动框选",
    "未检测到明显主体（主体只占画面 %.0f%%）。\n":
        "未检测到明显主体（主体只占画面 %.0f%%）。\n",
    "建议使用「手动框选」圈出主体，或换一张主体清晰的照片。":
        "建议使用「手动框选」圈出主体，或换一张主体清晰的照片。",
    "会员有效期至 %s": "会员有效期至 %s",
    "会员已过期": "会员已过期",
    "正在激活会员…": "正在激活会员…",
    "会员激活成功，有效期至 %s": "会员激活成功，有效期至 %s",
    "激活失败：%s": "激活失败：%s",
    "正在卡通化…": "正在卡通化…",
    "正在网格化图片…": "正在网格化图片…",
    "正在映射颜色到色卡…": "正在映射颜色到色卡…",
    "正在渲染预览…": "正在渲染预览…",
    "正在生成 PDF…": "正在生成 PDF…",
    "正在生成，请稍候（约数十秒）": "正在生成，请稍候（约数十秒）",
    "抠图完成；调整参数后点「生成图纸」。手动模式下：点击画布两次框选主体":
        "抠图完成；调整参数后点「生成图纸」。手动模式下：点击画布两次框选主体",
    "已清零拼制进度，重新开始标记": "已清零拼制进度，重新开始标记",
    "编号图模式：格内数字=颜色编号，底部图例对照": "编号图模式：格内数字=颜色编号，底部图例对照",
    "颜色图模式：直接看颜色拼豆": "颜色图模式：直接看颜色拼豆",
    "已%s翻转图纸，颜色分布已更新": "已%s翻转图纸，颜色分布已更新",
    "水平": "水平",
    "垂直": "垂直",
    "单色分布：只看「%s」的格子（其余淡显）": "单色分布：只看「%s」的格子（其余淡显）",
    "已恢复显示全部颜色": "已恢复显示全部颜色",
    "生成完成：{cols}x{rows}，{len(used)} 种颜色，共 {total} 颗豆":
        "生成完成：{cols}x{rows}，{len(used)} 种颜色，共 {total} 颗豆",
    "图纸尺寸：{cols} x {rows}   用色：{len(used)} 种   共需：{total} 颗豆":
        "图纸尺寸：{cols} x {rows}   用色：{len(used)} 种   共需：{total} 颗豆",
    "色卡：%s   模式：%s": "色卡：%s   模式：%s",
    "用豆最多：": "用豆最多：",
    "自动去背景": "自动去背景",
    "手动框选": "手动框选",
    "不抠图": "不抠图",
    "色卡：%s": "色卡：%s",
    "图纸已保存：": "图纸已保存：",
    "耗材清单已保存：": "耗材清单已保存：",
    "耗材清单 Excel 已导出：": "耗材清单 Excel 已导出：",
    "PDF 已导出：": "PDF 已导出：",
    "共 %d 页": "共 %d 页",
    "拼制进度：已拼 %d / %d 格（%.1f%%）——点击格子标记/取消，点「重置进度」清零":
        "拼制进度：已拼 %d / %d 格（%.1f%%）——点击格子标记/取消，点「重置进度」清零",

    # ---- 导出对话框 ----
    "预览图纸 · 确认保存": "预览图纸 · 确认保存",
    "下面是将要保存的完整图纸（可打印）：": "下面是将要保存的完整图纸（可打印）：",
    "保存图纸": "保存图纸",
    "保存拼豆图纸": "保存拼豆图纸",
    "PNG 图片": "PNG 图片",
    "所有文件": "所有文件",
    "预览耗材清单 · 确认保存": "预览耗材清单 · 确认保存",
    "下面是将要保存的耗材清单（txt）：": "下面是将要保存的耗材清单（txt）：",
    "保存清单": "保存清单",
    "另存为 Excel": "另存为 Excel",
    "保存耗材清单": "保存耗材清单",
    "文本文件": "文本文件",
    "导出耗材清单 Excel": "导出耗材清单 Excel",
    "Excel 工作簿": "Excel 工作簿",
    "导出 PDF（可打印）": "导出 PDF（可打印）",
    "PDF 文档": "PDF 文档",
    "拼豆图纸": "拼豆图纸",
    "拼豆耗材清单": "拼豆耗材清单",
    "用色 %d 种，共 %d 颗": "用色 %d 种，共 %d 颗",
    "需要 %d 颗": "需要 %d 颗",
    "提示：留空格已跳过，不占用耗材。": "提示：留空格已跳过，不占用耗材。",
    "图纸尺寸": "图纸尺寸",
    "用色": "用色",
    "共需": "共需",
    "编号": "编号",
    "色值 (HEX)": "色值 (HEX)",
    "所需颗数": "所需颗数",
    "选择照片": "选择照片",
    "图片文件": "图片文件",
    "导出耗材清单": "导出耗材清单",
    "拼豆耗材清单.txt": "拼豆耗材清单.txt",
    "拼豆耗材清单.xlsx": "拼豆耗材清单.xlsx",
    "拼豆耗材清单": "拼豆耗材清单",

    # ---- 拼豆板（WS2812 串口导出）----
    "导出拼豆板": "导出拼豆板",
    "导出到拼豆板（WS2812）": "导出到拼豆板（WS2812）",
    "把图纸发给 WS2812 拼豆板（STM32）": "把图纸发给 WS2812 拼豆板（STM32）",
    "图纸：%d × %d　共 %d 颗灯　点亮 %d 颗": "图纸：%d × %d　共 %d 颗灯　点亮 %d 颗",
    "数据 %d 字节 · 每颗 3 字节(GRB) · 含校验": "数据 %d 字节 · 每颗 3 字节(GRB) · 含校验",
    "串口": "串口",
    "波特率": "波特率",
    "（未检测到串口）": "（未检测到串口）",
    "提示：连接拼豆板后点「刷新」，选好串口再发送": "提示：连接拼豆板后点「刷新」，选好串口再发送",
    "发送到拼豆板": "发送到拼豆板",
    "图纸数据打包失败，请重试。": "图纸数据打包失败，请重试。",
    "请先选择一个串口。": "请先选择一个串口。",
    "正在发送到拼豆板…": "正在发送到拼豆板…",
    "已发送 %d 字节到 %s": "已发送 %d 字节到 %s",
    "已发送到拼豆板 %s": "已发送到拼豆板 %s",
    "发送失败：": "发送失败：",
    "发送失败": "发送失败",
    "测试灯板": "测试灯板",
    "测试灯板：发送中…": "测试灯板：发送中…",
    "测试帧已发送到 %s": "测试帧已发送到 %s",
    "测试帧已发送（1 颗白色）。板子应点亮 LED。\n\n"
    "若 LED 亮了 → 链路正常；\n"
    "若没亮 → 检查板子固件是否已烧录、串口是否正确。":
    "测试帧已发送（1 颗白色）。板子应点亮 LED。\n\n"
    "若 LED 亮了 → 链路正常；\n"
    "若没亮 → 检查板子固件是否已烧录、串口是否正确。",

    # ---- AI 卡通 ----
    "准备中…": "准备中…",
    "处理中": "处理中",
    "AI 卡通化中…": "AI 卡通化中…",
    "AI 卡通化中… %s": "AI 卡通化中… %s",
    "AI 卡通生成失败：%s": "AI 卡通生成失败：%s",
    "AI 卡通化失败": "AI 卡通化失败",
    "AI 卡通化完成，已替换原图；可点击「生成图纸」":
        "AI 卡通化完成，已替换原图；可点击「生成图纸」",
    "✔ OK 已替换原图": "✔ OK 已替换原图",
    "✕ 失败": "✕ 失败",
    "⏳ 准备中…": "⏳ 准备中…",
    "把它变成可爱卡通风格，Q版动漫，色彩明亮":
        "把它变成可爱卡通风格，Q版动漫，色彩明亮",

    # ---- AI 卡通 v2（风格方向 / 生成方式 / 拼豆友好化）----
    "风格方向": "风格方向",
    "🧸 奶油": "🧸 奶油",
    "✍️ 写实": "✍️ 写实",
    "👾 像素": "👾 像素",
    "🖤 漫画": "🖤 漫画",
    "🎨 简洁": "🎨 简洁",
    "🌅 水彩": "🌅 水彩",
    "生成方式": "生成方式",
    "图生图（改我的照片）": "图生图（改我的照片）",
    "文生图（凭空创作）": "文生图（凭空创作）",
    "自动优化为适合拼豆（减少渐变/压色数/加粗轮廓）":
        "自动优化为适合拼豆（减少渐变/压色数/加粗轮廓）",
    "生成后自动优化为适合拼豆的图纸底图，可预览对比":
        "生成后自动优化为适合拼豆的图纸底图，可预览对比",
    "AI 生成中（约数十秒）": "AI 生成中（约数十秒）",
    "拼豆友好化中…": "拼豆友好化中…",
    "AI 生成 · 拼豆友好对比": "AI 生成 · 拼豆友好对比",
    "对比：原始 vs 拼豆优化": "对比：原始 vs 拼豆优化",
    "AI 原图 %d 色 → 拼豆优化 %d 色（更省豆、更好拼）":
        "AI 原图 %d 色 → 拼豆优化 %d 色（更省豆、更好拼）",
    "AI 原始图": "AI 原始图",
    "拼豆优化版": "拼豆优化版",
    "✅ 用拼豆优化版": "✅ 用拼豆优化版",
    "用 AI 原始图": "用 AI 原始图",
    "图生图模式下需要提供原图。": "图生图模式下需要提供原图。",
    "文生图暂不支持，请用图生图。": "文生图暂不支持，请用图生图。",

    # ---- 会员弹窗 ----
    "💎 开通 / 激活会员": "💎 开通 / 激活会员",
    "（收款码图片待配置）": "（收款码图片待配置）",
    "（收款码加载失败）": "（收款码加载失败）",
    "支付宝扫码付款（9.9 元/月 · 29 元/年）":
        "支付宝扫码付款（9.9 元/月 · 29 元/年）",
    "付款后向客服获取兑换码，输入下方激活":
        "付款后向客服获取兑换码，输入下方激活",

    # ---- 灵感库 ----
    "拼豆灵感 · 挑一张好图开始拼": "拼豆灵感 · 挑一张好图开始拼",
    "精选·本地灵感": "精选·本地灵感",
    "在线找灵感": "在线找灵感",
    "预览": "预览",
    "点选左侧一张图": "点选左侧一张图",
    "用作底图": "用作底图",
    "从本地导入图片": "从本地导入图片",
    "提示：选中后点「用作底图」即可进入抠图 / 尺寸 / 色卡 / 生成流程":
        "提示：选中后点「用作底图」即可进入抠图 / 尺寸 / 色卡 / 生成流程",
    "灵感库还是空的\n点下面「在线找灵感」检索，或「从本地导入图片」":
        "灵感库还是空的\n点下面「在线找灵感」检索，或「从本地导入图片」",
    "无法预览": "无法预览",
    "名称：%s": "名称：%s",
    "来源：%s": "来源：%s",
    "关键词：%s": "关键词：%s",
    "本地/程序生成": "本地/程序生成",
    "灵感图已载入：「%s」—— 调整尺寸/色卡后点「生成图纸」":
        "灵感图已载入：「%s」—— 调整尺寸/色卡后点「生成图纸」",
    "导入拼豆灵感图（复制到灵感库）": "导入拼豆灵感图（复制到灵感库）",
    "已导入 %d 张灵感图到本地灵感库。": "已导入 %d 张灵感图到本地灵感库。",
    "在线检索公开图源（Bing 图片索引，含小红书/堆糖等平台的拼豆图）":
        "在线检索公开图源（Bing 图片索引，含小红书/堆糖等平台的拼豆图）",
    "关键词": "关键词",
    "数量": "数量",
    "检索并下载": "检索并下载",
    "采集中…": "采集中…",
    "采集失败：%s": "采集失败：%s",
    "没有下载到可用的图片，换个关键词试试。": "没有下载到可用的图片，换个关键词试试。",
    "已下载 %d 张灵感图（来源已记录），去「精选·本地灵感」页选用。":
        "已下载 %d 张灵感图（来源已记录），去「精选·本地灵感」页选用。",
    "在浏览器打开小红书搜索": "在浏览器打开小红书搜索",
    "在浏览器打开百度图片": "在浏览器打开百度图片",
    "浏览器里看到喜欢的图，可以右键保存，再回「精选·本地灵感」页点「从本地导入图片」加入灵感库。":
        "浏览器里看到喜欢的图，可以右键保存，再回「精选·本地灵感」页点「从本地导入图片」加入灵感库。",
    "本地导入": "本地导入",
    "自定义_%02d": "自定义_%02d",

    # ---- 图纸导出用的文字（图片里绘制，不进界面） ----
    "拼豆图纸  %s×%s · %s色 · 共%s颗": "拼豆图纸  %s×%s · %s色 · 共%s颗",
    "色卡图例（数字为每色所需颗数）": "色卡图例（数字为每色所需颗数）",
    "编号图例（数字对应拼豆颜色）": "编号图例（数字对应拼豆颜色）",

    # ---- f-string 里被拆出来的片段（保持前后空格/换行原样） ----
    "图纸尺寸：": "图纸尺寸：",
    "   用色": "   用色",
    "   用色：": "   用色：",
    " 种   共需：": " 种   共需：",
    " 颗": " 颗",
    " 颗\\n": " 颗\\n",
    "用色 ": "用色 ",
    " 种，共 ": " 种，共 ",
    " 颗豆": " 颗豆",
    " 种颜色，共 ": " 种颜色，共 ",
    "生成完成：": "生成完成：",
    "拼豆耗材清单　图纸 ": "拼豆耗材清单　图纸 ",
    "  需要 ": "  需要 ",
    " 需要 ": " 需要 ",
    " 颗": " 颗",
    "色 · 共": "色 · 共",
    "颗": "颗",
    " 页）": " 页）",
    "（共 ": "（共 ",
    "拼豆图纸  ": "拼豆图纸  ",
    "拼豆图纸_": "拼豆图纸_",
    "耗材清单": "耗材清单",
    "⚠ 会员已过期": "⚠ 会员已过期",
    "中文": "中文",
    "导入色卡 JSON": "导入色卡 JSON",
    "生成图纸失败：": "生成图纸失败：",
    "pixel-beads_错误日志.txt": "pixel-beads_错误日志.txt",
    "  在线找灵感  ": "  在线找灵感  ",
    "  精选·本地灵感  ": "  精选·本地灵感  ",
    "\\n\\n请调整参数后重试。": "\\n\\n请调整参数后重试。",
    "\\n\\n已写入《pixel-beads_错误日志.txt》。":
        "\\n\\n已写入《pixel-beads_错误日志.txt》。",
    "程序发生错误：\\n": "程序发生错误：\\n",

    # ---- bead_engine：图纸图例（图片里绘制）+ AI 卡通错误 ----
    "拼豆图纸": "拼豆图纸",
    "未配置 API key，请先在「卡通化」面板填写。":
        "未配置 API key，请先在「卡通化」面板填写。",
    "预处理后图片仍超过 %dMB，请换一张小图。":
        "预处理后图片仍超过 %dMB，请换一张小图。",
    "请求超时（生成较慢），请重试。": "请求超时（生成较慢），请重试。",
    "网络连接失败，请检查网络后重试。": "网络连接失败，请检查网络后重试。",
    "网络请求失败：%s": "网络请求失败：%s",
    "接口返回错误(%d)：%s": "接口返回错误(%d)：%s",
    "接口返回结果异常（无图片）。": "接口返回结果异常（无图片）。",
    "返回图片解析失败：%s": "返回图片解析失败：%s",

    # ---- member：会员价格与错误提示 ----
    "9.9 元/月 · 29 元/年": "9.9 元/月 · 29 元/年",
    "该兑换码在本机已使用过。": "该兑换码在本机已使用过。",
    "兑换码无效，请检查后重试。": "兑换码无效，请检查后重试。",
}


EN = {
    # ---- 窗口与品牌 ----
    "拼豆助手": "BeadCraft",
    "拼豆助手 —— 照片变拼豆图纸": "BeadCraft —— Photo to Bead Pattern",
    "照片 → 像素格子 → 照着拼的图纸": "Photo → pixel grid → printable pattern",

    # ---- 顶栏 ----
    "打开图片…": "Open Photo…",
    "保存图纸 PNG": "Save Pattern PNG",
    "保存耗材清单": "Save Bead List",
    "导出 PDF": "Export PDF",
    "拼豆灵感": "Inspiration",
    "编号图 ▶": "Numbered ▶",
    "◀ 颜色图": "◀ Color View",
    "适应画布": "Fit",
    "⟷ 翻转": "⟷ Flip",
    "↺ 重置": "↺ Reset",
    "⟳ 垂翻": "⟳ V-Flip",

    # ---- 画布标题 ----
    "原图": "Original",
    "拼豆图纸": "Bead Pattern",

    # ---- ① 抠图 ----
    "① 抠图": "① Cutout",
    "自动去背景（推荐 · 纯色背景）": "Auto remove background (solid BG)",
    "手动框选主体（点两点，右键取消）": "Manual crop (2 clicks; right-click to undo)",
    "不抠图（整张都用）": "No cutout (use whole image)",

    # ---- ② 底板 ----
    "② 底板": "② Canvas",
    "宽": "W",
    "高": "H",
    "按图片推荐": "Suggest",
    "按原图比例自动调整高": "Auto height from aspect ratio",
    "29×29 / 45×45=标准板；宽度决定高度（等比）":
        "29×29 / 45×45 = standard pegboards; width sets height (proportional)",

    # ---- ③ 色卡 ----
    "③ 色卡": "③ Palette",
    "色卡": "Palette",
    "色卡编辑": "Edit Palette",
    "最多颜色数": "Max colors",
    "数字越小越省豆省事，越大越还原照片":
        "Fewer colors = easier & cheaper; more = closer to the photo",

    # ---- ④ 空白格 ----
    "④ 空白格": "④ Empty Cells",
    "空白格用白色豆填满（铺满底板）": "Fill empty cells with white beads",

    # ---- ⑤ 卡通化 ----
    "⑤ 卡通化": "⑤ Cartoonize",
    "开启卡通化（粗黑边 + 平涂色块，更适合拼豆）":
        "Enable (bold outlines + flat colors, better for beads)",
    "边缘": "Edges",
    "平滑": "Smooth",
    "检测主体": "Detect subject",
    "边缘越粗线条越突出，平滑越强颜色越平":
        "Thicker edges = bolder lines; stronger smoothing = flatter colors",
    "AI 卡通（调用商汤 SenseNova，需联网）": "AI cartoon (SenseNova, online)",
    "保存": "Save",
    "🔑 获取 Key 教程 →（点击打开）": "🔑 Get API key → (click to open)",
    "风格": "Style",
    "AI 卡通化": "AI Cartoonize",
    "生成卡通图后替换原图，再点「生成图纸」即可":
        "The cartoon replaces the photo; then click Generate Pattern",

    # ---- ⑥ 会员 ----
    "💎 会员": "💎 Membership",
    "未开通会员": "Not a member",
    "💳 开通 / 激活会员": "💳 Subscribe / Activate",
    "激活": "Activate",
    "兑换码": "Redemption code",

    # ---- 主按钮与进度 ----
    "生 成 图 纸": "Generate Pattern",
    "生成中…": "Working…",
    "网格化": "Grid",
    "颜色映射": "Color map",
    "渲染预览": "Preview",

    # ---- 单色分布 ----
    "单色分布": "Single color",
    "（点开只看该色格子）": "(click to isolate one color)",
    "生成后可在「编号图」与「颜色图」间切换预览":
        "After generating, switch between Numbered and Color views",
    "全部": "All",

    # ---- 空态 ----
    "还没有图片": "No image yet",
    "点击左上角「打开图片…」选择一张照片\n推荐纯色背景 · 主体清晰":
        "Click \"Open Photo…\" in the top bar.\nSolid background & clear subject work best",
    "点「生成图纸」后图纸会显示在这里\n滚轮缩放 · 按住滚轮拖动":
        "The pattern appears here after generating.\nWheel to zoom · hold wheel to pan",
    "打开一张照片，把它变成拼豆图纸": "Open a photo to turn it into a bead pattern",

    # ---- 推荐尺寸 ----
    "推荐图纸尺寸（按图片比例）": "Suggested pattern sizes",
    "图片实际比例 %d × %d，按等比例推荐了下面几档尺寸：":
        "Image ratio %d × %d. Proportional suggestions:",
    "拼豆数量越少越省事，越多越还原照片细节。":
        "Fewer beads = faster; more beads = finer detail.",
    "小图 · 省豆快拼": "Small · quick",
    "中图 · 均衡": "Medium · balanced",
    "大图 · 细节丰富": "Large · detailed",
    "超大图 · 高度还原": "XL · high fidelity",
    "巨幅 · 精细还原": "XXL · fine detail",
    "%d × %d　约 %d 颗　%s%s": "%d × %d  ~%d beads  %s%s",
    "不动，保持当前尺寸（%d × %d）": "Keep current size (%d × %d)",
    "（当前": "(current",
    "）": ")",
    "应 用": "Apply",
    "取消": "Cancel",
    "已应用推荐尺寸 %d×%d": "Applied size %d×%d",

    # ---- 色卡管理 ----
    "色卡管理": "Palette Manager",
    "自定义颜色（品牌色号）": "Custom colors (brand codes)",
    "颜色名": "Color name",
    "十六进制（如 #E60012）": "Hex (e.g. #E60012)",
    "新增颜色": "Add color",
    "删除选中": "Delete selected",
    "我的色卡": "My palettes",
    "色卡名称": "Palette name",
    "颜色数": "Colors",
    "新建": "New",
    "编辑颜色": "Edit colors",
    "重命名": "Rename",
    "删除": "Delete",
    "导入 JSON": "Import JSON",
    "导入支持两种格式：": "Two import formats supported:",
    "· colors 列表 —— 引用已有颜色名；": "· colors list — reference existing color names;",
    "· hexes 映射 —— 颜色名对应真实色号（如品牌豆精确色号）。":
        "· hexes map — color name to real hex (e.g. brand codes).",
    "所有修改点「保存」后写入 user_palettes.json。":
        "Changes are written to user_palettes.json after you click Save.",
    "保 存": "Save",
    "关闭": "Close",
    "编辑色卡颜色：%s": "Edit palette colors: %s",
    "勾选该色卡包含的颜色（搜索可快速过滤）：":
        "Tick the colors in this palette (search to filter):",
    "新建色卡": "New palette",
    "色卡名称：": "Palette name:",
    "确 定": "OK",

    # ---- 状态栏与通用操作 ----
    "请先打开一张图片。": "Open a photo first.",
    "请先在上方填写 SenseNova API Key。\n在 platform.sensenova.cn 获取。":
        "Enter your SenseNova API key above.\nGet one at platform.sensenova.cn.",
    "请先填写 API Key": "Enter your API key first",
    "Key 已保存": "Key saved",
    "请输入 Key": "Please enter a key",
    "请输入兑换码。": "Please enter a redemption code.",
    "请先生成图纸，再使用翻转。": "Generate a pattern before flipping.",
    "请先生成图纸。": "Generate a pattern first.",
    "还没有可保存的图纸，先点「生成图纸」。":
        "No pattern to save yet — click Generate Pattern first.",
    "还没有可导出的图纸，先点「生成图纸」。":
        "No pattern to export yet — click Generate Pattern first.",
    "还没有生成结果。": "Nothing generated yet.",
    "请先在下表选中一个我的色卡。": "Select one of your palettes in the list below.",
    "至少勾选 1 个颜色。": "Tick at least one color.",
    "已存在同名色卡。": "A palette with that name already exists.",
    "已存在同名色卡：%s": "A palette named %s already exists.",
    "确定删除色卡「%s」？": "Delete the palette \"%s\"?",
    "请填写颜色名与十六进制色值。": "Enter a color name and a hex value.",
    "色值不是有效十六进制。": "Not a valid hex value.",
    "色值需要 6 位十六进制。": "Hex must be 6 digits.",
    "先在左侧选中一张灵感图。": "Select an inspiration image on the left.",
    "网格宽/高需在 2~400 之间": "Grid width/height must be 2–400",
    "生成失败：": "Generation failed: ",
    "请调整参数后重试。": "Adjust the parameters and try again.",
    "保存失败：": "Save failed: ",
    "导出 Excel 失败：": "Excel export failed: ",
    "导出 PDF 失败：": "PDF export failed: ",
    "加载灵感图失败：": "Failed to load inspiration image: ",
    "读取 JSON 失败：": "Failed to read JSON: ",
    "导入文件里没有可用的色卡内容。": "No usable palette content in that file.",
    "导入失败：": "Import failed: ",
    "成功导入 %d 张色卡，并已持久化。": "Imported %d palette(s) and saved.",
    "色卡已保存并持久化。": "Palette saved.",
    "自动去背景失败（退回原图）：": "Background removal failed (kept original): ",
    "图片打开失败：": "Could not open image: ",
    "无法打开教程页：": "Could not open the tutorial page: ",
    "程序发生错误：": "Error: ",
    "已写入《pixel-beads_错误日志.txt》。": "Written to pixel-beads_log.txt.",
    "本机未安装 openpyxl：": "openpyxl is not installed: ",
    "源码版请在命令行执行 pip install openpyxl 后重试。":
        "For source installs, run: pip install openpyxl",
    "激活成功": "Activated",
    "激活失败": "Activation failed",
    "🎉 会员激活成功！\n有效期至 %s":
        "🎉 Membership activated!\nValid until %s",
    "兑换码无效。": "Invalid redemption code.",
    "OK 主体已检测（%.0f%%）": "OK, subject detected (%.0f%%)",
    "主体不明显（%.0f%%），建议手动框选":
        "Weak subject (%.0f%%) — try manual crop",
    "未检测到明显主体（主体只占画面 %.0f%%）。\n":
        "No clear subject found (only %.0f%% of the frame).\n",
    "建议使用「手动框选」圈出主体，或换一张主体清晰的照片。":
        "Use manual crop to select the subject, or pick a clearer photo.",
    "会员有效期至 %s": "Member valid until %s",
    "会员已过期": "Membership expired",
    "正在激活会员…": "Activating membership…",
    "会员激活成功，有效期至 %s": "Activated, valid until %s",
    "激活失败：%s": "Activation failed: %s",
    "正在卡通化…": "Cartoonizing…",
    "正在网格化图片…": "Gridding the image…",
    "正在映射颜色到色卡…": "Mapping colors to the palette…",
    "正在渲染预览…": "Rendering preview…",
    "正在生成 PDF…": "Building PDF…",
    "正在生成，请稍候（约数十秒）": "Generating, please wait (~tens of seconds)",
    "抠图完成；调整参数后点「生成图纸」。手动模式下：点击画布两次框选主体":
        "Cutout done. Adjust settings, then Generate Pattern. "
        "Manual mode: click the canvas twice to box the subject.",
    "已清零拼制进度，重新开始标记": "Progress cleared, start marking again",
    "编号图模式：格内数字=颜色编号，底部图例对照":
        "Numbered view: digits = color numbers; match against the legend below",
    "颜色图模式：直接看颜色拼豆": "Color view: bead by color",
    "已%s翻转图纸，颜色分布已更新": "Pattern flipped (%s); colors updated",
    "水平": "horizontal",
    "垂直": "vertical",
    "单色分布：只看「%s」的格子（其余淡显）":
        "Single color: showing only \"%s\" cells (others dimmed)",
    "已恢复显示全部颜色": "Showing all colors again",
    "生成完成：{cols}x{rows}，{len(used)} 种颜色，共 {total} 颗豆":
        "Done: {cols}x{rows}, {len(used)} colors, {total} beads",
    "图纸尺寸：{cols} x {rows}   用色：{len(used)} 种   共需：{total} 颗豆":
        "Size: {cols} x {rows}   Colors: {len(used)}   Total: {total} beads",
    "色卡：%s   模式：%s": "Palette: %s   Mode: %s",
    "用豆最多：": "Most used: ",
    "自动去背景": "Auto cutout",
    "手动框选": "Manual crop",
    "不抠图": "No cutout",
    "色卡：%s": "Palette: %s",
    "图纸已保存：": "Pattern saved: ",
    "耗材清单已保存：": "Bead list saved: ",
    "耗材清单 Excel 已导出：": "Bead list (Excel) exported: ",
    "PDF 已导出：": "PDF exported: ",
    "共 %d 页": "%d page(s)",
    "拼制进度：已拼 %d / %d 格（%.1f%%）——点击格子标记/取消，点「重置进度」清零":
        "Progress: %d / %d cells (%.1f%%) — click cells to mark/unmark, "
        "Reset to clear",

    # ---- 导出对话框 ----
    "预览图纸 · 确认保存": "Preview pattern · confirm save",
    "下面是将要保存的完整图纸（可打印）：":
        "This is the full pattern that will be saved (printable):",
    "保存图纸": "Save pattern",
    "保存拼豆图纸": "Save bead pattern",
    "PNG 图片": "PNG image",
    "所有文件": "All files",
    "预览耗材清单 · 确认保存": "Preview bead list · confirm save",
    "下面是将要保存的耗材清单（txt）：":
        "This is the bead list that will be saved (txt):",
    "保存清单": "Save list",
    "另存为 Excel": "Save as Excel",
    "保存耗材清单": "Save bead list",
    "文本文件": "Text file",
    "导出耗材清单 Excel": "Export bead list to Excel",
    "Excel 工作簿": "Excel workbook",
    "导出 PDF（可打印）": "Export PDF (printable)",
    "PDF 文档": "PDF document",
    "拼豆图纸": "Bead pattern",
    "拼豆耗材清单": "Bead supply list",
    "用色 %d 种，共 %d 颗": "%d colors, %d beads",
    "需要 %d 颗": "%d beads",
    "提示：留空格已跳过，不占用耗材。":
        "Note: empty cells are skipped and use no beads.",
    "图纸尺寸": "Pattern size",
    "用色": "Colors",
    "共需": "Total",
    "编号": "No.",
    "色值 (HEX)": "Hex",
    "所需颗数": "Beads needed",
    "选择照片": "Choose a photo",
    "图片文件": "Image files",
    "导出耗材清单": "Export bead list",
    "拼豆耗材清单.txt": "bead-list.txt",
    "拼豆耗材清单.xlsx": "bead-list.xlsx",
    "拼豆耗材清单": "Bead supply list",

    # ---- 拼豆板（WS2812 串口导出）----
    "导出拼豆板": "Send to Board",
    "导出到拼豆板（WS2812）": "Send to Bead Board (WS2812)",
    "把图纸发给 WS2812 拼豆板（STM32）": "Send the pattern to the WS2812 bead board (STM32)",
    "图纸：%d × %d　共 %d 颗灯　点亮 %d 颗":
        "Pattern: %d × %d, %d LEDs, %d lit",
    "数据 %d 字节 · 每颗 3 字节(GRB) · 含校验":
        "%d bytes · 3 bytes/LED (GRB) · with checksum",
    "串口": "Port",
    "波特率": "Baud",
    "（未检测到串口）": "(no port detected)",
    "提示：连接拼豆板后点「刷新」，选好串口再发送":
        "Tip: connect the board, tap refresh, then pick a port",
    "发送到拼豆板": "Send to Board",
    "图纸数据打包失败，请重试。": "Failed to build the frame — please retry.",
    "请先选择一个串口。": "Please select a serial port first.",
    "正在发送到拼豆板…": "Sending to board…",
    "已发送 %d 字节到 %s": "Sent %d bytes to %s",
    "已发送到拼豆板 %s": "Sent to board %s",
    "发送失败：": "Send failed: ",
    "发送失败": "Send failed",
    "测试灯板": "Test LED",
    "测试灯板：发送中…": "Testing LED: sending…",
    "测试帧已发送到 %s": "Test frame sent to %s",
    "测试帧已发送（1 颗白色）。板子应点亮 LED。\n\n"
    "若 LED 亮了 → 链路正常；\n"
    "若没亮 → 检查板子固件是否已烧录、串口是否正确。":
        "Test frame sent (1 white bead). The board should light its LED.\n\n"
        "LED on → link is OK;\n"
        "LED off → check firmware is flashed and the port is correct.",

    # ---- AI 卡通 ----
    "准备中…": "Preparing…",
    "处理中": "Processing",
    "AI 卡通化中…": "AI cartoonizing…",
    "AI 卡通化中… %s": "AI cartoonizing… %s",
    "AI 卡通生成失败：%s": "AI cartoon failed: %s",
    "AI 卡通化失败": "AI cartoonization failed",
    "AI 卡通化完成，已替换原图；可点击「生成图纸」":
        "Cartoon ready, photo replaced — click Generate Pattern",
    "✔ OK 已替换原图": "✔ OK, photo replaced",
    "✕ 失败": "✕ Failed",
    "⏳ 准备中…": "⏳ Preparing…",
    "把它变成可爱卡通风格，Q版动漫，色彩明亮":
        "把它变成可爱卡通风格，Q版动漫，色彩明亮",

    # ---- AI 卡通 v2（风格方向 / 生成方式 / 拼豆友好化）----
    "风格方向": "Style",
    "🧸 奶油": "🧸 Cream",
    "✍️ 写实": "✍️ Realistic",
    "👾 像素": "👾 Pixel",
    "🖤 漫画": "🖤 Comic",
    "🎨 简洁": "🎨 Flat",
    "🌅 水彩": "🌅 Watercolor",
    "生成方式": "Source",
    "图生图（改我的照片）": "Image-to-image (edit my photo)",
    "文生图（凭空创作）": "Text-to-image (create from scratch)",
    "自动优化为适合拼豆（减少渐变/压色数/加粗轮廓）":
        "Auto-optimize for beads (smooth gradients / fewer colors / bold outlines)",
    "生成后自动优化为适合拼豆的图纸底图，可预览对比":
        "Result is auto-optimized for beading, with a before/after preview",
    "AI 生成中（约数十秒）": "AI generating (a few tens of seconds)",
    "拼豆友好化中…": "Optimizing for beads…",
    "AI 生成 · 拼豆友好对比": "AI result · bead-friendly compare",
    "对比：原始 vs 拼豆优化": "Compare: original vs bead-optimized",
    "AI 原图 %d 色 → 拼豆优化 %d 色（更省豆、更好拼）":
        "AI original %d colors → bead-optimized %d colors (fewer beads, easier)",
    "AI 原始图": "AI original",
    "拼豆优化版": "Bead-optimized",
    "✅ 用拼豆优化版": "✅ Use bead-optimized",
    "用 AI 原始图": "Use AI original",
    "图生图模式下需要提供原图。": "Image-to-image requires a source photo.",
    "文生图暂不支持，请用图生图。": "Text-to-image isn't supported yet — use image-to-image.",

    # ---- 会员弹窗 ----
    "💎 开通 / 激活会员": "💎 Subscribe / Activate",
    "（收款码图片待配置）": "(payment QR code not configured)",
    "（收款码加载失败）": "(failed to load payment QR code)",
    "支付宝扫码付款（9.9 元/月 · 29 元/年）":
        "Pay with Alipay (¥9.9/mo · ¥29/yr)",
    "付款后向客服获取兑换码，输入下方激活":
        "After paying, get a redemption code and enter it below",

    # ---- 灵感库 ----
    "拼豆灵感 · 挑一张好图开始拼": "Inspiration · pick a photo to start",
    "精选·本地灵感": "Local inspiration",
    "在线找灵感": "Find online",
    "预览": "Preview",
    "点选左侧一张图": "Pick one from the left",
    "用作底图": "Use as base",
    "从本地导入图片": "Import from local",
    "提示：选中后点「用作底图」即可进入抠图 / 尺寸 / 色卡 / 生成流程":
        "Tip: after selecting, click \"Use as base\" to continue with "
        "cutout / size / palette / generate",
    "灵感库还是空的\n点下面「在线找灵感」检索，或「从本地导入图片」":
        "Your library is empty.\nUse \"Find online\" below, or import locally.",
    "无法预览": "Cannot preview",
    "名称：%s": "Name: %s",
    "来源：%s": "Source: %s",
    "关键词：%s": "Keyword: %s",
    "本地/程序生成": "local / generated",
    "灵感图已载入：「%s」—— 调整尺寸/色卡后点「生成图纸」":
        "Loaded \"%s\" — adjust size/palette, then Generate Pattern",
    "导入拼豆灵感图（复制到灵感库）": "Import inspiration images",
    "已导入 %d 张灵感图到本地灵感库。": "Imported %d image(s) to the local library.",
    "在线检索公开图源（Bing 图片索引，含小红书/堆糖等平台的拼豆图）":
        "Search public image sources (Bing index, incl. XHS / Duitang patterns)",
    "关键词": "Keyword",
    "数量": "Count",
    "检索并下载": "Search & download",
    "采集中…": "Collecting…",
    "采集失败：%s": "Collection failed: %s",
    "没有下载到可用的图片，换个关键词试试。":
        "No usable images downloaded — try another keyword.",
    "已下载 %d 张灵感图（来源已记录），去「精选·本地灵感」页选用。":
        "Downloaded %d image(s) (sources recorded) — pick from Local inspiration.",
    "在浏览器打开小红书搜索": "Open XHS search in browser",
    "在浏览器打开百度图片": "Open Baidu Images in browser",
    "浏览器里看到喜欢的图，可以右键保存，再回「精选·本地灵感」页点「从本地导入图片」加入灵感库。":
        "Right-click to save anything you like in the browser, then come "
        "back to Local inspiration and use Import from local.",
    "本地导入": "local import",
    "自定义_%02d": "custom_%02d",

    # ---- 图纸导出用的文字（图片里绘制，不进界面） ----
    "拼豆图纸  %s×%s · %s色 · 共%s颗":
        "Bead Pattern  %s×%s · %s colors · %s beads",
    "色卡图例（数字为每色所需颗数）": "Palette legend (numbers = beads per color)",
    "编号图例（数字对应拼豆颜色）": "Number legend (numbers = bead colors)",

    # ---- f-string 里被拆出来的片段（保持前后空格/换行原样） ----
    "图纸尺寸：": "Size: ",
    "   用色": "   Colors",
    "   用色：": "   Colors: ",
    " 种   共需：": "   Total: ",
    " 颗": " beads",
    " 颗\\n": " beads\\n",
    "用色 ": "Colors ",
    " 种，共 ": " colors, ",
    " 颗豆": " beads",
    " 种颜色，共 ": " colors, ",
    "生成完成：": "Done: ",
    "拼豆耗材清单　图纸 ": "Bead List  ",
    "  需要 ": "  need ",
    " 需要 ": "  need ",
    "颗": " beads",
    "色 · 共": " colors · ",
    " 页）": " pages)",
    "（共 ": " (",
    "拼豆图纸  ": "Bead Pattern  ",
    "拼豆图纸_": "bead-pattern_",
    "耗材清单": "bead list",
    "⚠ 会员已过期": "⚠ Membership expired",
    "中文": "中文",
    "导入色卡 JSON": "Import palette JSON",
    "生成图纸失败：": "Pattern generation failed: ",
    "pixel-beads_错误日志.txt": "pixel-beads_log.txt",
    "  在线找灵感  ": "  Find online  ",
    "  精选·本地灵感  ": "  Local  ",
    "\\n\\n请调整参数后重试。": "\\n\\nAdjust the parameters and try again.",
    "\\n\\n已写入《pixel-beads_错误日志.txt》。":
        "\\n\\nWritten to pixel-beads_log.txt.",
    "程序发生错误：\\n": "Error:\\n",

    # ---- bead_engine：图纸图例（图片里绘制）+ AI 卡通错误 ----
    "拼豆图纸": "Bead Pattern",
    "未配置 API key，请先在「卡通化」面板填写。":
        "API key not set — fill it in the Cartoonize panel.",
    "预处理后图片仍超过 %dMB，请换一张小图。":
        "Image is still over %dMB after preprocessing — use a smaller one.",
    "请求超时（生成较慢），请重试。": "Request timed out (generation is slow) — please retry.",
    "网络连接失败，请检查网络后重试。": "Network connection failed — check your connection and retry.",
    "网络请求失败：%s": "Network request failed: %s",
    "接口返回错误(%d)：%s": "API returned error (%d): %s",
    "接口返回结果异常（无图片）。": "API returned no image.",
    "返回图片解析失败：%s": "Failed to parse the returned image: %s",

    # ---- member：会员价格与错误提示 ----
    "9.9 元/月 · 29 元/年": "¥9.9/mo · ¥29/yr",
    "该兑换码在本机已使用过。": "This redemption code has already been used on this machine.",
    "兑换码无效，请检查后重试。": "Invalid redemption code — please check and retry.",
}


TABLES = {"zh": ZH, "en": EN}


# ---------------------------------------------------------------------------
# 当前语言（由 gui.py 写入 user_settings.json 的 "lang" 字段）
# ---------------------------------------------------------------------------

_lang: str = DEFAULT_LANG
_callbacks: list = []


def set_lang(lang: str) -> None:
    """切换语言并通知已注册的重绘回调（gui.py 的整界面重建）。"""
    global _lang
    _lang = lang if lang in VALID_LANGS else DEFAULT_LANG
    for cb in list(_callbacks):
        try:
            cb()
        except Exception:
            pass


def get_lang() -> str:
    return _lang


def on_lang_changed(cb) -> None:
    """注册语言切换回调。"""
    if cb not in _callbacks:
        _callbacks.append(cb)


def load_lang_from_settings(data: dict) -> None:
    """从 user_settings.json 里读语言，不通知回调（启动时用）。"""
    global _lang
    lang = (data or {}).get(LANG_KEY)
    if lang in VALID_LANGS:
        _lang = lang


def save_lang_to_settings(data: dict, lang: str) -> dict:
    """把语言写进 settings dict，返回同一个 dict 便于链式调用。"""
    data[LANG_KEY] = lang
    return data


# ---------------------------------------------------------------------------
# 翻译入口
# ---------------------------------------------------------------------------

def tr(text: str) -> str:
    """按当前语言翻译。查不到 key 原样返回（永不返回空串、永不抛异常）。

    用中文原文当 key，所以中英文表可以不对称——漏了英文条目就显示中文。
    """
    if not isinstance(text, str) or not text:
        return text or ""
    if _lang == DEFAULT_LANG:
        return text
    return TABLES.get(_lang, {}).get(text, text)


def tr_fmt(text: str, *args) -> str:
    """先翻译再 % 格式化。用于 "%s 和参数混排" 的文案。"""
    return tr(text) % args


# ---------------------------------------------------------------------------
# 导出文件用的语言（图纸图例、耗材清单是图片/文本，不走界面重绘）
# ---------------------------------------------------------------------------

def export_lang() -> str:
    """供 bead_engine / 清单导出使用的语言码，只有 zh / en。"""
    return _lang
