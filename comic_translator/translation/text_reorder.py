"""
Text Reorder
文字重排序器

使用Gemini重新排序漫畫文字，支援structured output和圖片處理
"""

import json
from typing import List, Dict, Any
from ..utils.gemini_client import GeminiClient


class TextReorder:
    """文字重排序器"""
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化重排序器
        
        Args:
            gemini_client: Gemini客戶端
        """
        self.gemini_client = gemini_client
    
    def reorder_texts_with_image(self, image_path: str, extracted_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用圖片重新排序文字（新方法，使用structured output）
        
        Args:
            image_path: 圖片檔案路徑
            extracted_texts: 擷取的文字列表
            
        Returns:
            List[Dict]: 重排序後的文字列表
        """
        if not extracted_texts:
            return []
        
        # 準備文字資訊
        texts_for_reorder = []
        for item in extracted_texts:
            texts_for_reorder.append({
                'index': item['box_index'],
                'bbox': item['bbox'],
                'text': item['text']
            })
        
        # 定義JSON schema
        response_schema = {
            "type": "object",
            "properties": {
                "reordered_texts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "original_index": {"type": "integer"},
                            "new_order": {"type": "integer"},
                            "bbox": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "minItems": 4,
                                "maxItems": 4
                            },
                            "text": {"type": "string"}
                        },
                        "required": ["original_index", "new_order", "bbox", "text"],
                        "propertyOrdering": ["original_index", "new_order", "bbox", "text"]
                    }
                }
            },
            "required": ["reordered_texts"],
            "propertyOrdering": ["reordered_texts"]
        }
        
        # 準備提示詞
        prompt = self._create_reorder_prompt_with_image(texts_for_reorder)
        
        try:
            # 呼叫Gemini（使用structured output和圖片）
            result = self.gemini_client.generate_structured_content_with_image(
                prompt, image_path, response_schema
            )
            
            reordered_texts = result['reordered_texts']
            print(f"✅ Gemini重排序完成: {len(reordered_texts)} 個文字")
            
            return reordered_texts
            
        except Exception as e:
            print(f"⚠️ Gemini重排序失敗，使用原始順序: {e}")
            
            # 回退到原始順序
            return self._fallback_order(extracted_texts)
    
    def reorder_texts(self, extracted_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重新排序文字（舊方法，為了兼容性保留）
        
        Args:
            extracted_texts: 擷取的文字列表
            
        Returns:
            List[Dict]: 重排序後的文字列表
        """
        if not extracted_texts:
            return []
        
        # 準備Gemini提示詞
        texts_for_reorder = []
        for item in extracted_texts:
            texts_for_reorder.append({
                'index': item['box_index'],
                'bbox': item['bbox'],
                'text': item['text']
            })
        
        prompt = self._create_reorder_prompt(texts_for_reorder)
        
        try:
            # 呼叫Gemini
            gemini_result, raw_response = self.gemini_client.generate_json(prompt)
            reordered_texts = gemini_result['reordered_texts']
            
            print(f"✅ Gemini重排序完成: {len(reordered_texts)} 個文字")
            
            return reordered_texts
            
        except Exception as e:
            print(f"⚠️ Gemini重排序失敗，使用原始順序: {e}")
            
            # 回退到原始順序
            return self._fallback_order(extracted_texts)
    
    def _create_reorder_prompt_with_image(self, texts_for_reorder: List[Dict[str, Any]]) -> str:
        """
        創建包含圖片的重排序提示詞
        
        Args:
            texts_for_reorder: 需要重排序的文字
            
        Returns:
            str: Gemini提示詞
        """
        return f"""你是一個專業的日文漫畫文字排序專家。請觀察這張漫畫圖片，並將以下檢測到的文字按照正確的日文漫畫閱讀順序重新排序。

重要規則：
1. 日文漫畫的閱讀順序是從右到左，從上到下
2. 請直接觀察圖片中文字框的實際位置關係
3. 對話氣泡通常按照故事時間順序排列
4. 同一水平線上的對話氣泡，右邊的優先於左邊的
5. 上方的對話氣泡優先於下方的
6. 請考慮對話的邏輯流程和角色對話的自然順序

檢測到的文字和位置信息（bbox格式為[x, y, width, height]）：
{json.dumps(texts_for_reorder, ensure_ascii=False, indent=2)}

請根據圖片中的實際文字位置，按照日文漫畫的閱讀習慣重新排序這些文字。
輸出格式必須是JSON，包含reordered_texts陣列，每個元素包含original_index、new_order（從0開始）、bbox和text。"""
    
    def _create_reorder_prompt(self, texts_for_reorder: List[Dict[str, Any]]) -> str:
        """
        創建重排序提示詞
        
        Args:
            texts_for_reorder: 需要重排序的文字
            
        Returns:
            str: Gemini提示詞
        """
        return f"""你是一個專業的日文漫畫文字排序專家。請將以下日文對話文字按照正確的漫畫閱讀順序重新排序。

重要規則：
1. 日文漫畫的閱讀順序是從右到左，從上到下
2. 對話氣泡通常按照故事時間順序排列
3. 同一水平線上的對話氣泡，右邊的優先於左邊的
4. 上方的對話氣泡優先於下方的
5. bbox格式為[x, y, width, height]，其中(x,y)是左上角座標

待排序的文字和位置信息：
{json.dumps(texts_for_reorder, ensure_ascii=False, indent=2)}

請分析每個文字框的位置關係，按照日文漫畫的閱讀習慣重新排序。

返回格式（只返回JSON，不要其他說明）：
{{"reordered_texts": [{{"original_index": 原始索引, "new_order": 新排序號(從0開始), "bbox": [x,y,w,h], "text": "原始文字"}}]}}"""
    
    def _fallback_order(self, extracted_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        回退排序（當Gemini失敗時使用）
        
        Args:
            extracted_texts: 原始文字列表
            
        Returns:
            List[Dict]: 回退排序結果
        """
        reordered_texts = []
        for i, item in enumerate(extracted_texts):
            reordered_texts.append({
                'original_index': item['box_index'],
                'new_order': i,
                'bbox': item['bbox'],
                'text': item['text']
            })
        
        return reordered_texts
    
    def reorder_with_metadata(self, extracted_texts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        重排序並返回詳細資訊
        
        Args:
            extracted_texts: 擷取的文字列表
            
        Returns:
            Dict: 包含重排序結果和元數據
        """
        reordered_texts = self.reorder_texts(extracted_texts)
        
        return {
            'total_texts': len(extracted_texts),
            'reordered_count': len(reordered_texts),
            'reordered_texts': reordered_texts,
            'success': len(reordered_texts) > 0
        } 