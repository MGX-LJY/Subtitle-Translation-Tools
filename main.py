# -*- coding: utf-8 -*-
"""
AI 字幕翻译器 - 模块化版本入口文件
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from ui import MainWindow
from utils import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)


def main():
    """应用程序主入口"""
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        logger.info("应用程序启动成功")
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())