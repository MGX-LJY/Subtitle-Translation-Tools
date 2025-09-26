# -*- coding: utf-8 -*-
"""
文件处理服务
"""

from pathlib import Path
from typing import List

from models import SubtitleCue
from utils import get_logger

logger = get_logger(__name__)


class FileService:
    """文件处理服务类"""
    
    @staticmethod
    def parse_srt(file_path: Path) -> List[SubtitleCue]:
        """
        解析 SRT 字幕文件
        
        Args:
            file_path: SRT 文件路径
            
        Returns:
            List[SubtitleCue]: 字幕条目列表
        """
        cues = []
        block = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line.strip():
                        block.append(line)
                    else:
                        if block:
                            FileService._parse_block_to_cue(block, cues)
                            block = []
                
                # 处理最后一个块
                if block:
                    FileService._parse_block_to_cue(block, cues)
            
            logger.info(f"成功解析 SRT 文件: {file_path}，共 {len(cues)} 条字幕")
            
        except Exception as e:
            logger.error(f"解析 SRT 文件失败: {e}")
            raise
        
        return cues
    
    @staticmethod
    def _parse_block_to_cue(block: List[str], cues: List[SubtitleCue]) -> None:
        """
        将文本块解析为字幕条目
        
        Args:
            block: 文本块列表
            cues: 字幕条目列表（用于添加解析结果）
        """
        if len(block) < 3:
            return
        
        try:
            # 解析序号
            index = int(block[0])
            
            # 解析时间轴
            time_line = block[1]
            if ' --> ' not in time_line:
                return
            
            start_time, end_time = time_line.split(' --> ', 1)
            
            # 解析字幕文本（可能有多行）
            original_text = '\n'.join(block[2:])
            
            cue = SubtitleCue(
                index=index,
                start=start_time.strip(),
                end=end_time.strip(),
                original=original_text
            )
            
            cues.append(cue)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"跳过无效的字幕块: {block}, 错误: {e}")
    
    @staticmethod
    def write_srt(file_path: Path, cues: List[SubtitleCue]) -> None:
        """
        写入 SRT 字幕文件
        
        Args:
            file_path: 输出文件路径
            cues: 字幕条目列表
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for cue in cues:
                    # 优先使用修复后文本，然后是翻译文本，最后是原文
                    text = cue.display_text
                    
                    f.write(f"{cue.index}\n")
                    f.write(f"{cue.start} --> {cue.end}\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"成功写入 SRT 文件: {file_path}，共 {len(cues)} 条字幕")
            
        except Exception as e:
            logger.error(f"写入 SRT 文件失败: {e}")
            raise
    
    @staticmethod
    def validate_srt_file(file_path: Path) -> bool:
        """
        验证 SRT 文件格式是否正确
        
        Args:
            file_path: SRT 文件路径
            
        Returns:
            bool: 文件格式是否有效
        """
        try:
            if not file_path.exists():
                return False
            
            if not file_path.suffix.lower() == '.srt':
                return False
            
            # 尝试解析文件
            cues = FileService.parse_srt(file_path)
            return len(cues) > 0
            
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 文件信息字典
        """
        try:
            stat = file_path.stat()
            cues = FileService.parse_srt(file_path)
            
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'subtitle_count': len(cues),
                'has_translation': sum(1 for c in cues if c.has_translation)
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {}