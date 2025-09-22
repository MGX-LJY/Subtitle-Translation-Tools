# -*- coding: utf-8 -*-
"""
日志配置工具
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = "translator.log"
) -> None:
    """
    设置应用日志配置
    
    Args:
        level: 日志级别
        log_file: 日志文件路径，None 表示不写入文件
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(
            logging.FileHandler(log_file, encoding="utf-8")
        )
    
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        handlers=handlers
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    return logging.getLogger(name)