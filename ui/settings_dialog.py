# -*- coding: utf-8 -*-
"""
设置对话框
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QFrame, QGroupBox,
    QFormLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from models import Config
from services import ConfigService
from utils import SUPPORTED_MODELS, SUPPORTED_LANGUAGES, get_logger
from .styles import StyleSheet, IconProvider, LightTheme

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config: Config, config_service: ConfigService, parent=None):
        """
        初始化设置对话框
        
        Args:
            config: 当前配置对象
            config_service: 配置服务实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config = config
        self.config_service = config_service
        
        # 初始化主题和图标
        self.theme = LightTheme()
        self.icons = IconProvider()
        
        self._setup_ui()
        self._apply_styles()
        self._load_config()
    
    def _setup_ui(self):
        """设置现代化UI界面"""
        self.setWindowTitle(f"{self.icons.SETTINGS} 应用设置")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 标题区域
        self._create_header(main_layout)
        
        # 配置表单区域
        self._create_form_section(main_layout)
        
        # 按钮区域
        self._create_button_section(main_layout)
    
    def _create_header(self, parent_layout):
        """创建标题区域"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 16)
        header_layout.setSpacing(8)
        
        # 主标题
        title_label = QLabel(f"{self.icons.SETTINGS} 应用设置")
        title_label.setObjectName("dialogTitle")
        header_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("配置 AI 翻译服务参数")
        subtitle_label.setObjectName("dialogSubtitle")
        header_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(header_frame)
    
    def _create_form_section(self, parent_layout):
        """创建表单区域"""
        # API 配置组
        api_group = QGroupBox(f"{self.icons.LANGUAGE} API 配置")
        api_group.setObjectName("settingsGroup")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)
        api_layout.setContentsMargins(20, 20, 20, 20)
        
        # API Key 输入
        api_key_label = QLabel(f"🔑 API Key")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setObjectName("passwordInput")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请输入您的 OpenAI API Key")
        api_layout.addRow(api_key_label, self.api_key_edit)
        
        # 接口地址输入
        base_url_label = QLabel(f"🔗 接口地址")
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setObjectName("urlInput")
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1 (留空使用默认地址)")
        api_layout.addRow(base_url_label, self.base_url_edit)
        
        parent_layout.addWidget(api_group)
        
        # 翻译配置组
        translate_group = QGroupBox(f"{self.icons.TRANSLATE} 翻译配置")
        translate_group.setObjectName("settingsGroup")
        translate_layout = QFormLayout(translate_group)
        translate_layout.setSpacing(12)
        translate_layout.setContentsMargins(20, 20, 20, 20)
        
        # 模型选择
        model_label = QLabel(f"{self.icons.MAGIC} AI 模型")
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.addItems(SUPPORTED_MODELS)
        self.model_combo.setEditable(True)
        translate_layout.addRow(model_label, self.model_combo)
        
        # 目标语言选择
        language_label = QLabel(f"{self.icons.LANGUAGE} 目标语言")
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageCombo")
        self.language_combo.addItems(SUPPORTED_LANGUAGES)
        self.language_combo.setEditable(True)
        translate_layout.addRow(language_label, self.language_combo)
        
        parent_layout.addWidget(translate_group)
    
    def _create_button_section(self, parent_layout):
        """创建按钮区域"""
        # 添加弹性空间
        parent_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        button_frame = QFrame()
        button_frame.setObjectName("buttonFrame")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.setSpacing(12)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton(f"{self.icons.CLOSE} 取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 保存按钮
        self.save_button = QPushButton(f"{self.icons.SUCCESS} 保存设置")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_button)
        
        parent_layout.addWidget(button_frame)
    
    def _apply_styles(self):
        """应用现代化样式"""
        dialog_styles = f"""
        /* 对话框样式 */
        QDialog {{
            background-color: {self.theme.colors.background};
            border-radius: {self.theme.spacing.border_radius_lg}px;
        }}
        
        /* 标题样式 */
        QLabel#dialogTitle {{
            font-size: {self.theme.typography.font_size_2xl}px;
            font-weight: {self.theme.typography.font_weight_bold};
            color: {self.theme.colors.text_primary};
            margin-bottom: {self.theme.spacing.xs}px;
        }}
        
        QLabel#dialogSubtitle {{
            font-size: {self.theme.typography.font_size_base}px;
            color: {self.theme.colors.text_secondary};
            margin-bottom: {self.theme.spacing.base}px;
        }}
        
        /* 组样式 */
        QGroupBox#settingsGroup {{
            font-size: {self.theme.typography.font_size_lg}px;
            font-weight: {self.theme.typography.font_weight_medium};
            color: {self.theme.colors.text_primary};
            border: 2px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_lg}px;
            padding-top: {self.theme.spacing.base}px;
            margin-top: {self.theme.spacing.base}px;
        }}
        
        QGroupBox#settingsGroup::title {{
            subcontrol-origin: margin;
            left: {self.theme.spacing.base}px;
            padding: 0 {self.theme.spacing.sm}px 0 {self.theme.spacing.sm}px;
            background-color: {self.theme.colors.background};
        }}
        
        /* 输入框样式 */
        QLineEdit#passwordInput, QLineEdit#urlInput {{
            background-color: {self.theme.colors.card};
            color: {self.theme.colors.text_primary};
            border: 2px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px;
            font-size: {self.theme.typography.font_size_base}px;
            min-height: 20px;
        }}
        
        QLineEdit#passwordInput:focus, QLineEdit#urlInput:focus {{
            border-color: {self.theme.colors.border_focus};
            background-color: {self.theme.colors.background};
        }}
        
        /* 下拉框样式 */
        QComboBox#modelCombo, QComboBox#languageCombo {{
            background-color: {self.theme.colors.card};
            color: {self.theme.colors.text_primary};
            border: 2px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px;
            font-size: {self.theme.typography.font_size_base}px;
            min-height: 20px;
        }}
        
        QComboBox#modelCombo:focus, QComboBox#languageCombo:focus {{
            border-color: {self.theme.colors.border_focus};
        }}
        
        /* 按钮样式 */
        QPushButton#saveButton {{
            background-color: {self.theme.colors.primary};
            color: {self.theme.colors.text_inverse};
            border: 1px solid {self.theme.colors.primary};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px {self.theme.spacing.xl}px;
            font-weight: {self.theme.typography.font_weight_medium};
            font-size: {self.theme.typography.font_size_base}px;
            min-width: 120px;
            min-height: 40px;
        }}
        
        QPushButton#saveButton:hover {{
            background-color: {self.theme.colors.primary_hover};
            border-color: {self.theme.colors.primary_hover};
        }}
        
        QPushButton#cancelButton {{
            background-color: transparent;
            color: {self.theme.colors.text_secondary};
            border: 1px solid {self.theme.colors.border};
            border-radius: {self.theme.spacing.border_radius_base}px;
            padding: {self.theme.spacing.base}px {self.theme.spacing.xl}px;
            font-weight: {self.theme.typography.font_weight_medium};
            font-size: {self.theme.typography.font_size_base}px;
            min-width: 100px;
            min-height: 40px;
        }}
        
        QPushButton#cancelButton:hover {{
            background-color: {self.theme.colors.surface};
            border-color: {self.theme.colors.text_secondary};
            color: {self.theme.colors.text_primary};
        }}
        
        /* 标签样式 */
        QFormLayout QLabel {{
            color: {self.theme.colors.text_primary};
            font-weight: {self.theme.typography.font_weight_medium};
            font-size: {self.theme.typography.font_size_base}px;
            padding-bottom: {self.theme.spacing.xs}px;
        }}
        """
        
        self.setStyleSheet(dialog_styles)
    
    def _load_config(self):
        """加载配置到界面"""
        self.api_key_edit.setText(self.config.api_key)
        self.base_url_edit.setText(self.config.base_url)
        
        # 设置模型选择
        if self.config.model in SUPPORTED_MODELS:
            self.model_combo.setCurrentText(self.config.model)
        else:
            self.model_combo.setCurrentText(self.config.model)
        
        # 设置语言选择
        if self.config.target_lang in SUPPORTED_LANGUAGES:
            self.language_combo.setCurrentText(self.config.target_lang)
        else:
            self.language_combo.setCurrentText(self.config.target_lang)
    
    def _save_config(self):
        """保存配置"""
        try:
            # 更新配置对象
            self.config.api_key = self.api_key_edit.text().strip()
            self.config.base_url = self.base_url_edit.text().strip()
            self.config.model = self.model_combo.currentText().strip()
            self.config.target_lang = self.language_combo.currentText().strip()
            
            # 验证配置
            errors = self.config.validate()
            if errors:
                QMessageBox.warning(
                    self, 
                    "配置错误", 
                    "配置验证失败：\n" + "\n".join(errors)
                )
                return
            
            # 保存配置
            if self.config_service.save_config(self.config):
                logger.info("配置保存成功")
                self.accept()  # 关闭对话框
            else:
                QMessageBox.critical(
                    self, 
                    "保存失败", 
                    "无法保存配置，请检查文件权限"
                )
                
        except Exception as e:
            logger.error(f"保存配置时发生错误: {e}")
            QMessageBox.critical(
                self, 
                "错误", 
                f"保存配置时发生错误：{str(e)}"
            )
    
    def get_config(self) -> Config:
        """获取当前配置"""
        return self.config