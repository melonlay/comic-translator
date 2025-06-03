"""
Region Extractor
區域提取器

專門負責從圖像中提取指定區域的功能
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple
from .rotation_corrector import RotationCorrector
from .debug_saver import DebugSaver


class RegionExtractor:
    """區域提取器"""
    
    def __init__(self, rotation_corrector: RotationCorrector, debug_saver: DebugSaver):
        """
        初始化區域提取器
        
        Args:
            rotation_corrector: 旋轉校正器
            debug_saver: 調試保存器
        """
        self.rotation_corrector = rotation_corrector
        self.debug_saver = debug_saver
    
    def extract_region(self, image_path: str, bbox: List[int], block_index: int = 0, 
                      angle: float = 0.0, xyxy: List[int] = None) -> Dict:
        """
        從圖片的指定區域提取文字區域
        
        Args:
            image_path: 圖片路徑
            bbox: 邊界框 [x, y, w, h]
            block_index: 文字塊索引（用於debug文件命名）
            angle: 旋轉角度（度）
            xyxy: 精確的xyxy格式邊界框 [x1, y1, x2, y2]，優先使用
            
        Returns:
            Dict: 包含提取結果的字典
        """
        try:
            # 讀取圖片
            image_cv = cv2.imread(image_path)
            if image_cv is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            # 優先使用xyxy格式進行精確切割
            if xyxy is not None:
                x1, y1, x2, y2 = xyxy
                # 保存原始座標用於debug（不做邊界檢查）
                original_x1, original_y1, original_x2, original_y2 = x1, y1, x2, y2
                
                # 只在實際切割時做邊界檢查
                height, width = image_cv.shape[:2]
                x1 = max(0, min(x1, width-1))
                y1 = max(0, min(y1, height-1))
                x2 = max(x1+1, min(x2, width))
                y2 = max(y1+1, min(y2, height))
                
                print(f"🎯 原始xyxy座標: [{original_x1}, {original_y1}, {original_x2}, {original_y2}]")
                if (x1, y1, x2, y2) != (original_x1, original_y1, original_x2, original_y2):
                    print(f"   ⚠️ 邊界檢查後座標: [{x1}, {y1}, {x2}, {y2}]")
            else:
                # 後備方案：使用xywh格式
                x, y, w, h = bbox
                original_x1, original_y1, original_x2, original_y2 = x, y, x + w, y + h
                x1, y1, x2, y2 = original_x1, original_y1, original_x2, original_y2
                print(f"⚠️ 使用xywh格式切割: [{x}, {y}, {w}, {h}] -> [{x1}, {y1}, {x2}, {y2}]")
            
            # 直接從原圖提取區域或進行旋轉校正後提取
            if self.rotation_corrector.should_rotate(angle):
                # 進行旋轉校正：旋轉整個圖像，然後用原始框座標切割
                temp_bbox = [original_x1, original_y1, original_x2-original_x1, original_y2-original_y1]
                region, _ = self.rotation_corrector.correct_rotation(image_cv, temp_bbox, -angle)  # 負號是因為要反向旋轉校正
                print(f"🔄 文字塊 {block_index}: 旋轉校正 {angle:.1f}°")
                print(f"   📐 使用原始精確邊界框用於渲染: {bbox}")
                
                # Debug模式：保存原始斜文字區域和旋轉校正後的正立文字區域
                if self.debug_saver.is_enabled():
                    try:
                        # original: 原始斜的文字區域（直接從原圖切割）
                        original_region = image_cv[original_y1:original_y2, original_x1:original_x2]
                        # rotated: 旋轉校正後的正立文字區域
                        stem = Path(image_path).stem
                        
                        self.debug_saver.save_region_pair(original_region, region, stem, block_index)
                        print(f"🐛 Debug: 原始斜文字區域 [{original_x1}, {original_y1}, {original_x2}, {original_y2}]")
                        print(f"🐛 Debug: 旋轉校正後正立文字區域已保存")
                    except Exception as e:
                        print(f"⚠️ Debug保存失敗: {e}")
                        safe_region = image_cv[y1:y2, x1:x2]
                        self.debug_saver.save_image(safe_region, f"{stem}_block_{block_index:02d}_original.jpg")
                
                # 對於旋轉的文字框，rendered_bbox使用原始的精確邊界框
                # 因為comic-text-detector已經提供了很好的貼合文字的邊界框
                rendered_bbox = bbox
                
            else:
                # 沒有旋轉，直接使用xyxy進行精確裁切
                region = image_cv[y1:y2, x1:x2]
                rendered_bbox = bbox
                
                # Debug模式：保存原始圖片（使用原始座標）
                if self.debug_saver.is_enabled():
                    try:
                        original_region = image_cv[original_y1:original_y2, original_x1:original_x2]
                        stem = Path(image_path).stem
                        original_filename = f"{stem}_block_{block_index:02d}_original.jpg"
                        self.debug_saver.save_image(original_region, original_filename)
                        print(f"🐛 Debug: 使用原始座標 [{original_x1}, {original_y1}, {original_x2}, {original_y2}] 保存原始區域")
                    except Exception as e:
                        print(f"⚠️ Debug保存失敗，使用安全座標: {e}")
                        self.debug_saver.save_image(region, f"{stem}_block_{block_index:02d}_original.jpg")
            
            # 轉換顏色空間：BGR -> RGB
            if len(region.shape) == 3:
                region = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
            
            # 轉換為PIL圖片
            pil_image = Image.fromarray(region)
            
            # 返回包含邊界框信息的完整信息
            return {
                'pil_image': pil_image,
                'original_bbox': bbox,
                'rendered_bbox': rendered_bbox,  # 用於渲染的邊界框 - 使用原始精確邊界框
                'angle': angle,
                'was_rotated': self.rotation_corrector.should_rotate(angle, 0.1)
            }
            
        except Exception as e:
            print(f"❌ 區域提取失敗 (region {bbox}): {e}")
            return {
                'pil_image': None,
                'original_bbox': bbox,
                'rendered_bbox': bbox,
                'angle': angle,
                'was_rotated': False
            } 