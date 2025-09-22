# -*- coding: utf-8 -*-
"""
AI Subtitle Translator - 模块化版本
智能字幕翻译工具，支持多种翻译服务和文件格式
"""

__version__ = "2.0.0"
__author__ = "AI Subtitle Translator Team"

from .models import Config, SubtitleCue
from .services import ConfigService, FileService, TranslationService
from .ui import MainWindow

__all__ = [
    "Config",
    "SubtitleCue", 
    "ConfigService",
    "FileService",
    "TranslationService",
    "MainWindow"
]