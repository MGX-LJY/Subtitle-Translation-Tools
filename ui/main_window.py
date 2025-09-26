# -*- coding: utf-8 -*-
"""
主窗口
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QToolBar, QStatusBar, QProgressBar, QLabel,
    QPushButton, QFileDialog, QMessageBox, QHeaderView, QApplication,
    QDialog, QFrame, QSplitter, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QPixmap, QPalette

from models import SubtitleCue, Config
from services import ConfigService, FileService, OpenAIService
from services.translation_service import TranslationProgress, TranslationResult
from utils import (
    get_logger, WINDOW_TITLE, WINDOW_DEFAULT_SIZE, TABLE_COLUMNS, 
    SRT_FILE_FILTER
)
from .settings_dialog import SettingsDialog
from .styles import StyleSheet, IconProvider, LightTheme

logger = get_logger(__name__)


class TranslationWorker(QThread):
    """翻译工作线程"""
    
    progress_updated = Signal(int, int)  # 完成数, 总数
    result_ready = Signal(int, str, str)  # 行号, 翻译文本, 修复文本
    token_updated = Signal(int, int)  # prompt_tokens, completion_tokens
    error_occurred = Signal(str)  # 错误消息
    finished_signal = Signal(str)  # 模式
    
    def __init__(self, cues: List[SubtitleCue], config: Config, mode: str):
        super().__init__()
        self.cues = cues.copy()  # 创建副本
        self.config = config
        self.mode = mode
        self.translation_service = OpenAIService(config)
    
    def run(self):
        """线程执行入口"""
        try:
            asyncio.run(self._translate_batch())
        except Exception as e:
            logger.error(f"翻译线程执行失败: {e}")
            self.error_occurred.emit(str(e))
    
    async def _translate_batch(self):
        """批量翻译"""
        def progress_callback(progress: TranslationProgress):
            self.progress_updated.emit(progress.completed, progress.total)
        
        def result_callback(result: TranslationResult):
            if result.success:
                cue = self.cues[result.index]
                if self.mode == "translate":
                    cue.set_translation(result.translated_text)
                else:
                    cue.set_fixed_text(result.translated_text)
                
                self.result_ready.emit(
                    result.index, 
                    cue.translation, 
                    cue.fixed_text
                )
                self.token_updated.emit(
                    result.prompt_tokens, 
                    result.completion_tokens
                )
            else:
                self.error_occurred.emit(
                    f"翻译第 {result.index + 1} 行失败: {result.error_message}"
                )
        
        try:
            await self.translation_service.translate_batch(
                cues=self.cues,
                mode=self.mode,
                progress_callback=progress_callback,
                result_callback=result_callback
            )
            
            self.finished_signal.emit(self.mode)
            
        except Exception as e:
            logger.error(f"批量翻译失败: {e}")
            self.error_occurred.emit(str(e))
        finally:
            await self.translation_service.close()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化服务
        self.config_service = ConfigService()
        self.file_service = FileService()
        self.config = self.config_service.load_config()
        
        # 初始化数据
        self.cues: List[SubtitleCue] = []
        self.history: List[List[SubtitleCue]] = []
        self.current_file: Optional[Path] = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        
        # 初始化UI
        self._setup_ui()
        self._setup_styles()
        
        logger.info("主窗口初始化完成")
    
    def _setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(*WINDOW_DEFAULT_SIZE)
        self.setMinimumSize(1000, 700)
        
        # 应用现代主题
        self.theme = LightTheme()
        self.icons = IconProvider()
        
        # 创建主要组件
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()
        
        # 设置中央窗口
        self.setCentralWidget(self.main_widget)
    
    def _create_toolbar(self):
        """创建现代化工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setObjectName("mainToolbar")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        
        # 文件操作组
        file_actions = [
            (self.icons.OPEN + " 打开", self._open_file, "打开SRT字幕文件"),
            (self.icons.SAVE + " 保存", self._save_file, "保存当前字幕文件"),
            (self.icons.EXPORT + " 导出", self._export_file, "导出翻译后的字幕")
        ]
        
        for text, callback, tooltip in file_actions:
            action = self._create_action(text, callback, tooltip)
            toolbar.addAction(action)
        
        toolbar.addSeparator()
        
        # 翻译操作组
        translate_actions = [
            (self.icons.TRANSLATE + " 全部翻译", self._translate_all, "对所有字幕进行 AI 翻译"),
            (self.icons.FIX + " 全部修复", self._fix_all, "修复和优化翻译结果")
        ]
        
        for text, callback, tooltip in translate_actions:
            action = self._create_action(text, callback, tooltip)
            toolbar.addAction(action)
        
        toolbar.addSeparator()
        
        # 其他操作组
        other_actions = [
            (self.icons.UNDO + " 撤销", self._undo, "撤销上一步操作"),
            (self.icons.SETTINGS + " 设置", self._open_settings, "打开应用设置")
        ]
        
        for text, callback, tooltip in other_actions:
            action = self._create_action(text, callback, tooltip)
            toolbar.addAction(action)
    
    def _create_action(self, text: str, callback, tooltip: str = "") -> QAction:
        """创建动作"""
        action = QAction(text, self)
        action.triggered.connect(callback)
        if tooltip:
            action.setToolTip(tooltip)
        return action
    
    def _create_main_content(self):
        """创建主内容区域"""
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # 创建上部信息面板
        self._create_info_panel(main_layout)
        
        # 创建字幕表格区域
        self._create_table_section(main_layout)
        
        # 创建底部控制面板
        self._create_control_panel(main_layout)
    
    def _create_info_panel(self, parent_layout):
        """创建信息面板"""
        info_frame = QFrame()
        info_frame.setObjectName("infoPanel")
        info_frame.setFrameStyle(QFrame.Box)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        # 文件信息
        self.file_info_label = QLabel(f"{self.icons.FOLDER} 未加载文件")
        self.file_info_label.setObjectName("fileInfo")
        info_layout.addWidget(self.file_info_label)
        
        info_layout.addStretch()
        
        # 状态信息
        self.status_info_label = QLabel(f"{self.icons.INFO} 就绪")
        self.status_info_label.setObjectName("statusInfo")
        info_layout.addWidget(self.status_info_label)
        
        parent_layout.addWidget(info_frame)
    
    def _create_table_section(self, parent_layout):
        """创建表格区域"""
        # 表格容器
        table_frame = QFrame()
        table_frame.setObjectName("tableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(8)
        
        # 表格标题
        table_title = QLabel(f"{self.icons.EDIT} 字幕编辑器")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        
        # 创建表格
        self._create_modern_table()
        table_layout.addWidget(self.table)
        
        parent_layout.addWidget(table_frame, 1)  # 让表格占据主要空间
    
    def _create_modern_table(self):
        """创建现代化表格"""
        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setObjectName("subtitleTable")
        self.table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        
        # 设置列宽策略
        header = self.table.horizontalHeader()
        for i in [0, 1, 2, 6]:  # 序号、开始、结束、恢复列
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        for i in [3, 4, 5]:  # 原文、译文、修复列
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        # 设置表格属性
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        
        # 设置表格高度
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().hide()
    
    def _create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_frame = QFrame()
        control_frame.setObjectName("controlPanel")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(16, 12, 16, 12)
        control_layout.setSpacing(12)
        
        # 创建进度条区域
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)
        
        self.progress_label = QLabel(f"{self.icons.LOADING} 翻译进度")
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("mainProgressBar")
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        control_layout.addWidget(progress_widget, 1)
        
        # 快捷操作按钮组
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # 翻译按钮
        self.translate_btn = QPushButton(f"{self.icons.TRANSLATE} 开始翻译")
        self.translate_btn.setObjectName("primaryButton")
        self.translate_btn.clicked.connect(self._translate_all)
        button_layout.addWidget(self.translate_btn)
        
        # 修复按钮
        self.fix_btn = QPushButton(f"{self.icons.FIX} 修复翻译")
        self.fix_btn.setObjectName("secondaryButton")
        self.fix_btn.clicked.connect(self._fix_all)
        button_layout.addWidget(self.fix_btn)
        
        # 撤销按钮
        self.undo_btn = QPushButton(f"{self.icons.UNDO} 撤销")
        self.undo_btn.setObjectName("secondaryButton")
        self.undo_btn.clicked.connect(self._undo)
        button_layout.addWidget(self.undo_btn)
        
        control_layout.addWidget(button_group)
        parent_layout.addWidget(control_frame)
    
    def _create_status_bar(self):
        """创建现代化状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("modernStatusBar")
        self.setStatusBar(self.status_bar)
        
        # 状态文本
        self.status_text = QLabel(f"{self.icons.INFO} 就绪")
        self.status_text.setObjectName("statusText")
        self.status_bar.addWidget(self.status_text)
        
        # Token 计数标签
        self.token_label = QLabel(f"{self.icons.STAR} Tokens P:0 | C:0")
        self.token_label.setObjectName("tokenCounter")
        self.status_bar.addPermanentWidget(self.token_label)
    
    def _setup_styles(self):
        """应用现代化样式"""
        # 设置现代风格
        QApplication.setStyle("Fusion")
        
        # 应用主题样式
        stylesheet = StyleSheet.get_light_theme_stylesheet()
        
        # 添加特定组件样式
        custom_styles = f"""
        /* 信息面板样式 */
        QFrame#infoPanel {{
            background-color: {self.theme.colors.surface};
            border: 1px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_lg}px;
            padding: {self.theme.spacing.base}px;
        }}
        
        QLabel#fileInfo {{
            font-size: {self.theme.typography.font_size_lg}px;
            font-weight: {self.theme.typography.font_weight_medium};
            color: {self.theme.colors.text_primary};
        }}
        
        QLabel#statusInfo {{
            font-size: {self.theme.typography.font_size_base}px;
            color: {self.theme.colors.text_secondary};
        }}
        
        /* 表格标题样式 */
        QLabel#sectionTitle {{
            font-size: {self.theme.typography.font_size_xl}px;
            font-weight: {self.theme.typography.font_weight_bold};
            color: {self.theme.colors.text_primary};
            padding: {self.theme.spacing.sm}px 0px;
        }}
        
        /* 控制面板样式 */
        QFrame#controlPanel {{
            background-color: {self.theme.colors.surface};
            border: 1px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_lg}px;
        }}
        
        QLabel#progressLabel {{
            font-size: {self.theme.typography.font_size_sm}px;
            color: {self.theme.colors.text_secondary};
            font-weight: {self.theme.typography.font_weight_medium};
        }}
        
        QPushButton#primaryButton {{
            background-color: {self.theme.colors.primary};
            color: {self.theme.colors.text_inverse};
            border: 1px solid {self.theme.colors.primary};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px {self.theme.spacing.lg}px;
            font-weight: {self.theme.typography.font_weight_medium};
            min-width: 120px;
            min-height: 40px;
        }}
        
        QPushButton#primaryButton:hover {{
            background-color: {self.theme.colors.primary_hover};
            border-color: {self.theme.colors.primary_hover};
        }}
        
        QPushButton#secondaryButton {{
            background-color: transparent;
            color: {self.theme.colors.text_primary};
            border: 1px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px {self.theme.spacing.lg}px;
            font-weight: {self.theme.typography.font_weight_medium};
            min-width: 100px;
            min-height: 40px;
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {self.theme.colors.surface};
            border-color: {self.theme.colors.primary};
            color: {self.theme.colors.primary};
        }}
        
        /* 状态栏样式 */
        QStatusBar#modernStatusBar {{
            background-color: {self.theme.colors.surface};
            border-top: 1px solid {self.theme.colors.border};
            padding: {self.theme.spacing.sm}px {self.theme.spacing.base}px;
        }}
        
        QLabel#statusText {{
            color: {self.theme.colors.text_secondary};
            font-size: {self.theme.typography.font_size_sm}px;
        }}
        
        QLabel#tokenCounter {{
            color: {self.theme.colors.text_secondary};
            font-size: {self.theme.typography.font_size_sm}px;
            font-weight: {self.theme.typography.font_weight_medium};
            padding: {self.theme.spacing.xs}px {self.theme.spacing.sm}px;
            background-color: {self.theme.colors.card};
            border: 1px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_base}px;
        }}
        """
        
        # 应用样式
        QApplication.instance().setStyleSheet(stylesheet + custom_styles)
    
    def _refresh_table(self):
        """刷新表格显示"""
        self.table.setRowCount(len(self.cues))
        for row, cue in enumerate(self.cues):
            self._update_table_row(row, cue.translation, cue.fixed_text)
    
    def _update_table_row(self, row: int, translation: str, fixed_text: str):
        """更新表格行"""
        cue = self.cues[row]
        cue.translation = translation
        cue.fixed_text = fixed_text
        
        # 设置表格数据
        values = [
            str(cue.index),
            cue.start,
            cue.end,
            cue.original,
            cue.translation,
            cue.fixed_text,
            ""
        ]
        
        for col, value in enumerate(values[:-1]):  # 排除最后一列（恢复按钮）
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            if col > 2:  # 原文、译文、修复列可编辑
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, col, item)
        
        # 恢复按钮
        if cue.has_translation:
            restore_button = QPushButton("恢复")
            restore_button.clicked.connect(lambda: self._restore_translation(row))
            self.table.setCellWidget(row, 6, restore_button)
        else:
            self.table.setCellWidget(row, 6, QWidget())
    
    def _restore_translation(self, row: int):
        """恢复翻译"""
        if 0 <= row < len(self.cues):
            self.cues[row].clear_translation()
            self._update_table_row(row, "", "")
    
    def _save_history(self):
        """保存历史状态"""
        # 创建当前状态的深拷贝
        history_state = []
        for cue in self.cues:
            history_state.append(SubtitleCue(
                index=cue.index,
                start=cue.start,
                end=cue.end,
                original=cue.original,
                translation=cue.translation,
                fixed_text=cue.fixed_text
            ))
        self.history.append(history_state)
    
    def _update_token_display(self):
        """更新Token显示"""
        self.token_label.setText(
            f"{self.icons.STAR} Tokens P:{self.prompt_tokens} | C:{self.completion_tokens}"
        )
    
    # 文件操作方法
    def _open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 SRT 文件", "", SRT_FILE_FILTER
        )
        
        if file_path:
            try:
                path = Path(file_path)
                self.cues = self.file_service.parse_srt(path)
                self.current_file = path
                self._refresh_table()
                self.history.clear()
                
                # 更新UI显示
                self.file_info_label.setText(f"{self.icons.get_file_icon('.srt')} {path.name}")
                self.status_info_label.setText(f"{self.icons.SUCCESS} 已加载 {len(self.cues)} 条字幕")
                self.status_text.setText(f"{self.icons.INFO} 文件加载完成")
                logger.info(f"成功加载文件: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件失败：{str(e)}")
                logger.error(f"加载文件失败: {e}")
    
    def _save_file(self):
        """保存文件"""
        if not self.cues:
            QMessageBox.warning(self, "提示", "没有可保存的内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "translated.srt", SRT_FILE_FILTER
        )
        
        if file_path:
            try:
                self.file_service.write_srt(Path(file_path), self.cues)
                self.status_text.setText(f"{self.icons.SUCCESS} 文件已保存")
                logger.info(f"文件保存成功: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")
                logger.error(f"保存文件失败: {e}")
    
    def _export_file(self):
        """导出文件"""
        if not self.cues:
            QMessageBox.warning(self, "提示", "没有可导出的内容")
            return
        
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not export_dir:
            return
        
        try:
            # 生成文件名
            if self.current_file:
                filename = f"{self.current_file.stem}_翻译后.srt"
            else:
                filename = "translated.srt"
            
            export_path = Path(export_dir) / filename
            self.file_service.write_srt(export_path, self.cues)
            self.status_text.setText(f"{self.icons.SUCCESS} 文件已导出")
            logger.info(f"文件导出成功: {export_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出文件失败：{str(e)}")
            logger.error(f"导出文件失败: {e}")
    
    # 翻译操作方法
    def _translate_all(self):
        """全部翻译"""
        self._start_translation("translate")
    
    def _fix_all(self):
        """全部修复"""
        self._start_translation("fix")
    
    def _start_translation(self, mode: str):
        """开始翻译任务"""
        if not self._check_ready():
            return
        
        # 重置计数器
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self._update_token_display()
        
        # 设置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.cues))
        self.progress_bar.setVisible(True)
        
        # 保存历史状态
        self._save_history()
        
        # 创建并启动翻译线程
        self.translation_worker = TranslationWorker(
            self.cues, self.config, mode
        )
        
        # 连接信号
        self.translation_worker.progress_updated.connect(
            self.progress_bar.setValue
        )
        self.translation_worker.result_ready.connect(
            self._update_table_row
        )
        self.translation_worker.token_updated.connect(
            self._add_tokens
        )
        self.translation_worker.error_occurred.connect(
            self._show_error
        )
        self.translation_worker.finished_signal.connect(
            self._translation_finished
        )
        
        self.translation_worker.start()
        
        mode_text = "翻译" if mode == "translate" else "修复"
        self.status_bar.showMessage(f"{mode_text}任务进行中...")
        logger.info(f"开始{mode_text}任务")
    
    def _check_ready(self) -> bool:
        """检查是否准备就绪"""
        if not self.cues:
            QMessageBox.warning(self, "提示", "请先加载 SRT 文件")
            return False
        
        if not self.config.is_valid:
            QMessageBox.warning(self, "提示", "请先在设置中配置 API Key")
            return False
        
        return True
    
    def _add_tokens(self, prompt_tokens: int, completion_tokens: int):
        """添加Token计数"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self._update_token_display()
    
    def _show_error(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, "翻译错误", message)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("翻译中断")
    
    def _translation_finished(self, mode: str):
        """翻译完成"""
        self.progress_bar.setVisible(False)
        mode_text = "翻译" if mode == "translate" else "修复"
        self.status_bar.showMessage(f"{mode_text}全部完成！")
        logger.info(f"{mode_text}任务完成")
    
    # 其他操作方法
    def _undo(self):
        """撤销操作"""
        if self.history:
            self.cues = self.history.pop()
            self._refresh_table()
            self.status_bar.showMessage("已撤销上一步操作")
        else:
            QMessageBox.information(self, "提示", "没有可撤销的操作")
    
    def _open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.config, self.config_service, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.get_config()
            self.status_bar.showMessage("设置已更新")
            logger.info("配置已更新")