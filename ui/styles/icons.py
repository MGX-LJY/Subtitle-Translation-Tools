# -*- coding: utf-8 -*-
"""
图标系统
提供统一的图标接口和图标资源
"""

from typing import Dict, Optional
from enum import Enum


class IconSize(Enum):
    """图标尺寸枚举"""
    SMALL = 16
    MEDIUM = 20
    LARGE = 24
    XLARGE = 32


class IconProvider:
    """图标提供器 - 使用Unicode字符作为图标"""
    
    # 文件操作图标
    OPEN = "📁"
    SAVE = "💾"
    EXPORT = "📤"
    IMPORT = "📥"
    NEW = "📄"
    FOLDER = "📂"
    
    # 翻译操作图标  
    TRANSLATE = "🌐"
    FIX = "🔧"
    REFRESH = "🔄"
    MAGIC = "✨"
    LANGUAGE = "🗣️"
    
    # 播放控制图标
    PLAY = "▶️"
    PAUSE = "⏸️"
    STOP = "⏹️"
    SKIP_FORWARD = "⏭️"
    SKIP_BACKWARD = "⏮️"
    
    # 编辑操作图标
    EDIT = "✏️"
    DELETE = "🗑️"
    COPY = "📋"
    CUT = "✂️"
    PASTE = "📄"
    UNDO = "↶"
    REDO = "↷"
    
    # 系统操作图标
    SETTINGS = "⚙️"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    SUCCESS = "✅"
    QUESTION = "❓"
    
    # 导航图标
    MENU = "☰"
    CLOSE = "✕"
    MINIMIZE = "−"
    MAXIMIZE = "□"
    BACK = "←"
    FORWARD = "→"
    UP = "↑"
    DOWN = "↓"
    
    # 状态图标
    LOADING = "⏳"
    DONE = "✓"
    PENDING = "○"
    PROCESSING = "⚡"
    
    # 其他图标
    STAR = "⭐"
    HEART = "❤️"
    BOOKMARK = "🔖"
    TAG = "🏷️"
    SEARCH = "🔍"
    FILTER = "🔽"
    SORT = "⇅"
    
    @classmethod
    def get_icon(cls, name: str, size: IconSize = IconSize.MEDIUM) -> str:
        """
        获取图标字符
        
        Args:
            name: 图标名称
            size: 图标尺寸
            
        Returns:
            图标字符串
        """
        icon = getattr(cls, name.upper(), "")
        return icon
    
    @classmethod
    def get_sized_icon(cls, icon: str, size: IconSize) -> str:
        """
        获取指定尺寸的图标样式
        
        Args:
            icon: 图标字符
            size: 图标尺寸
            
        Returns:
            带样式的图标HTML
        """
        size_px = size.value
        return f'<span style="font-size: {size_px}px; line-height: 1;">{icon}</span>'
    
    @classmethod
    def create_icon_button_text(cls, icon: str, text: str, 
                               size: IconSize = IconSize.MEDIUM) -> str:
        """
        创建图标+文本的按钮内容
        
        Args:
            icon: 图标字符
            text: 按钮文本
            size: 图标尺寸
            
        Returns:
            格式化的按钮文本
        """
        return f"{icon} {text}"
    
    @classmethod
    def get_file_icon(cls, file_extension: str) -> str:
        """
        根据文件扩展名获取对应图标
        
        Args:
            file_extension: 文件扩展名
            
        Returns:
            文件类型图标
        """
        icon_map = {
            '.srt': '📝',
            '.txt': '📄',
            '.json': '⚙️',
            '.log': '📊',
            '.py': '🐍',
            '.md': '📑',
        }
        return icon_map.get(file_extension.lower(), '📄')
    
    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """
        根据状态获取对应图标
        
        Args:
            status: 状态名称
            
        Returns:
            状态图标
        """
        status_map = {
            'success': cls.SUCCESS,
            'error': cls.ERROR,
            'warning': cls.WARNING,
            'info': cls.INFO,
            'loading': cls.LOADING,
            'done': cls.DONE,
            'pending': cls.PENDING,
            'processing': cls.PROCESSING,
        }
        return status_map.get(status.lower(), cls.INFO)