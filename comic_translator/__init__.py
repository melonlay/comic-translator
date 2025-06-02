"""
Comic Translator
漫畫翻譯器

一個專業的漫畫翻譯系統，支援5階段翻譯流程
"""

# 核心模組
from .core.five_stage_pipeline import FiveStagePipeline

# 各功能模組
from .detection import ComicTextDetector
from .extraction import MangaOCRExtractor  
from .translation import TextReorder, TextTranslator
from .terminology import TerminologyManager
from .rendering import TextOverlay
from .utils import GeminiClient, StageManager

__version__ = "1.0.0"
__author__ = "Professional Python Engineer"

__all__ = [
    'FiveStagePipeline',
    'ComicTextDetector', 
    'MangaOCRExtractor',
    'TextReorder',
    'TextTranslator',
    'TerminologyManager',
    'TextOverlay',
    'GeminiClient',
    'StageManager'
] 