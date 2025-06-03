"""
Translation Flow
翻譯流程管理器

負責管理翻譯流程，包括圖片失敗時的備用機制
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.gemini_client import GeminiClient
from .translation_core import TranslationCore


class TranslationFlow:
    """
    翻譯流程管理器
    Translation Flow Manager
    
    負責管理整體翻譯流程，處理圖片調用失敗時的備用機制
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化翻譯流程管理器
        
        Args:
            gemini_client: Gemini客戶端實例
        """
        self.gemini_client = gemini_client
        self.translation_core = TranslationCore(gemini_client)
        
        print("✅ 翻譯流程管理器初始化完成")
    
    def translate_texts_with_fallback(
        self, 
        texts: List[str], 
        image_path: str = None,
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        翻譯文字，如果圖片調用失敗則自動切換到純文字模式
        
        Args:
            texts: 待翻譯的文字列表
            image_path: 圖片路徑（可選）
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return self._create_empty_result()
        
        # 如果提供了圖片路徑，先嘗試圖片輔助翻譯
        if image_path and Path(image_path).exists():
            try:
                print("🎯 嘗試圖片輔助翻譯...")
                result = self.translation_core.translate_with_image(
                    texts, image_path, terminology_dict, translation_history
                )
                
                # 如果成功，直接返回結果
                if result.get('success', False):
                    return result
                
                # 如果失敗但不是因為API調用問題，直接返回失敗結果
                error_msg = result.get('error', '')
                if not self._is_api_failure(error_msg):
                    return result
                
                print("⚠️ 圖片調用可能被過濾，嘗試純文字翻譯...")
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ 圖片輔助翻譯失敗: {error_msg}")
                
                # 如果不是API調用相關的錯誤，重新拋出異常
                if not self._is_api_failure(error_msg):
                    raise
                
                print("🔄 切換到純文字翻譯模式...")
        
        # 執行純文字翻譯
        try:
            print("📝 執行純文字翻譯...")
            result = self.translation_core.translate_text_only(
                texts, terminology_dict, translation_history
            )
            
            # 如果純文字翻譯也失敗，返回備用結果
            if not result.get('success', False):
                print("❌ 純文字翻譯也失敗，使用備用翻譯")
                return {
                    'translated_texts': self._create_fallback_translations(texts),
                    'new_terminology': {},
                    'success': False,
                    'error': f"Both image and text-only translation failed: {result.get('error', 'Unknown error')}"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ 純文字翻譯失敗: {e}")
            return {
                'translated_texts': self._create_fallback_translations(texts),
                'new_terminology': {},
                'success': False,
                'error': f"All translation methods failed: {str(e)}"
            }
    
    def _is_api_failure(self, error_msg: str) -> bool:
        """
        判斷是否為API調用失敗（例如內容過濾）
        
        Args:
            error_msg: 錯誤訊息
            
        Returns:
            bool: 是否為API調用失敗
        """
        # 檢查常見的API失敗訊息
        api_failure_indicators = [
            "API回應為空",
            "Empty API response",
            "API response is empty",
            "content filter",
            "blocked",
            "filtered",
            "safety",
            "policy violation",
            "inappropriate content"
        ]
        
        error_lower = error_msg.lower()
        for indicator in api_failure_indicators:
            if indicator.lower() in error_lower:
                return True
        
        return False
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        創建空結果
        
        Returns:
            Dict: 空的翻譯結果
        """
        return {
            'translated_texts': [],
            'new_terminology': {},
            'success': False,
            'error': 'No texts to translate'
        }
    
    def _create_fallback_translations(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        創建備用翻譯結果
        
        Args:
            texts: 原始文字列表
            
        Returns:
            List[Dict]: 備用翻譯結果
        """
        return [
            {
                'original': text,
                'translated': text,
                'text_direction': 'horizontal',
                'bubble_type': 'pure_white',
                'estimated_font_size': 16
            }
            for text in texts
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取翻譯統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        return self.translation_core.get_statistics() 