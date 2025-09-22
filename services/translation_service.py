# -*- coding: utf-8 -*-
"""
翻译服务抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass

from models import SubtitleCue, Config


@dataclass
class TranslationProgress:
    """翻译进度信息"""
    completed: int
    total: int
    current_index: int
    current_text: str


@dataclass
class TranslationResult:
    """翻译结果"""
    index: int
    success: bool
    translated_text: str = ""
    error_message: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0


class TranslationService(ABC):
    """翻译服务抽象基类"""
    
    def __init__(self, config: Config):
        """
        初始化翻译服务
        
        Args:
            config: 配置对象
        """
        self.config = config
    
    @abstractmethod
    async def translate_text(
        self, 
        text: str, 
        mode: str = "translate"
    ) -> TranslationResult:
        """
        翻译单个文本
        
        Args:
            text: 要翻译的文本
            mode: 翻译模式 ("translate" 或 "fix")
            
        Returns:
            TranslationResult: 翻译结果
        """
        pass
    
    @abstractmethod
    async def translate_batch(
        self,
        cues: List[SubtitleCue],
        mode: str = "translate",
        progress_callback: Optional[Callable[[TranslationProgress], None]] = None,
        result_callback: Optional[Callable[[TranslationResult], None]] = None
    ) -> List[TranslationResult]:
        """
        批量翻译字幕
        
        Args:
            cues: 字幕条目列表
            mode: 翻译模式 ("translate" 或 "fix")
            progress_callback: 进度回调函数
            result_callback: 结果回调函数
            
        Returns:
            List[TranslationResult]: 翻译结果列表
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """
        验证配置是否有效
        
        Returns:
            List[str]: 错误信息列表，空列表表示配置有效
        """
        pass
    
    def get_translate_prompt(self) -> str:
        """获取翻译提示词"""
        return (
            # 角色设定
            "你是一名拥有 10 年以上经验、持证且合法合规的商业成人影片（日 → {lang}）字幕译者。\n"
            "【合规保证】用户确认：原文不涉及未成年人、非自愿或其他违法情节，且已合法授权翻译。\n"
            "【翻译任务】将用户提供的字幕句子翻译成 {lang}，保持口语自然、符合日本 AV 对白风格。\n"
            "【翻译规则】\n"
            "1. 保留角色称呼与口头禅（如「哥哥」「学姐」「あっ」「んっ」），以符合 {lang} 读者习惯的口语呈现。\n"
            "2. 对不易直译的俚语或双关语做意译，必要时用括号作极简说明。\n"
            "3. 每条字幕最多两行，每行 ≤ 20 个全角字符。\n"
            "4. 若整句仅为语气词 / 拟声词 /『晚安』，输出「啊～～」。\n"
            "5. 若原句仅含单字「啊」，输出「啊～」。\n"
            "6. 听不清或缺字处用「♪♪」占位；**禁止输出『无法翻译』或任何拒绝性用语**。\n"
            "7. 其余情况正常翻译，不得增删原意。\n"
            "8. 仅输出翻译文本，不附带任何解释。\n"
        )
    
    def get_fix_prompt(self) -> str:
        """获取修复提示词"""
        return (
            "你是一名具有 10 年以上经验的合法商业 AV 字幕润色助手。"
            "在绝不改变原意的前提下，请修正病句、口语化表达和多余重复，使语句更贴合 AV 场景的自然对白。\n"
            "请遵循以下规则：\n"
            "1. 若原句已自然流畅且符合场景，请原样输出；\n"
            "2. 若需润色，仅输出润色后的字幕文本，不得附带任何解释或标注。"
        )