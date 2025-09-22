# -*- coding: utf-8 -*-
"""
现代化样式表生成器
基于主题系统生成完整的QSS样式
"""

from .theme import Theme, LightTheme


class StyleSheet:
    """样式表生成器"""
    
    def __init__(self, theme: Theme):
        self.theme = theme
        self.colors = theme.colors
        self.typography = theme.typography
        self.spacing = theme.spacing
        self.animation = theme.animation
    
    def generate(self) -> str:
        """生成完整的QSS样式表"""
        return f"""
/* ==================== 全局样式 ==================== */
QWidget {{
    font-family: {self.typography.font_family};
    font-size: {self.typography.font_size_base}px;
    color: {self.colors.text_primary};
    background-color: {self.colors.background};
    selection-background-color: {self.colors.primary};
    selection-color: {self.colors.text_inverse};
}}

/* ==================== 主窗口样式 ==================== */
QMainWindow {{
    background-color: {self.colors.background};
    border: none;
}}

QMainWindow::separator {{
    background-color: {self.colors.border};
    width: 1px;
    height: 1px;
}}

/* ==================== 工具栏样式 ==================== */
QToolBar {{
    background-color: {self.colors.surface};
    border: none;
    border-bottom: 1px solid {self.colors.border};
    spacing: {self.spacing.sm}px;
    padding: {self.spacing.sm}px {self.spacing.base}px;
}}

QToolBar::separator {{
    background-color: {self.colors.border_light};
    width: 1px;
    margin: {self.spacing.xs}px {self.spacing.sm}px;
}}

QToolButton {{
    background-color: transparent;
    color: {self.colors.text_primary};
    border: 1px solid transparent;
    border-radius: {self.spacing.border_radius_base}px;
    padding: {self.spacing.sm}px {self.spacing.base}px;
    margin: {self.spacing.xs}px;
    font-weight: {self.typography.font_weight_medium};
    min-width: 80px;
}}

QToolButton:hover {{
    background-color: {self.colors.primary_hover};
    color: {self.colors.text_inverse};
    border-color: {self.colors.primary_hover};
}}

QToolButton:pressed {{
    background-color: {self.colors.primary_pressed};
    border-color: {self.colors.primary_pressed};
}}

QToolButton:disabled {{
    background-color: {self.colors.primary_disabled};
    color: {self.colors.text_disabled};
    border-color: {self.colors.border_light};
}}

/* ==================== 按钮样式 ==================== */
QPushButton {{
    background-color: {self.colors.primary};
    color: {self.colors.text_inverse};
    border: 1px solid {self.colors.primary};
    border-radius: {self.spacing.border_radius_base}px;
    padding: {self.spacing.sm}px {self.spacing.lg}px;
    font-weight: {self.typography.font_weight_medium};
    min-width: 80px;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {self.colors.primary_hover};
    border-color: {self.colors.primary_hover};
}}

QPushButton:pressed {{
    background-color: {self.colors.primary_pressed};
    border-color: {self.colors.primary_pressed};
}}

QPushButton:disabled {{
    background-color: {self.colors.primary_disabled};
    color: {self.colors.text_disabled};
    border-color: {self.colors.border_light};
}}

/* 次要按钮样式 */
QPushButton[class="secondary"] {{
    background-color: transparent;
    color: {self.colors.text_primary};
    border: 1px solid {self.colors.border};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {self.colors.surface};
    border-color: {self.colors.primary};
    color: {self.colors.primary};
}}

QPushButton[class="secondary"]:pressed {{
    background-color: {self.colors.border_light};
}}

/* 危险按钮样式 */
QPushButton[class="danger"] {{
    background-color: {self.colors.error};
    border-color: {self.colors.error};
}}

QPushButton[class="danger"]:hover {{
    background-color: #b91c1c;
    border-color: #b91c1c;
}}

/* ==================== 表格样式 ==================== */
QTableWidget {{
    background-color: {self.colors.card};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_lg}px;
    gridline-color: {self.colors.border_light};
    selection-background-color: {self.colors.primary};
    selection-color: {self.colors.text_inverse};
    outline: none;
}}

QTableWidget::item {{
    padding: {self.spacing.sm}px {self.spacing.base}px;
    border: none;
    border-bottom: 1px solid {self.colors.border_light};
}}

QTableWidget::item:selected {{
    background-color: {self.colors.primary};
    color: {self.colors.text_inverse};
}}

QTableWidget::item:hover {{
    background-color: {self.colors.surface};
}}

QTableWidget::item:focus {{
    border: 2px solid {self.colors.border_focus};
    background-color: {self.colors.surface};
}}

/* 表格头部样式 */
QHeaderView::section {{
    background-color: {self.colors.surface};
    color: {self.colors.text_primary};
    border: none;
    border-right: 1px solid {self.colors.border_light};
    border-bottom: 1px solid {self.colors.border};
    padding: {self.spacing.base}px;
    font-weight: {self.typography.font_weight_medium};
    text-align: left;
}}

QHeaderView::section:first {{
    border-left: none;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {self.colors.primary_hover};
    color: {self.colors.text_inverse};
}}

/* ==================== 输入框样式 ==================== */
QLineEdit {{
    background-color: {self.colors.card};
    color: {self.colors.text_primary};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_base}px;
    padding: {self.spacing.sm}px {self.spacing.base}px;
    font-size: {self.typography.font_size_base}px;
    min-height: 32px;
}}

QLineEdit:focus {{
    border-color: {self.colors.border_focus};
    background-color: {self.colors.background};
}}

QLineEdit:disabled {{
    background-color: {self.colors.surface};
    color: {self.colors.text_disabled};
    border-color: {self.colors.border_light};
}}

/* ==================== 下拉框样式 ==================== */
QComboBox {{
    background-color: {self.colors.card};
    color: {self.colors.text_primary};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_base}px;
    padding: {self.spacing.sm}px {self.spacing.base}px;
    min-height: 32px;
    min-width: 120px;
}}

QComboBox:focus {{
    border-color: {self.colors.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: {self.spacing.base}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-style: solid;
    border-width: 4px 4px 0px 4px;
    border-color: {self.colors.text_secondary} transparent transparent transparent;
}}

QComboBox QAbstractItemView {{
    background-color: {self.colors.card};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_base}px;
    selection-background-color: {self.colors.primary};
    outline: none;
}}

/* ==================== 进度条样式 ==================== */
QProgressBar {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_base}px;
    text-align: center;
    color: {self.colors.text_primary};
    font-weight: {self.typography.font_weight_medium};
    min-height: 20px;
}}

QProgressBar::chunk {{
    background-color: {self.colors.primary};
    border-radius: {self.spacing.border_radius_base - 1}px;
}}

/* ==================== 状态栏样式 ==================== */
QStatusBar {{
    background-color: {self.colors.surface};
    color: {self.colors.text_secondary};
    border-top: 1px solid {self.colors.border};
    padding: {self.spacing.xs}px {self.spacing.base}px;
}}

QStatusBar QLabel {{
    background-color: transparent;
    color: {self.colors.text_secondary};
    padding: {self.spacing.xs}px {self.spacing.sm}px;
}}

/* ==================== 对话框样式 ==================== */
QDialog {{
    background-color: {self.colors.background};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_lg}px;
}}

/* ==================== 标签样式 ==================== */
QLabel {{
    background-color: transparent;
    color: {self.colors.text_primary};
    font-weight: {self.typography.font_weight_normal};
}}

QLabel[class="title"] {{
    font-size: {self.typography.font_size_xl}px;
    font-weight: {self.typography.font_weight_bold};
    color: {self.colors.text_primary};
    padding: {self.spacing.base}px 0px;
}}

QLabel[class="subtitle"] {{
    font-size: {self.typography.font_size_lg}px;
    font-weight: {self.typography.font_weight_medium};
    color: {self.colors.text_secondary};
}}

QLabel[class="caption"] {{
    font-size: {self.typography.font_size_sm}px;
    color: {self.colors.text_secondary};
}}

/* ==================== 滚动条样式 ==================== */
QScrollBar:vertical {{
    background-color: {self.colors.surface};
    width: 12px;
    border-radius: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {self.colors.border};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {self.colors.text_secondary};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {self.colors.surface};
    height: 12px;
    border-radius: 6px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {self.colors.border};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {self.colors.text_secondary};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ==================== 特殊组件样式 ==================== */
/* 卡片容器 */
QWidget[class="card"] {{
    background-color: {self.colors.card};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_lg}px;
    padding: {self.spacing.base}px;
}}

/* 分隔线 */
QFrame[frameShape="4"] {{ /* HLine */
    color: {self.colors.border};
    background-color: {self.colors.border};
    max-height: 1px;
}}

QFrame[frameShape="5"] {{ /* VLine */
    color: {self.colors.border};
    background-color: {self.colors.border};
    max-width: 1px;
}}

/* 工具提示 */
QToolTip {{
    background-color: {self.colors.overlay};
    color: {self.colors.text_inverse};
    border: 1px solid {self.colors.border};
    border-radius: {self.spacing.border_radius_base}px;
    padding: {self.spacing.xs}px {self.spacing.sm}px;
    font-size: {self.typography.font_size_sm}px;
}}

/* ==================== 其他样式 ==================== */
/* QSS 不支持 CSS transition 属性，所以这里暂时注释掉 */
"""
    
    @classmethod
    def get_light_theme_stylesheet(cls) -> str:
        """获取明亮主题的样式表"""
        theme = LightTheme()
        stylesheet = cls(theme)
        return stylesheet.generate()
    
    @classmethod
    def get_button_style(cls, button_class: str = "primary") -> str:
        """
        获取特定按钮样式
        
        Args:
            button_class: 按钮类型 (primary, secondary, danger)
            
        Returns:
            按钮特定样式
        """
        theme = LightTheme()
        colors = theme.colors
        spacing = theme.spacing
        typography = theme.typography
        
        if button_class == "secondary":
            return f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {spacing.border_radius_base}px;
                padding: {spacing.sm}px {spacing.lg}px;
                font-weight: {typography.font_weight_medium};
                min-width: 80px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {colors.surface};
                border-color: {colors.primary};
                color: {colors.primary};
            }}
            """
        elif button_class == "danger":
            return f"""
            QPushButton {{
                background-color: {colors.error};
                color: {colors.text_inverse};
                border: 1px solid {colors.error};
                border-radius: {spacing.border_radius_base}px;
                padding: {spacing.sm}px {spacing.lg}px;
                font-weight: {typography.font_weight_medium};
                min-width: 80px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
                border-color: #b91c1c;
            }}
            """
        else:  # primary
            return f"""
            QPushButton {{
                background-color: {colors.primary};
                color: {colors.text_inverse};
                border: 1px solid {colors.primary};
                border-radius: {spacing.border_radius_base}px;
                padding: {spacing.sm}px {spacing.lg}px;
                font-weight: {typography.font_weight_medium};
                min-width: 80px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {colors.primary_hover};
                border-color: {colors.primary_hover};
            }}
            """