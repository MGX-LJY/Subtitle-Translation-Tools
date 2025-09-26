# -*- coding: utf-8 -*-
"""
OpenAI 翻译服务实现
"""

import asyncio
from typing import List, Tuple, Callable, Optional

from openai import AsyncOpenAI

from .translation_service import TranslationService, TranslationResult, TranslationProgress
from models import SubtitleCue, Config
from utils import get_logger, MAX_CONCURRENCY, REQUEST_TIMEOUT

logger = get_logger(__name__)


class OpenAIService(TranslationService):
    """OpenAI 翻译服务实现"""
    
    def __init__(self, config: Config):
        """
        初始化 OpenAI 翻译服务
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.client: Optional[AsyncOpenAI] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """获取 OpenAI 客户端"""
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.effective_base_url
            )
        return self.client
    
    def validate_config(self) -> List[str]:
        """
        验证配置是否有效
        
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        if not self.config.api_key.strip():
            errors.append("OpenAI API Key 不能为空")
        
        if not self.config.model.strip():
            errors.append("模型名称不能为空")
        
        return errors
    
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
        try:
            client = self._get_client()
            
            if mode == "translate":
                prompt = self.get_translate_prompt().format(lang=self.config.target_lang)
            else:
                prompt = self.get_fix_prompt()
            
            # 处理特殊情况：如果是修复模式且文本包含问题标记，改用翻译模式
            if mode == "fix" and any(bad in text for bad in ("无法翻译", "【违规内容")):
                fallback_prompt = (
                    self.get_translate_prompt().format(lang=self.config.target_lang)
                    + "\n【额外指令】请保持直译风格，避免润色和主观扩写；"
                      "若出现敏感内容请用 ♪♪ 占位。"
                )
                prompt = fallback_prompt
            
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                timeout=REQUEST_TIMEOUT
            )
            
            translated_text, prompt_tokens, completion_tokens = self._extract_response(response)
            
            return TranslationResult(
                index=0,  # 将由调用者设置
                success=True,
                translated_text=translated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
        except Exception as e:
            logger.error(f"翻译文本失败: {e}")
            return TranslationResult(
                index=0,
                success=False,
                error_message=str(e)
            )
    
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
        results = []
        total = len(cues)
        completed = 0
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        
        async def translate_single(index: int, cue: SubtitleCue) -> TranslationResult:
            """翻译单个字幕条目"""
            async with semaphore:
                try:
                    # 确定翻译文本
                    if mode == "translate":
                        source_text = cue.original
                    else:
                        source_text = cue.translation or cue.original
                    
                    # 发送进度更新
                    if progress_callback:
                        progress = TranslationProgress(
                            completed=completed,
                            total=total,
                            current_index=index,
                            current_text=source_text[:50] + "..." if len(source_text) > 50 else source_text
                        )
                        progress_callback(progress)
                    
                    # 执行翻译
                    result = await self.translate_text(source_text, mode)
                    result.index = index
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"翻译字幕 {index} 失败: {e}")
                    return TranslationResult(
                        index=index,
                        success=False,
                        error_message=str(e)
                    )
        
        # 创建所有翻译任务
        tasks = [translate_single(i, cue) for i, cue in enumerate(cues)]
        
        # 使用 as_completed 确保结果按完成顺序处理
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
                completed += 1
                
                # 调用结果回调
                if result_callback:
                    result_callback(result)
                
                # 发送最终进度更新
                if progress_callback:
                    progress = TranslationProgress(
                        completed=completed,
                        total=total,
                        current_index=result.index,
                        current_text=""
                    )
                    progress_callback(progress)
                
            except Exception as e:
                logger.error(f"处理翻译结果失败: {e}")
        
        # 按索引排序结果
        results.sort(key=lambda x: x.index)
        
        logger.info(f"批量翻译完成，共处理 {len(results)} 条字幕")
        return results
    
    @staticmethod
    def _extract_response(response) -> Tuple[str, int, int]:
        """
        统一解析不同 SDK / 网关返回
        
        Args:
            response: API 响应对象
            
        Returns:
            Tuple[str, int, int]: (翻译文本, prompt_tokens, completion_tokens)
        """
        try:
            if hasattr(response, "choices"):
                content = response.choices[0].message.content or ""
                return (
                    content.strip(), 
                    response.usage.prompt_tokens, 
                    response.usage.completion_tokens
                )
            
            if isinstance(response, dict) and "choices" in response:
                usage = response.get("usage", {})
                message = response["choices"][0].get("message", {})
                content = (message.get("content") if isinstance(message, dict) else message) or ""
                return (
                    content.strip(), 
                    usage.get("prompt_tokens", 0), 
                    usage.get("completion_tokens", 0)
                )
            
            # 兜底处理
            text = str(response or "").strip()
            if text.lower().startswith("<!doctype") or "<html" in text.lower():
                raise ValueError("收到 HTML — base_url 或 Token 可能配置错误")
            
            return text, 0, 0
            
        except Exception as e:
            logger.error(f"解析 API 响应失败: {e}")
            raise
    
    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.close()
            self.client = None