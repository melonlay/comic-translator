"""
Background Processor
背景處理器

專門負責對話框背景的處理功能
"""

import cv2
import numpy as np
from PIL import Image


class BackgroundProcessor:
    """背景處理器"""
    
    def __init__(self):
        """初始化背景處理器"""
        pass
    
    def process_background(self, image: Image.Image, x: int, y: int, width: int, height: int, bubble_type: str):
        """
        根據對話框類型處理背景 - 強化textured處理
        
        Args:
            image: 圖片對象
            x, y: 左上角座標
            width, height: 區域尺寸
            bubble_type: 對話框類型
        """
        # 提取對話框區域
        region = image.crop((x, y, x + width, y + height))
        
        if bubble_type == 'pure_white':
            # 純白對話框：直接填充白色
            white_region = Image.new('RGB', (width, height), 'white')
            image.paste(white_region, (x, y))
        else:
            # 有紋理或透明對話框：使用強化處理
            processed_region = self._create_textured_background(region, width, height)
            image.paste(processed_region, (x, y))
    
    def _create_textured_background(self, region: Image.Image, width: int, height: int) -> Image.Image:
        """
        創建智能修復的textured背景 - 使用圖像修復技術完全消除文字痕跡
        
        Args:
            region: 原始區域圖片
            width: 寬度
            height: 高度
            
        Returns:
            Image.Image: 修復後的背景圖片
        """
        # 將 PIL 圖片轉換為 OpenCV 格式
        region_cv = cv2.cvtColor(np.array(region), cv2.COLOR_RGB2BGR)
        
        # 步驟1: 創建文字掩膜 - 檢測可能的文字區域
        mask = self._create_text_mask(region_cv)
        
        # 步驟2: 使用圖像修復算法消除文字
        # 使用 Fast Marching Method 進行修復
        inpainted = cv2.inpaint(region_cv, mask, 5, cv2.INPAINT_TELEA)
        
        # 步驟3: 對修復結果進行後處理
        # 輕微模糊以使修復更自然
        inpainted = cv2.GaussianBlur(inpainted, (3, 3), 0)
        
        # 步驟4: 邊緣處理 - 確保邊界自然過渡
        inpainted = self._smooth_edges(inpainted, mask)
        
        # 轉換回 PIL 格式
        final_region = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
        
        return final_region
    
    def _create_text_mask(self, image_cv: np.ndarray) -> np.ndarray:
        """
        創建文字區域的掩膜
        
        Args:
            image_cv: OpenCV格式的圖片
            
        Returns:
            np.ndarray: 二值掩膜，白色為需要修復的區域
        """
        # 轉換為灰度
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # 方法1: 使用自適應閾值檢測文字
        # 創建自適應二值化
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # 方法2: 使用 Otsu 閾值
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 方法3: 檢測極端亮度或暗度區域（可能是文字）
        mean_brightness = np.mean(gray)
        # 檢測比平均亮度明顯不同的區域
        bright_mask = gray > (mean_brightness + 40)
        dark_mask = gray < (mean_brightness - 40)
        extreme_mask = (bright_mask | dark_mask).astype(np.uint8) * 255
        
        # 合併多種方法的結果
        # 取反 binary1 和 binary2（因為文字通常是暗色）
        text_mask1 = cv2.bitwise_not(binary1)
        text_mask2 = cv2.bitwise_not(binary2)
        
        # 合併掩膜
        combined_mask = cv2.bitwise_or(text_mask1, text_mask2)
        combined_mask = cv2.bitwise_or(combined_mask, extreme_mask)
        
        # 形態學操作清理掩膜
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # 先進行開運算去除小噪點
        cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # 再進行閉運算填補文字內部空隙
        final_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
        
        # 膨脹一點確保完全覆蓋文字邊緣
        final_mask = cv2.dilate(final_mask, kernel, iterations=1)
        
        return final_mask
    
    def _smooth_edges(self, inpainted: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        平滑修復區域的邊緣，使其與周圍更自然融合
        
        Args:
            inpainted: 修復後的圖片
            mask: 原始掩膜
            
        Returns:
            np.ndarray: 邊緣平滑後的圖片
        """
        # 創建羽化邊緣的掩膜
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated_mask = cv2.dilate(mask, kernel, iterations=1)
        
        # 創建羽化效果
        feathered_mask = cv2.GaussianBlur(dilated_mask.astype(np.float32), (7, 7), 0)
        feathered_mask = feathered_mask / 255.0
        
        # 對修復區域進行輕微的亮度和對比度調整，使其更好地融合
        # 計算周圍區域的平均亮度
        gray = cv2.cvtColor(inpainted, cv2.COLOR_BGR2GRAY)
        
        # 創建邊界區域掩膜（修復區域外圍的一圈）
        border_mask = cv2.dilate(mask, kernel, iterations=3) - mask
        border_mean = np.mean(gray[border_mask > 0]) if np.any(border_mask > 0) else 128
        
        # 調整修復區域的亮度使其接近邊界亮度
        repair_mean = np.mean(gray[mask > 0]) if np.any(mask > 0) else 128
        if repair_mean > 0:
            brightness_ratio = border_mean / repair_mean
            brightness_ratio = np.clip(brightness_ratio, 0.8, 1.2)  # 限制調整範圍
            
            # 應用亮度調整
            adjusted = inpainted.astype(np.float32) * brightness_ratio
            adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
            
            # 使用羽化掩膜混合調整後的結果
            for i in range(3):  # BGR 三個通道
                inpainted[:, :, i] = (adjusted[:, :, i] * feathered_mask + 
                                     inpainted[:, :, i] * (1 - feathered_mask))
        
        return inpainted.astype(np.uint8) 