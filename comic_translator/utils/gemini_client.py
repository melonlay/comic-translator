"""
Gemini API Client
Gemini API客戶端

封裝Google Generative AI的API呼叫，使用正確的google.genai庫，支援structured output和圖片處理
"""

import os
import json
from typing import Dict, Tuple, Any, Optional
from pathlib import Path
from PIL import Image


class GeminiClient:
    """Gemini API客戶端"""
    
    def __init__(self, api_key: str = None, model_name: str = 'models/gemini-2.0-flash'):
        """
        初始化Gemini客戶端
        #gemini-2.5-flash-preview-05-20
        Args:
            api_key: API密鑰，如果未提供則從環境變數獲取
            model_name: 模型名稱（使用正確的models/gemini-2.5-flash-preview-05-20）
        """
        self.api_key = api_key or os.getenv('genaikey')
        self.model_name = model_name
        self.model = None
        self.genai = None
        self.types = None
        
        if not self.api_key:
            raise ValueError("需要Gemini API Key! 請設定環境變數genaikey或傳入api_key參數")
        
        self._init_client()
    
    def _init_client(self):
        """初始化Gemini客戶端，使用正確的google.genai庫"""
        try:
            import google.genai as genai
            from google.genai import types
            
            # 配置API密鑰
            client = genai.Client(api_key=self.api_key)
            self.genai = client
            self.types = types
            
            print(f"✅ Gemini客戶端初始化完成 ({self.model_name})")
            
        except ImportError as e:
            print(f"❌ 無法匯入google.genai: {e}")
            print("請安裝: pip install google-genai")
            raise
        except Exception as e:
            print(f"❌ Gemini客戶端初始化失敗: {e}")
            raise
    
    def generate_content(self, prompt: str) -> str:
        """
        生成內容
        
        Args:
            prompt: 提示詞
            
        Returns:
            str: 生成的內容
        """
        if self.genai is None:
            raise RuntimeError("Gemini客戶端未初始化")
        
        try:
            response = self.genai.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            if response and response.text:
                return response.text
            else:
                raise RuntimeError("API回應為空")
                
        except Exception as e:
            print(f"❌ Gemini API呼叫失敗: {e}")
            raise
    
    def generate_content_with_image(self, prompt: str, image_path: str) -> str:
        """
        使用圖片生成內容
        
        Args:
            prompt: 提示詞
            image_path: 圖片檔案路徑
            
        Returns:
            str: 生成的內容
        """
        if self.genai is None:
            raise RuntimeError("Gemini客戶端未初始化")
        
        try:
            # 讀取圖片檔案
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
            
            # 使用PIL打開圖片
            img = Image.open(str(image_path))
            
            # 準備contents
            contents = [prompt, img]
            
            response = self.genai.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            
            if response and response.text:
                return response.text
            else:
                raise RuntimeError("API回應為空")
                
        except Exception as e:
            print(f"❌ Gemini API圖片呼叫失敗: {e}")
            raise
    
    def generate_structured_content(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成結構化內容（JSON）
        
        Args:
            prompt: 提示詞
            response_schema: 回應結構定義
            
        Returns:
            Dict: 結構化回應
        """
        if self.genai is None:
            raise RuntimeError("Gemini客戶端未初始化")
        
        try:
            response = self.genai.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                }
            )
            
            if response and response.text:
                return json.loads(response.text)
            else:
                raise RuntimeError("API回應為空")
                
        except Exception as e:
            print(f"❌ Gemini API結構化呼叫失敗: {e}")
            raise
    
    def generate_structured_content_with_image(self, prompt: str, image_path: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用圖片生成結構化內容（JSON）
        
        Args:
            prompt: 提示詞
            image_path: 圖片檔案路徑
            response_schema: 回應結構定義
            
        Returns:
            Dict: 結構化回應
        """
        if self.genai is None:
            raise RuntimeError("Gemini客戶端未初始化")
        
        try:
            # 讀取圖片檔案
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
            
            # 使用PIL打開圖片
            img = Image.open(str(image_path))
            
            # 準備contents
            contents = [prompt, img]
            
            response = self.genai.models.generate_content(
                model=self.model_name,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                }
            )
            
            if response and response.text:
                return json.loads(response.text)
            else:
                raise RuntimeError("API回應為空")
                
        except Exception as e:
            print(f"❌ Gemini API結構化圖片呼叫失敗: {e}")
            raise
    
    def generate_json(self, prompt: str) -> Tuple[Dict[str, Any], str]:
        """
        生成JSON格式內容（舊方法，為了兼容性保留）
        
        Args:
            prompt: 提示詞
            
        Returns:
            Tuple[Dict, str]: 解析後的JSON和原始回應
        """
        raw_response = self.generate_content(prompt)
        
        # 清理回應文字
        response_text = raw_response.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            parsed_json = json.loads(response_text)
            return parsed_json, raw_response
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失敗: {e}")
            print(f"原始回應: {raw_response}")
            raise
    
    def list_models(self) -> list:
        """
        列出可用的模型
        
        Returns:
            list: 可用模型列表
        """
        if self.genai is None:
            raise RuntimeError("Gemini客戶端未初始化")
        
        try:
            models = self.genai.models.list()
            return [model.name for model in models]
        except Exception as e:
            print(f"❌ 無法列出模型: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, str]:
        """
        獲取模型資訊
        
        Returns:
            Dict: 模型資訊
        """
        return {
            'model_name': self.model_name,
            'api_key_set': bool(self.api_key),
            'initialized': self.genai is not None
        } 