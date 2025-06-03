"""
Comic Text Detector
漫畫文字檢測器

使用本地comic-text-detector進行文字框檢測
"""

import sys
import cv2
import os
from pathlib import Path
from typing import List, Tuple

# 添加本地comic-text-detector到路徑
comic_detector_path = Path(__file__).parent.parent.parent / "comic-text-detector"
if comic_detector_path.exists():
    sys.path.insert(0, str(comic_detector_path))
else:
    raise FileNotFoundError(f"找不到本地comic-text-detector: {comic_detector_path}")


class ComicTextDetector:
    """漫畫文字檢測器"""
    
    def __init__(self, 
                 input_size: int = 1024,
                 nms_thresh: float = 0.35,
                 conf_thresh: float = 0.4,
                 mask_thresh: float = 0.3,
                 use_cuda: bool = True):
        """
        初始化檢測器
        
        Args:
            input_size: 輸入圖像大小
            nms_thresh: NMS閾值
            conf_thresh: 置信度閾值
            mask_thresh: 遮罩閾值
            use_cuda: 是否使用CUDA
        """
        self.config = {
            'input_size': input_size,
            'nms_thresh': nms_thresh,
            'conf_thresh': conf_thresh,
            'mask_thresh': mask_thresh,
            'use_cuda': use_cuda
        }
        
        self.detector = None
        self.refinemask_annotation = None
        self._init_detector()
    
    def _init_detector(self):
        """初始化檢測器"""
        try:
            from inference import TextDetector
            from utils.textmask import REFINEMASK_ANNOTATION
            
            model_path = comic_detector_path / "data" / "comictextdetector.pt"
            if not model_path.exists():
                raise FileNotFoundError(f"找不到模型文件: {model_path}")
            
            self.detector = TextDetector(
                model_path=str(model_path),
                input_size=self.config['input_size'],
                device='cuda' if self.config['use_cuda'] else 'cpu',
                half=False,
                nms_thresh=self.config['nms_thresh'],
                conf_thresh=self.config['conf_thresh'],
                mask_thresh=self.config['mask_thresh'],
                act='leaky'
            )
            
            self.refinemask_annotation = REFINEMASK_ANNOTATION
            print(f"✅ Comic Text Detector初始化完成 (GPU: {self.config['use_cuda']})")
            
        except Exception as e:
            print(f"❌ Comic Text Detector初始化失敗: {e}")
            raise
    
    def detect(self, image_path: str) -> List[List[int]]:
        """
        檢測文字框
        
        Args:
            image_path: 圖像路徑
            
        Returns:
            List[List[int]]: 文字框座標列表 [[x, y, w, h], ...]
        """
        if self.detector is None:
            raise RuntimeError("檢測器未初始化")
        
        # 讀取圖像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"無法讀取圖像: {image_path}")
        
        height, width = image.shape[:2]
        
        # 執行檢測
        mask, mask_refined, blk_list = self.detector(
            image, 
            refine_mode=self.refinemask_annotation, 
            keep_undetected_mask=True
        )
        
        # 提取有效文字框
        text_boxes = []
        for blk in blk_list:
            x1, y1, x2, y2 = blk.xyxy
            x, y, w, h = max(0, x1), max(0, y1), x2 - x1, y2 - y1
            
            # 過濾太小的框
            if w >= 5 and h >= 5:
                text_boxes.append([int(float(x)), int(float(y)), int(float(w)), int(float(h))])  # 強制轉換為Python int
        
        # 按位置排序（從上到下，從右到左）
        text_boxes.sort(key=lambda box: (box[1], box[0]))
        
        return text_boxes
    
    def detect_with_metadata(self, image_path: str) -> dict:
        """
        檢測文字框並返回詳細資訊
        
        Args:
            image_path: 圖像路徑
            
        Returns:
            dict: 包含檢測結果和元數據
        """
        if self.detector is None:
            raise RuntimeError("檢測器未初始化")
        
        # 讀取圖像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"無法讀取圖像: {image_path}")
        
        height, width = image.shape[:2]
        
        # 執行檢測
        mask, mask_refined, blk_list = self.detector(
            image, 
            refine_mode=self.refinemask_annotation, 
            keep_undetected_mask=True
        )
        
        # 提取詳細文字框信息
        text_blocks = []
        for i, blk in enumerate(blk_list):
            x1, y1, x2, y2 = blk.xyxy
            x, y, w, h = max(0, x1), max(0, y1), x2 - x1, y2 - y1
            
            # 過濾太小的框
            if w >= 5 and h >= 5:
                # 直接從blk對象獲取屬性
                angle = float(getattr(blk, 'angle', 0))
                vertical = bool(getattr(blk, 'vertical', False))
                font_size = int(getattr(blk, 'font_size', 16))
                lines = getattr(blk, 'lines', [])
                
                # 處理lines數組
                if lines is not None and len(lines) > 0:
                    processed_lines = []
                    for line in lines:
                        if hasattr(line, 'tolist'):
                            processed_lines.append(line.tolist())
                        elif isinstance(line, (list, tuple)):
                            processed_lines.append(list(line))
                        else:
                            processed_lines.append(line)
                    lines = processed_lines
                else:
                    lines = []
                
                block_info = {
                    'block_index': i,
                    'bbox': [int(float(x)), int(float(y)), int(float(w)), int(float(h))],  # xywh格式
                    'xyxy': [int(float(x1)), int(float(y1)), int(float(x2)), int(float(y2))],  # xyxy格式，用於精確切割
                    'angle': angle,
                    'vertical': vertical,
                    'font_size': font_size,
                    'lines': lines,
                }
                text_blocks.append(block_info)
        
        # 按位置排序（從上到下，從右到左）
        text_blocks.sort(key=lambda block: (block['bbox'][1], block['bbox'][0]))
        
        # 為了向下兼容，也提供簡單的bbox列表
        text_boxes = [block['bbox'] for block in text_blocks]
        
        return {
            'text_boxes': text_boxes,  # 向下兼容
            'text_blocks': text_blocks,  # 詳細信息
            'total_boxes': len(text_blocks),
            'image_size': [width, height],
            'source_image': str(Path(image_path).absolute()),
            'config': self.config.copy()
        } 