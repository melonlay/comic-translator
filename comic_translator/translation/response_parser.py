"""
Response Parser
回應解析器

負責解析Gemini API回應的原子化模組
"""

from typing import List, Dict, Any
import json


class ResponseParser:
    """
    回應解析器
    Response Parser
    
    負責解析和驗證翻譯API的回應結果
    """
    
    def __init__(self):
        """初始化回應解析器"""
        pass
    
    def parse_structured_response(
        self, 
        response_data: Dict[str, Any], 
        expected_count: int
    ) -> Dict[str, Any]:
        """
        解析結構化翻譯回應
        
        Args:
            response_data: API回應數據
            expected_count: 期望的翻譯數量
            
        Returns:
            Dict: 解析後的結果
        """
        try:
            translations = response_data.get('translations', [])
            new_terminology = response_data.get('new_terminology', [])
            
            # 將new_terminology從array轉換為dict格式
            terminology_dict = {}
            for term in new_terminology:
                if isinstance(term, dict) and 'japanese' in term and 'chinese' in term:
                    terminology_dict[term['japanese']] = term['chinese']
            
            # 轉換為標準格式
            translated_texts = []
            for translation in translations:
                translated_texts.append({
                    'original': translation.get('original', ''),
                    'translated': translation.get('translated', ''),
                    'text_direction': translation.get('text_direction', 'horizontal'),
                    'bubble_type': translation.get('bubble_type', 'pure_white'),
                    'estimated_font_size': translation.get('estimated_font_size', 16)
                })
            
            # 驗證輸出數量
            if len(translated_texts) != expected_count:
                print(f"⚠️ 翻譯數量不匹配: 期望 {expected_count} 個，實際 {len(translated_texts)} 個")
                return {
                    'translated_texts': translated_texts,
                    'new_terminology': terminology_dict,
                    'success': False,
                    'error': f'Translation count mismatch: expected {expected_count}, got {len(translated_texts)}'
                }
            
            return {
                'translated_texts': translated_texts,
                'new_terminology': terminology_dict,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ 結構化回應解析失敗: {e}")
            return {
                'translated_texts': [],
                'new_terminology': {},
                'success': False,
                'error': str(e)
            }
    
    def create_fallback_translations(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        創建備用翻譯結果（當翻譯失敗時使用）
        
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
    
    def validate_translation_result(
        self, 
        result: Dict[str, Any], 
        expected_count: int
    ) -> bool:
        """
        驗證翻譯結果的完整性
        
        Args:
            result: 翻譯結果
            expected_count: 期望的翻譯數量
            
        Returns:
            bool: 是否有效
        """
        if not result or not result.get('success', False):
            return False
        
        translated_texts = result.get('translated_texts', [])
        if len(translated_texts) != expected_count:
            return False
        
        # 檢查每個翻譯項目的必要欄位
        for item in translated_texts:
            if not isinstance(item, dict):
                return False
            
            required_fields = ['original', 'translated', 'text_direction', 'bubble_type', 'estimated_font_size']
            for field in required_fields:
                if field not in item:
                    return False
        
        return True 