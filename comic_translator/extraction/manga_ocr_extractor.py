"""
Manga OCR Extractor
漫畫OCR擷取器

使用manga-ocr進行日文文字擷取
"""

import cv2
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Union


class MangaOCRExtractor:
    """漫畫OCR擷取器"""
    
    def __init__(self):
        """初始化OCR擷取器"""
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.ocr_model = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化OCR模型"""
        try:
            import manga_ocr
            self.ocr_model = manga_ocr.MangaOcr()
            print(f"✅ Manga OCR初始化完成 (設備: {self.device})")
            
            if self.device == 'cuda':
                print(f"🚀 GPU: {torch.cuda.get_device_name()}")
                
        except Exception as e:
            print(f"❌ Manga OCR初始化失敗: {e}")
            raise
    
    def extract_from_region(self, image: Union[str, Image.Image], bbox: List[int]) -> str:
        """
        從指定區域擷取文字
        
        Args:
            image: 圖像路徑或PIL Image
            bbox: 文字框座標 [x, y, w, h]
            
        Returns:
            str: 擷取的文字
        """
        if self.ocr_model is None:
            raise RuntimeError("OCR模型未初始化")
        
        # 處理輸入圖像
        if isinstance(image, str):
            image_cv = cv2.imread(image)
            if image_cv is None:
                raise ValueError(f"無法讀取圖像: {image}")
        else:
            # 假設是PIL Image，轉換為opencv格式
            import numpy as np
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 裁切區域
        x, y, w, h = bbox
        region = image_cv[y:y+h, x:x+w]
        
        if region.size == 0:
            return ""
        
        # 轉換為PIL格式
        region_pil = Image.fromarray(cv2.cvtColor(region, cv2.COLOR_BGR2RGB))
        
        # OCR擷取
        try:
            text = self.ocr_model(region_pil)
            return text.strip() if text else ""
        except Exception as e:
            print(f"⚠️ OCR擷取失敗: {e}")
            return ""
    
    def extract_from_boxes(self, image_path: str, text_boxes: List[List[int]]) -> List[Dict]:
        """
        從多個文字框擷取文字
        
        Args:
            image_path: 圖像路徑
            text_boxes: 文字框座標列表
            
        Returns:
            List[Dict]: 擷取結果列表
        """
        if not text_boxes:
            return []
        
        # 讀取圖像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"無法讀取圖像: {image_path}")
        
        results = []
        successful_count = 0
        
        for i, bbox in enumerate(text_boxes):
            print(f"📖 處理文字框 {i+1}/{len(text_boxes)}")
            
            text = self.extract_from_region(image_path, bbox)
            
            if text:
                results.append({
                    'box_index': i,
                    'bbox': bbox,
                    'text': text,
                    'confidence': 0.9  # manga-ocr沒有提供置信度，使用固定值
                })
                successful_count += 1
                print(f"  ✅ '{text}'")
            else:
                print(f"  ⚠️ 未識別到文字")
        
        print(f"🎯 成功擷取 {successful_count}/{len(text_boxes)} 個文字框")
        return results
    
    def extract_single(self, image_path: str, bbox: List[int]) -> Dict:
        """
        單一文字框擷取
        
        Args:
            image_path: 圖像路徑
            bbox: 文字框座標 [x, y, w, h]
            
        Returns:
            Dict: 擷取結果
        """
        text = self.extract_from_region(image_path, bbox)
        
        return {
            'bbox': bbox,
            'text': text,
            'confidence': 0.9 if text else 0.0
        }
    
    def get_device_info(self) -> Dict:
        """
        獲取設備資訊
        
        Returns:
            Dict: 設備資訊
        """
        info = {
            'device': self.device,
            'cuda_available': torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name()
            info['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory
        
        return info 