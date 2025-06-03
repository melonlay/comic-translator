"""
Text Translator
文字翻譯器

統一的翻譯介面，整合原子化模組，支援圖片失敗時的備用機制
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.gemini_client import GeminiClient
from .translation_flow import TranslationFlow


class TextTranslator:
    """
    文字翻譯器
    Text Translator
    
    統一的翻譯介面，整合所有翻譯相關功能
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化翻譯器
        
        Args:
            gemini_client: Gemini客戶端實例
        """
        self.gemini_client = gemini_client
        self.translation_flow = TranslationFlow(gemini_client)
        
        print("✅ 文字翻譯器初始化完成")
    
    def translate_texts_with_history(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None,
        image_path: str = None
    ) -> Dict[str, Any]:
        """
        翻譯文字列表（支援歷史上下文和圖片分析，具備備用機制）
        
        Args:
            texts: 待翻譯的文字列表
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            image_path: 圖片路徑（可選，若失敗會自動退回純文字模式）
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return {
                'translated_texts': [], 
                'new_terminology': {}, 
                'success': False,
                'error': 'No texts provided'
            }
        
        print(f"🌐 開始翻譯 {len(texts)} 個文字...")
        if image_path:
            print(f"📷 圖片路徑: {Path(image_path).name}")
        if translation_history:
            print(f"📚 使用 {len(translation_history)} 條歷史翻譯作為上下文")
        
        # 使用翻譯流程管理器進行翻譯，自動處理圖片失敗的備用機制
        result = self.translation_flow.translate_texts_with_fallback(
            texts=texts,
            image_path=image_path,
            terminology_dict=terminology_dict,
            translation_history=translation_history
        )
        
        if result.get('success', False):
            translated_texts = result.get('translated_texts', [])
            new_terminology = result.get('new_terminology', {})
            print(f"✅ 翻譯完成: {len(translated_texts)} 個文字")
            print(f"🆕 發現新專有名詞: {len(new_terminology)}")
        else:
            print(f"❌ 翻譯失敗: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """
        獲取翻譯統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        return self.translation_flow.get_statistics() 