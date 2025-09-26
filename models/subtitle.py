# -*- coding: utf-8 -*-
"""
字幕数据模型
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SubtitleCue:
    """字幕条目数据模型"""
    index: int                      # 字幕序号
    start: str                      # 开始时间 "00:00:01,000"
    end: str                        # 结束时间 "00:00:03,000"
    original: str                   # 原始文本
    translation: str = ""           # 翻译文本
    fixed_text: str = ""            # 修复后文本
    
    @property
    def display_text(self) -> str:
        """获取用于显示的文本（优先级：修复后 > 翻译 > 原始）"""
        return self.fixed_text or self.translation or self.original
    
    @property
    def has_translation(self) -> bool:
        """是否有翻译内容"""
        return bool(self.translation or self.fixed_text)
    
    def clear_translation(self) -> None:
        """清除翻译内容"""
        self.translation = ""
        self.fixed_text = ""
    
    def set_translation(self, text: str) -> None:
        """设置翻译文本"""
        self.translation = text
        self.fixed_text = ""  # 清除修复文本
    
    def set_fixed_text(self, text: str) -> None:
        """设置修复后文本"""
        self.fixed_text = text