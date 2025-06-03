"""
Manga OCR Extractor
漫畫OCR擷取器

使用manga-ocr進行日文文字擷取，支援旋轉校正和debug模式
原子化設計：組合各個專門的功能模組
"""

from typing import List, Dict
from .ocr_initializer import OCRInitializer
from .rotation_corrector import RotationCorrector
from .debug_saver import DebugSaver
from .region_extractor import RegionExtractor


class MangaOCRExtractor:
    """漫畫OCR擷取器 - 原子化組合器"""
    
    def __init__(self, debug_mode: bool = False, debug_dir: str = "debug"):
        """
        初始化OCR擷取器
        
        Args:
            debug_mode: 是否啟用debug模式
            debug_dir: debug檔案儲存目錄
        """
        # 初始化各個原子化模組
        self.ocr_initializer = OCRInitializer()
        self.rotation_corrector = RotationCorrector()
        self.debug_saver = DebugSaver(debug_mode, debug_dir)
        self.region_extractor = RegionExtractor(self.rotation_corrector, self.debug_saver)
        
        # 初始化OCR模型
        self.ocr_model = self.ocr_initializer.initialize_manga_ocr()
    
    def extract_from_region(self, image_path: str, bbox: List[int], block_index: int = 0, 
                           angle: float = 0.0, debug_mode: bool = False, xyxy: List[int] = None) -> Dict:
        """
        從圖片的指定區域提取文字
        
        Args:
            image_path: 圖片路徑
            bbox: 邊界框 [x, y, w, h]
            block_index: 文字塊索引（用於debug文件命名）
            angle: 旋轉角度（度）
            debug_mode: 是否啟用debug模式（已棄用，使用構造函數中的設置）
            xyxy: 精確的xyxy格式邊界框 [x1, y1, x2, y2]，優先使用
            
        Returns:
            Dict: 包含文字和邊界框信息的字典
        """
        # 使用區域提取器提取圖像區域
        extraction_result = self.region_extractor.extract_region(
            image_path, bbox, block_index, angle, xyxy
        )
        
        pil_image = extraction_result['pil_image']
        if pil_image is None:
            return {
                'text': "",
                'original_bbox': bbox,
                'rendered_bbox': bbox,
                'angle': angle,
                'was_rotated': False
            }
        
        # 執行OCR
        text = self.ocr_model(pil_image)
        
        # 返回包含邊界框信息的完整信息
        return {
            'text': text if text else "",
            'original_bbox': extraction_result['original_bbox'],
            'rendered_bbox': extraction_result['rendered_bbox'],
            'angle': extraction_result['angle'],
            'was_rotated': extraction_result['was_rotated']
        }
    
    def extract_from_boxes(self, image_path: str, text_boxes: List[List[int]], 
                          text_blocks: List[Dict] = None) -> List[Dict]:
        """
        從多個文字框擷取文字
        
        Args:
            image_path: 圖像路徑
            text_boxes: 文字框座標列表（向下兼容）
            text_blocks: 詳細文字塊信息（包含旋轉角度）
            
        Returns:
            List[Dict]: 擷取結果列表
        """
        # 如果沒有提供詳細信息，則使用簡單的bbox列表
        if text_blocks is None:
            if not text_boxes:
                return []
            text_blocks = [
                {
                    'block_index': i,
                    'bbox': bbox,
                    'angle': 0.0,
                    'vertical': False
                }
                for i, bbox in enumerate(text_boxes)
            ]
        
        if not text_blocks:
            return []
        
        results = []
        successful_count = 0
        
        for block in text_blocks:
            block_index = block.get('block_index', 0)
            bbox = block['bbox']
            xyxy = block.get('xyxy', None)  # 取得xyxy格式座標
            angle = block.get('angle', 0.0)
            vertical = block.get('vertical', False)
            
            print(f"📖 處理文字框 {block_index+1}/{len(text_blocks)}")
            if abs(angle) > 0.1:
                print(f"   🔄 檢測到旋轉角度: {angle:.1f}°")
            if vertical:
                print(f"   📝 檢測到直書文字")
            
            result = self.extract_from_region(image_path, bbox, block_index, angle, self.debug_saver.is_enabled(), xyxy)
            
            if result['text']:
                results.append({
                    'box_index': block_index,
                    'bbox': bbox,  # 原始檢測的邊界框
                    'rendered_bbox': result['rendered_bbox'],  # 用於渲染的邊界框
                    'text': result['text'],
                    'angle': angle,
                    'vertical': vertical,
                    'was_rotated': result['was_rotated'],
                    'confidence': 0.9  # manga-ocr沒有提供置信度，使用固定值
                })
                successful_count += 1
                print(f"  ✅ '{result['text']}'")
                if result['was_rotated']:
                    print(f"     🔄 旋轉校正: {bbox} → {result['rendered_bbox']}")
            else:
                print(f"  ⚠️ 未識別到文字")
        
        print(f"🎯 成功擷取 {successful_count}/{len(text_blocks)} 個文字框")
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
        result = self.extract_from_region(image_path, bbox)
        
        return {
            'bbox': bbox,
            'text': result['text'],
            'confidence': 0.9 if result['text'] else 0.0
        }
    
    def get_device_info(self) -> Dict:
        """
        獲取設備資訊
        
        Returns:
            Dict: 設備資訊
        """
        return self.ocr_initializer.get_device_info() 