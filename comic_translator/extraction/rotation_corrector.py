"""
Rotation Corrector
旋轉校正器

專門負責圖像旋轉校正功能
"""

import cv2
import numpy as np
from typing import List, Tuple


class RotationCorrector:
    """旋轉校正器"""
    
    def __init__(self):
        """初始化旋轉校正器"""
        pass
    
    def correct_rotation(self, image: np.ndarray, bbox: List[int], angle: float) -> Tuple[np.ndarray, List[int]]:
        """
        旋轉整個圖像使文字框變成正立，然後提取原始框區域
        
        Args:
            image: 原始完整圖片
            bbox: 文字框座標 [x, y, w, h]
            angle: 旋轉角度（度）
            
        Returns:
            Tuple[np.ndarray, List[int]]: (校正後的文字區域, 原始bbox)
        """
        if abs(angle) < 0.1:  # 角度太小，不需要旋轉
            x, y, w, h = bbox
            return image[y:y+h, x:x+w], bbox
        
        height, width = image.shape[:2]
        x, y, w, h = bbox
        
        # 計算文字框中心點
        center_x = x + w // 2
        center_y = y + h // 2
        
        # 創建旋轉矩陣（以文字框中心為旋轉中心）
        rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), -angle, 1.0)
        
        # 對整個圖像進行旋轉，讓傾斜的文字框變成正立
        rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                      borderMode=cv2.BORDER_REPLICATE)
        
        # 在旋轉後的圖像中，直接用原始bbox座標進行切割
        # 因為旋轉是以文字框中心為中心，所以原始框座標在旋轉後的圖像中
        # 對應的就是正立的文字區域
        
        # 確保座標在圖像範圍內
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        x2 = min(x + w, width)
        y2 = min(y + h, height)
        w = x2 - x
        h = y2 - y
        
        if w > 0 and h > 0:
            extracted_region = rotated_image[y:y+h, x:x+w]
            return extracted_region, bbox
        else:
            # 如果計算出的區域無效，返回原始區域
            return image[y:y+h, x:x+w], bbox
    
    def should_rotate(self, angle: float, threshold: float = 5.0) -> bool:
        """
        判斷是否需要進行旋轉校正
        
        Args:
            angle: 旋轉角度
            threshold: 角度閾值
            
        Returns:
            bool: 是否需要旋轉
        """
        return abs(angle) > threshold 