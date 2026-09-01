# -*- coding: utf-8 -*-
"""拼豆图纸 → WS2812 拼豆板 的串口导出。

把 exe 里的图纸网格打包成 STM32 能解析的二进制协议帧，经串口发给
STM32F411，再由 STM32 转成 WS2812 的位流点亮 29×29 的 RGB 灯矩阵。

协议帧（固定顺序，含边界与校验）：
    帧头  0xAA 0x55        （2 字节，告诉 STM32“开始”）
    行数  1 字节
    列数  1 字节
    数据  rows×cols×3 字节  （每颗灯固定 3 字节，顺序 G、R、B —— WS2812 是 GRB）
    校验  1 字节            （数据部分简单累加和，供 STM32 检查是否传错）
    帧尾  0x0D 0x0A        （2 字节，告诉 STM32“结束”）

- 空位（None，留空的格子）→ 灯熄灭 (0, 0, 0)。
- 有色的格子 → 用其 HEX 颜色转成 (G, R, B)。
- 为什么要有协议：串口是“无边界字节流”，STM32 需要帧头/帧尾划边界、
  行列数知道尺寸、校验和判断有没有传错。没有这套，数据就是一团乱码。
"""
from __future__ import annotations

import sys

# pyserial 是可选的：没装也能打包/预览，只是真正发送时提示安装
try:
    import serial
    import serial.tools.list_ports
    _HAS_SERIAL = True
except Exception:
    _HAS_SERIAL = False


FRAME_HEAD = bytes((0xAA, 0x55))
FRAME_TAIL = bytes((0x0D, 0x0A))
DEFAULT_BAUD = 115200


def hex_to_grb(hex_str: str) -> tuple:
    """'#RRGGBB' -> (G, R, B)。WS2812 的颜色字节顺序是 GRB。"""
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return (0, 0, 0)
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (g, r, b)


def build_frame(cells, rows: int, cols: int) -> bytes:
    """把图纸网格打包成串口协议帧。

    - cells: 二维列表（rows 行 × cols 列），每格为 (名称, hex) 或 None。
    - 返回 bytes：完整的二进制帧。
    """
    data = bytearray()
    for r in range(rows):
        for c in range(cols):
            cell = cells[r][c] if r < len(cells) and c < len(cells[r]) else None
            if cell is not None and cell[1]:
                g, r_, b = hex_to_grb(cell[1])
            else:
                g, r_, b = (0, 0, 0)
            data.append(g)
            data.append(r_)
            data.append(b)

    checksum = sum(data) & 0xFF
    frame = (FRAME_HEAD
             + bytes((rows & 0xFF, cols & 0xFF))
             + bytes(data)
             + bytes((checksum,))
             + FRAME_TAIL)
    return bytes(frame)


def build_test_frame() -> bytes:
    """构造一个简单的「测试灯板」帧：1×1，一颗灯，亮白色 (255,255,255)。

    用于在 PC 端点击「测试灯板」时，验证整条链路（exe 打包 → 串口发送 →
    板子接收解析 → 点亮 LED）是否通畅，而不必查看串口监视器。
    """
    cells = [[("测试", "#FFFFFF")]]
    return build_frame(cells, 1, 1)


def frame_stats(frame: bytes) -> dict:
    """解析一帧并返回统计信息（用于预览 / 测试）。"""
    if len(frame) < 4:
        return {"ok": False, "msg": "帧太短"}
    head = frame[:2]
    rows, cols = frame[2], frame[3]
    n = rows * cols
    body = frame[4:4 + n * 3]
    if len(body) != n * 3:
        return {"ok": False, "msg": "数据长度不匹配"}
    checksum = frame[4 + n * 3]
    calc = sum(body) & 0xFF
    lit = sum(1 for i in range(0, len(body), 3)
              if not (body[i] == 0 and body[i + 1] == 0 and body[i + 2] == 0))
    return {
        "ok": checksum == calc and head == FRAME_HEAD,
        "rows": rows, "cols": cols, "beads": n,
        "lit": lit, "bytes": len(frame),
        "checksum_ok": checksum == calc,
    }


def list_ports() -> list:
    """列出可用串口，返回 [(device, description), ...]。"""
    if not _HAS_SERIAL:
        return []
    try:
        return [(p.device, p.description or "") for p in
                serial.tools.list_ports.comports()]
    except Exception:
        return []


def send_frame(frame: bytes, port: str, baud: int = DEFAULT_BAUD,
               timeout: float = 2.0) -> None:
    """把一帧写到串口。失败抛异常（由调用方提示）。"""
    if not _HAS_SERIAL:
        raise RuntimeError("未安装 pyserial。请先安装：pip install pyserial")
    with serial.Serial(port=port, baudrate=baud, timeout=timeout) as ser:
        ser.write(frame)
        ser.flush()


def has_serial() -> bool:
    return _HAS_SERIAL
