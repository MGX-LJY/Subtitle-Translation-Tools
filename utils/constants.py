# -*- coding: utf-8 -*-
"""
应用常量定义
"""

from pathlib import Path

# 文件相关常量
CONFIG_FILENAME = "main.config.json"
LOG_FILENAME = "translator.log"

# 翻译相关常量
MAX_CONCURRENCY = 8  # 最大并发数
REQUEST_TIMEOUT = 25  # API 请求超时时间（秒）

# 支持的模型列表
SUPPORTED_MODELS = [
    "gpt-4o-mini",
    "gpt-4o", 
    "gpt-4o-128k",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k"
]

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "中文",
    "English", 
    "日本語",
    "Español",
    "Français",
    "Deutsch"
]

# UI相关常量
WINDOW_TITLE = "AI 字幕翻译器"
WINDOW_DEFAULT_SIZE = (1120, 650)

# 表格列定义
TABLE_COLUMNS = ["#", "开始", "结束", "原文", "译文", "修复后", "恢复"]
TABLE_COLUMN_COUNT = len(TABLE_COLUMNS)

# 文件过滤器
SRT_FILE_FILTER = "SRT (*.srt)"