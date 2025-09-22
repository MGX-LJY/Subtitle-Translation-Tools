# -*- coding: utf-8 -*-
"""
配置数据模型
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """应用配置数据模型"""
    api_key: str = ""               # OpenAI API 密钥
    base_url: str = ""              # API 基础 URL
    model: str = "gpt-4o-mini"      # GPT 模型名称
    target_lang: str = "中文"       # 目标语言
    
    @property
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return bool(self.api_key.strip())
    
    @property
    def effective_base_url(self) -> Optional[str]:
        """获取有效的 base_url"""
        return self.base_url.strip() or None
    
    def validate(self) -> list[str]:
        """验证配置并返回错误信息列表"""
        errors = []
        
        if not self.api_key.strip():
            errors.append("API Key 不能为空")
        
        if self.base_url and not self.base_url.strip().startswith(('http://', 'https://')):
            errors.append("Base URL 必须以 http:// 或 https:// 开头")
        
        if not self.model.strip():
            errors.append("模型名称不能为空")
        
        if not self.target_lang.strip():
            errors.append("目标语言不能为空")
        
        return errors