#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
import os
import json
from typing import Optional, Dict


def dp(scale: float, value: float) -> int:
    return int(round(value * scale))


def compute_scale(app: QApplication, base_width: int = 1280, base_height: int = 720) -> float:
    screen = app.primaryScreen()
    if not screen:
        return 1.0
    g = screen.availableGeometry()
    sw = g.width() / float(base_width)
    sh = g.height() / float(base_height)
    dpi_scale = screen.logicalDotsPerInch() / 96.0
    scale = (sw + sh) / 2.0
    scale = scale * max(1.0, dpi_scale * 0.9)
    return max(0.85, min(1.8, scale))


def apply_base_font(app: QApplication, scale: float) -> None:
    font = QFont('Microsoft YaHei UI', dp(scale, 11))
    app.setFont(font)


def build_style(scale: float, palette: Optional[Dict[str, str]] = None) -> str:
    # Sizes
    b = dp(scale, 1)
    r_card = dp(scale, 10)
    r_btn = dp(scale, 8)
    pad = dp(scale, 6)
    # 紧凑按钮内边距（更贴近文本与边缘）
    btn_pad_v = dp(scale, 4)
    btn_pad_h = dp(scale, 8)

    # 默认 Nordic Blue 配色（无金色）
    default_palette = {
        "bg": "#0b1624",
        "panel": "#0e1c2e",
        "text": "#e6edf5",
        "muted": "#b9c7d9",
        "border": "#000000",
        "primary": "#3a5f78",
        "primary_hover": "#34576f",
        "primary_disabled": "#2a465a",
        "input_bg": "#132235",
    }

    # 允许通过外部 JSON（ui_palette.json）或传入参数覆盖配色
    file_palette = None
    try:
        p = os.path.join(os.path.dirname(__file__), "ui_palette.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                file_palette = json.load(f)
    except Exception:
        file_palette = None

    final_palette = {**default_palette, **(file_palette or {}), **(palette or {})}

    bg = final_palette["bg"]
    panel = final_palette["panel"]
    text = final_palette["text"]
    muted = final_palette["muted"]
    border = final_palette["border"]
    primary = final_palette["primary"]
    primary_hover = final_palette["primary_hover"]
    primary_disabled = final_palette["primary_disabled"]
    input_bg = final_palette["input_bg"]

    return f"""
* {{ font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; }}
QWidget {{ background-color: {bg}; color: {text}; }}

QFrame#Card, QFrame#PreviewCard, QFrame#PanelCard, QFrame#LogCard {{
    background-color: {panel};
    border: {b}px solid {border};
    border-radius: {r_card}px;
}}

QLabel#Title {{ font-size: {dp(scale, 18)}px; font-weight: 700; }}
QLabel {{ font-size: {dp(scale, 13)}px; }}

QPushButton {{
    background-color: {primary};
    color: #f0f6fb;
    border: {b}px solid {border};
    padding: {btn_pad_v}px {btn_pad_h}px;
    border-radius: {r_btn}px;
    font-size: {dp(scale, 13)}px;
    min-height: {dp(scale, 28)}px;
}}
QPushButton:hover {{ background-color: {primary_hover}; }}
QPushButton:disabled {{ background-color: {primary_disabled}; color: {muted}; border-color: {border}; }}

    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
        background-color: {input_bg};
        border: {b}px solid {border};
        border-radius: {r_btn}px;
        padding: {pad}px;
        color: {text};
        font-size: {dp(scale, 13)}px;
        min-height: {dp(scale, 28)}px;
    }}

    /* 占位符文字更柔和，避免视觉拥挤 */
    QLineEdit::placeholder {{
        color: {muted};
    }}

/* 统一列表与滚动区域样式 */
QScrollArea {{
    background-color: {panel};
    border: {b}px solid {border};
    border-radius: {r_card}px;
}}
QListWidget {{
    background-color: {panel};
    border: {b}px solid {border};
    border-radius: {r_card}px;
    padding: {pad}px;
    color: {text};
    font-size: {dp(scale, 14)}px;
}}
QListWidget::item:selected {{
    background-color: {primary};
    color: #f0f6fb;
}}

/* 按钮选中态（用于切换型按钮） */
QPushButton:checked {{
    background-color: {primary_hover};
}}

QComboBox QAbstractItemView {{
    background-color: {panel};
    color: {text};
    border: {b}px solid {border};
    selection-background-color: {primary};
    font-size: {dp(scale, 14)}px;
}}

QProgressBar {{
    border: {b}px solid {border};
    border-radius: {r_btn}px;
    text-align: center;
    height: {dp(scale, 16)}px;
    font-size: {dp(scale, 12)}px;
}}
QProgressBar::chunk {{ background-color: {primary}; border-radius: {dp(scale, 8)}px; }}

QToolTip {{
    background-color: {input_bg};
    color: {text};
    border: {b}px solid {border};
    padding: {dp(scale, 6)}px {dp(scale, 10)}px;
    font-size: {dp(scale, 13)}px;
}}
"""