# -*- coding: utf-8 -*-
"""
主题系统
定义颜色方案、字体、间距等设计规范
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ColorPalette:
    """颜色调色板"""
    # 主色调
    primary: str
    primary_hover: str
    primary_pressed: str
    primary_disabled: str
    
    # 次要色调
    secondary: str
    secondary_hover: str
    secondary_pressed: str
    
    # 背景色
    background: str
    surface: str
    card: str
    overlay: str
    
    # 文本色
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_inverse: str
    
    # 边框色
    border: str
    border_light: str
    border_focus: str
    
    # 状态色
    success: str
    warning: str
    error: str
    info: str
    
    # 阴影色
    shadow: str
    shadow_light: str


@dataclass 
class Typography:
    """字体规范"""
    font_family: str = "Arial, 'Helvetica Neue', Helvetica, sans-serif"
    font_size_xs: int = 10
    font_size_sm: int = 12
    font_size_base: int = 14
    font_size_lg: int = 16
    font_size_xl: int = 18
    font_size_2xl: int = 24
    font_size_3xl: int = 32
    
    font_weight_light: int = 300
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_bold: int = 700
    
    line_height_tight: float = 1.25
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75


@dataclass
class Spacing:
    """间距规范"""
    xs: int = 4
    sm: int = 8
    base: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48
    
    border_radius_sm: int = 4
    border_radius_base: int = 8
    border_radius_lg: int = 12
    border_radius_xl: int = 16
    border_radius_full: int = 9999


@dataclass
class Animation:
    """动画规范"""
    duration_fast: int = 150
    duration_normal: int = 300
    duration_slow: int = 500
    
    easing_ease: str = "ease"
    easing_ease_in: str = "ease-in"
    easing_ease_out: str = "ease-out"
    easing_ease_in_out: str = "ease-in-out"


class Theme(ABC):
    """主题基类"""
    
    def __init__(self):
        self.colors = self.get_colors()
        self.typography = Typography()
        self.spacing = Spacing()
        self.animation = Animation()
    
    @abstractmethod
    def get_colors(self) -> ColorPalette:
        """获取颜色调色板"""
        pass
    
    @property
    def name(self) -> str:
        """主题名称"""
        return self.__class__.__name__.replace("Theme", "").lower()


class LightTheme(Theme):
    """明亮主题"""
    
    def get_colors(self) -> ColorPalette:
        return ColorPalette(
            # 主色调 - 现代蓝色
            primary="#2563eb",
            primary_hover="#1d4ed8", 
            primary_pressed="#1e40af",
            primary_disabled="#93c5fd",
            
            # 次要色调 - 优雅紫色
            secondary="#7c3aed",
            secondary_hover="#6d28d9",
            secondary_pressed="#5b21b6",
            
            # 背景色 - 纯净白色系
            background="#ffffff",
            surface="#f8fafc",
            card="#ffffff",
            overlay="rgba(0, 0, 0, 0.1)",
            
            # 文本色 - 高对比度
            text_primary="#1e293b",
            text_secondary="#64748b",
            text_disabled="#94a3b8",
            text_inverse="#ffffff",
            
            # 边框色 - 精细层次
            border="#e2e8f0",
            border_light="#f1f5f9",
            border_focus="#2563eb",
            
            # 状态色 - 语义化
            success="#16a34a",
            warning="#ea580c",
            error="#dc2626", 
            info="#0284c7",
            
            # 阴影色 - 立体感
            shadow="rgba(0, 0, 0, 0.1)",
            shadow_light="rgba(0, 0, 0, 0.05)"
        )


class DarkTheme(Theme):
    """暗黑主题"""
    
    def get_colors(self) -> ColorPalette:
        return ColorPalette(
            # 主色调 - 明亮蓝色
            primary="#3b82f6",
            primary_hover="#2563eb",
            primary_pressed="#1d4ed8",
            primary_disabled="#1e40af",
            
            # 次要色调 - 明亮紫色
            secondary="#8b5cf6",
            secondary_hover="#7c3aed", 
            secondary_pressed="#6d28d9",
            
            # 背景色 - 深色系
            background="#0f172a",
            surface="#1e293b",
            card="#334155",
            overlay="rgba(0, 0, 0, 0.5)",
            
            # 文本色 - 高对比度
            text_primary="#f1f5f9",
            text_secondary="#cbd5e1",
            text_disabled="#64748b",
            text_inverse="#1e293b",
            
            # 边框色 - 精细层次
            border="#475569",
            border_light="#334155",
            border_focus="#3b82f6",
            
            # 状态色 - 语义化
            success="#22c55e",
            warning="#f59e0b",
            error="#ef4444",
            info="#06b6d4",
            
            # 阴影色 - 立体感
            shadow="rgba(0, 0, 0, 0.3)",
            shadow_light="rgba(0, 0, 0, 0.15)"
        )