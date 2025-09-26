# -*- coding: utf-8 -*-
"""
配置管理服务
"""

import json
from pathlib import Path
from typing import Optional

from models import Config
from utils import get_logger, CONFIG_FILENAME

logger = get_logger(__name__)


class ConfigService:
    """配置管理服务类"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置服务
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的 main.config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / CONFIG_FILENAME
        self.config_path = config_path
    
    def load_config(self) -> Config:
        """
        加载配置文件
        
        Returns:
            Config: 配置对象
        """
        config = Config()
        
        if not self.config_path.exists():
            logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
            return config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config.api_key = data.get("api_key", "")
            config.base_url = data.get("base_url", "")
            config.model = data.get("model", config.model)
            config.target_lang = data.get("target_lang", config.target_lang)
            
            logger.info(f"配置已从 {self.config_path} 加载")
            
        except Exception as e:
            logger.warning(f"读取配置失败: {e}")
        
        return config
    
    def save_config(self, config: Config) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 验证配置
            errors = config.validate()
            if errors:
                logger.error(f"配置验证失败: {', '.join(errors)}")
                return False
            
            data = {
                "api_key": config.api_key,
                "base_url": config.base_url,
                "model": config.model,
                "target_lang": config.target_lang,
            }
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到 {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"写入配置失败: {e}")
            return False
    
    def backup_config(self) -> bool:
        """
        备份当前配置文件
        
        Returns:
            bool: 备份是否成功
        """
        if not self.config_path.exists():
            logger.warning("配置文件不存在，无法备份")
            return False
        
        try:
            backup_path = self.config_path.with_suffix('.backup.json')
            backup_path.write_bytes(self.config_path.read_bytes())
            logger.info(f"配置已备份到 {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"备份配置失败: {e}")
            return False
    
    def restore_config(self) -> bool:
        """
        从备份恢复配置文件
        
        Returns:
            bool: 恢复是否成功
        """
        backup_path = self.config_path.with_suffix('.backup.json')
        
        if not backup_path.exists():
            logger.warning("备份文件不存在，无法恢复")
            return False
        
        try:
            self.config_path.write_bytes(backup_path.read_bytes())
            logger.info(f"配置已从 {backup_path} 恢复")
            return True
            
        except Exception as e:
            logger.error(f"恢复配置失败: {e}")
            return False