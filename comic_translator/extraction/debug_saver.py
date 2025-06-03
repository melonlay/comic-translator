"""
Debug Saver
調試保存器

專門負責調試圖片的保存功能
"""

import cv2
import numpy as np
from pathlib import Path


class DebugSaver:
    """調試保存器"""
    
    def __init__(self, debug_mode: bool = False, debug_dir: str = "debug"):
        """
        初始化調試保存器
        
        Args:
            debug_mode: 是否啟用debug模式
            debug_dir: debug檔案儲存目錄
        """
        self.debug_mode = debug_mode
        self.debug_dir = Path(debug_dir)
        
        if self.debug_mode:
            self.debug_dir.mkdir(exist_ok=True)
            print(f"🐛 Debug模式啟用，子區域圖片將保存到: {self.debug_dir}")
    
    def save_image(self, image: np.ndarray, filename: str) -> None:
        """
        保存debug圖片
        
        Args:
            image: 圖片
            filename: 檔案名稱
        """
        if not self.debug_mode:
            return
            
        debug_path = self.debug_dir / filename
        cv2.imwrite(str(debug_path), image)
        print(f"🐛 Debug: 保存子區域圖片 -> {debug_path}")
    
    def save_region_pair(self, original_region: np.ndarray, rotated_region: np.ndarray, 
                        image_stem: str, block_index: int) -> None:
        """
        保存原始和旋轉校正後的區域對
        
        Args:
            original_region: 原始區域
            rotated_region: 旋轉校正後的區域
            image_stem: 圖片檔名（不含副檔名）
            block_index: 文字塊索引
        """
        if not self.debug_mode:
            return
        
        try:
            original_filename = f"{image_stem}_block_{block_index:02d}_original.jpg"
            rotated_filename = f"{image_stem}_block_{block_index:02d}_rotated.jpg"
            
            self.save_image(original_region, original_filename)
            self.save_image(rotated_region, rotated_filename)
            print(f"🐛 Debug: 原始斜文字區域")
            print(f"🐛 Debug: 旋轉校正後正立文字區域已保存")
        except Exception as e:
            print(f"⚠️ Debug保存失敗: {e}")
    
    def is_enabled(self) -> bool:
        """
        檢查debug模式是否啟用
        
        Returns:
            bool: 是否啟用debug模式
        """
        return self.debug_mode 