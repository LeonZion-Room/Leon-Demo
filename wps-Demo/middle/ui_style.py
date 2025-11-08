#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


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


def build_style(scale: float) -> str:
    b = dp(scale, 2)
    r_card = dp(scale, 12)
    r_btn = dp(scale, 10)
    pad = dp(scale, 8)
    btn_pad_v = dp(scale, 8)
    btn_pad_h = dp(scale, 14)
    return f"""
* {{ font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; }}
QWidget {{ background-color: #0b1020; color: #e6e8ef; }}

QFrame#Card, QFrame#PreviewCard, QFrame#PanelCard, QFrame#LogCard {{
    background-color: #0b1020;
    border: {b}px solid #e0a857;
    border-radius: {r_card}px;
}}

QLabel#Title {{ font-size: {dp(scale, 20)}px; font-weight: 700; }}

QPushButton {{
    background-color: #2f5fae;
    color: #ffffff;
    border: {b}px solid #e0a857;
    padding: {btn_pad_v}px {btn_pad_h}px;
    border-radius: {r_btn}px;
    font-size: {dp(scale, 14)}px;
}}
QPushButton:hover {{ background-color: #3c6fd1; }}
QPushButton:disabled {{ background-color: #294f8a; color: #b8c1d9; border-color: #a78a50; }}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: #11162a;
    border: {b}px solid #e0a857;
    border-radius: {r_btn}px;
    padding: {pad}px;
    color: #e6e8ef;
    font-size: {dp(scale, 14)}px;
}}

QProgressBar {{
    border: {b}px solid #e0a857;
    border-radius: {r_btn}px;
    text-align: center;
    height: {dp(scale, 20)}px;
    font-size: {dp(scale, 12)}px;
}}
QProgressBar::chunk {{ background-color: #2f5fae; border-radius: {dp(scale, 8)}px; }}
"""