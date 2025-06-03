"""
Translation Core
翻譯核心

負責執行具體翻譯邏輯的原子化模組
"""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.gemini_client import GeminiClient
from .prompt_manager import PromptManager
from .response_parser import ResponseParser


class TranslationCore:
    """
    翻譯核心
    Translation Core
    
    負責執行具體的翻譯操作
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化翻譯核心
        
        Args:
            gemini_client: Gemini客戶端實例
        """
        self.gemini_client = gemini_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        self.api_call_count = 0
        
        print("✅ 翻譯核心初始化完成")
    
    def translate_with_image(
        self, 
        texts: List[str], 
        image_path: str,
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        使用圖片進行翻譯（包含OCR校正和視覺分析）
        
        Args:
            texts: 待翻譯的文字列表
            image_path: 圖片路徑
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return self._create_empty_result()
        
        if not image_path or not Path(image_path).exists():
            raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
        
        print(f"🌐 開始圖片輔助翻譯 {len(texts)} 個文字...")
        print(f"📷 使用圖片分析: {Path(image_path).name}")
        
        start_time = time.time()
        
        try:
            # 生成提示詞
            prompt = self.prompt_manager.create_visual_translation_prompt(
                texts, terminology_dict, translation_history
            )
            
            # 獲取回應schema
            response_schema = self.prompt_manager.get_response_schema()
            
            # 呼叫Gemini API
            self.api_call_count += 1
            print(f"💰 API 呼叫 #{self.api_call_count} - 模型: {self.gemini_client.model_name}")
            
            response_data = self.gemini_client.generate_structured_content_with_image(
                prompt, image_path, response_schema
            )
            
            print("✅ 使用圖片視覺分析進行翻譯")
            
            # 解析回應
            result = self.response_parser.parse_structured_response(response_data, len(texts))
            
            processing_time = time.time() - start_time
            
            if result['success']:
                print(f"✅ 翻譯完成，耗時: {processing_time:.2f}秒")
                print(f"📝 成功翻譯: {len(result['translated_texts'])}/{len(texts)}")
                print(f"🆕 發現新專有名詞: {len(result['new_terminology'])}")
            
            return result
            
        except Exception as e:
            print(f"❌ 圖片輔助翻譯失敗: {e}")
            return {
                'translated_texts': self.response_parser.create_fallback_translations(texts),
                'new_terminology': {},
                'success': False,
                'error': str(e)
            }
    
    def translate_text_only(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        純文字翻譯（不使用圖片）
        
        Args:
            texts: 待翻譯的文字列表
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return self._create_empty_result()
        
        print(f"📝 開始純文字翻譯 {len(texts)} 個文字...")
        
        start_time = time.time()
        
        try:
            # 生成提示詞
            prompt = self.prompt_manager.create_text_only_translation_prompt(
                texts, terminology_dict, translation_history
            )
            
            # 獲取回應schema
            response_schema = self.prompt_manager.get_response_schema()
            
            # 呼叫Gemini API
            self.api_call_count += 1
            print(f"💰 API 呼叫 #{self.api_call_count} - 模型: {self.gemini_client.model_name}")
            
            response_data = self.gemini_client.generate_structured_content(
                prompt, response_schema
            )
            
            print("✅ 純文字翻譯完成")
            
            # 解析回應
            result = self.response_parser.parse_structured_response(response_data, len(texts))
            
            processing_time = time.time() - start_time
            
            if result['success']:
                print(f"✅ 翻譯完成，耗時: {processing_time:.2f}秒")
                print(f"📝 成功翻譯: {len(result['translated_texts'])}/{len(texts)}")
                print(f"🆕 發現新專有名詞: {len(result['new_terminology'])}")
            
            return result
            
        except Exception as e:
            print(f"❌ 純文字翻譯失敗: {e}")
            return {
                'translated_texts': self.response_parser.create_fallback_translations(texts),
                'new_terminology': {},
                'success': False,
                'error': str(e)
            }
    
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取翻譯統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        return {
            'total_api_calls': self.api_call_count,
            'model_used': self.gemini_client.model_name,
            'client_initialized': self.gemini_client.genai is not None
        } 