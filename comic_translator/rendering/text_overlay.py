"""
Text Overlay Renderer
文字覆蓋渲染器

讀取翻譯結果並將翻譯文字覆蓋到原始圖片的對話框上
支援橫書/直書和不同類型的對話框背景處理
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import cv2


class TextOverlay:
    """文字覆蓋渲染器"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化文字覆蓋渲染器
        
        Args:
            output_dir: 輸出資料夾路徑
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 嘗試載入中文字體
        self.font = self._load_font()
        
        print(f"✅ 文字覆蓋渲染器初始化完成，輸出目錄: {self.output_dir}")
    
    def _load_font(self, size: int = 20) -> ImageFont.ImageFont:
        """
        載入字體 - 簡化版，優先使用可靠的系統字型
        
        Args:
            size: 字體大小
            
        Returns:
            ImageFont.ImageFont: 字體對象
        """
        # 簡化字型優先順序，使用系統中確實存在的字型
        font_paths = [
            # 首選：微軟雅黑（系統確認存在）
            "C:/Windows/Fonts/msyh.ttc",         # Microsoft YaHei
            
            # 備用字型：其他常見中文字型
            "C:/Windows/Fonts/simsun.ttc",      # 宋體
            "C:/Windows/Fonts/simhei.ttf",      # 黑體
            "C:/Windows/Fonts/kaiu.ttf",        # 楷體
            "C:/Windows/Fonts/mingliu.ttc",     # 細明體
            
            # DFLiSong-Md（如果有的話）
            "DFLiSong-Md.ttf",
            "C:/Windows/Fonts/DFLiSong-Md.ttf",
            
            # 最後備用
            "arial.ttf"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, size)
                if "msyh" in font_path:
                    print(f"✅ 使用微軟雅黑字型: {font_path}")
                elif "DFLiSong" in font_path:
                    print(f"✅ 使用指定字型: {font_path}")
                else:
                    print(f"✅ 使用字型: {font_path}")
                return font
            except (OSError, IOError):
                continue
        
        # 最後備用：默認字型
        print("⚠️ 未找到任何字型，使用默認字型")
        return ImageFont.load_default()
    
    def _load_unicode_font(self, size: int = 20) -> ImageFont.ImageFont:
        """
        載入支援Unicode字符的字體
        
        Args:
            size: 字體大小
            
        Returns:
            ImageFont.ImageFont: Unicode字體對象
        """
        # 專門用於Unicode字符的字型，優先使用msgothic.ttc處理垂直省略號
        unicode_fonts = [
            ("C:/Windows/Fonts/msgothic.ttc", "MS Gothic"),          # 日文，支援垂直省略號⋮
            ("C:/Windows/Fonts/seguiemj.ttf", "Segoe UI Emoji"),      # 表情符號
            ("C:/Windows/Fonts/msyh.ttc", "Microsoft YaHei"),         # 簡中
            ("C:/Windows/Fonts/simsun.ttc", "宋體"),                 # 繁中備用
        ]
        
        for font_path, font_name in unicode_fonts:
            try:
                font = ImageFont.truetype(font_path, size)
                print(f"   🔤 成功載入Unicode字型: {font_name} ({font_path})")
                return font
            except (OSError, IOError) as e:
                print(f"   ❌ 載入字型失敗: {font_name} - {e}")
                continue
        
        # 回退到主字型
        print("   ⚠️ 所有Unicode字型載入失敗，使用主字型")
        return self._load_font(size)
    
    def render_translated_image(self, original_image_path: str, stage4_json_path: str = None) -> str:
        """
        渲染翻譯後的圖片
        
        Args:
            original_image_path: 原始圖片路徑
            stage4_json_path: Stage4翻譯結果JSON路徑（可選，會自動推導）
            
        Returns:
            str: 輸出圖片路徑
        """
        original_path = Path(original_image_path)
        
        # 自動推導JSON檔案路徑，優先從新的目錄結構尋找
        if stage4_json_path is None:
            # 新目錄結構: output/stages_results/
            stage4_json_path = f"output/stages_results/{original_path.stem}_stage4_translate.json"
            if not Path(stage4_json_path).exists():
                # 舊目錄結構: stages_results/
                stage4_json_path = f"stages_results/{original_path.stem}_stage4_translate.json"
                if not Path(stage4_json_path).exists():
                    # 最後嘗試results資料夾
                    stage4_json_path = f"results/{original_path.stem}_stage4_translate.json"
        
        stage4_path = Path(stage4_json_path)
        
        if not original_path.exists():
            raise FileNotFoundError(f"原始圖片不存在: {original_image_path}")
        
        if not stage4_path.exists():
            raise FileNotFoundError(f"翻譯結果JSON不存在: {stage4_json_path}")
        
        print(f"🎨 開始渲染翻譯圖片: {original_path.name}")
        print(f"📄 讀取翻譯結果: {stage4_path.name}")
        
        # 載入翻譯結果
        translation_data = self._load_translation_data(stage4_path)
        
        if not translation_data or not translation_data.get('translated_texts'):
            print("⚠️ 沒有找到翻譯文字")
            return None
        
        # 載入原始圖片
        image = Image.open(original_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 創建繪圖對象
        draw = ImageDraw.Draw(image)
        
        # 處理每個翻譯文字
        translated_texts = translation_data['translated_texts']
        print(f"📝 處理 {len(translated_texts)} 個翻譯文字")
        
        processed_count = 0
        skipped_count = 0
        
        for i, text_item in enumerate(translated_texts):
            try:
                # 檢查是否有實際翻譯發生
                original_text = text_item.get('original', '').strip()
                translated_text = text_item.get('translated', '').strip()
                
                # 如果原文和翻譯完全相同，跳過渲染
                if original_text == translated_text and original_text:
                    print(f"   ⏭️ 跳過項目 {i+1}: 原文與翻譯相同 '{original_text}'")
                    skipped_count += 1
                    continue
                
                # 如果翻譯為空，也跳過
                if not translated_text:
                    print(f"   ⏭️ 跳過項目 {i+1}: 翻譯為空")
                    skipped_count += 1
                    continue
                
                # 兼容舊格式：如果沒有新字段，使用默認值
                if 'text_direction' not in text_item:
                    text_item['text_direction'] = 'horizontal'
                if 'bubble_type' not in text_item:
                    text_item['bubble_type'] = 'pure_white'
                if 'estimated_font_size' not in text_item:
                    text_item['estimated_font_size'] = 16
                
                self._overlay_text_enhanced(draw, text_item, image)
                direction = text_item.get('text_direction', 'horizontal')
                bubble_type = text_item.get('bubble_type', 'pure_white')
                print(f"   ✅ 處理文字 {processed_count+1}: '{translated_text[:15]}...' ({direction}, {bubble_type})")
                processed_count += 1
                
            except Exception as e:
                print(f"   ⚠️ 處理文字 {i+1} 失敗: {e}")
                skipped_count += 1
        
        print(f"📊 渲染統計: 成功 {processed_count} 個，跳過 {skipped_count} 個")
        
        # 保存結果
        output_filename = f"translated_{original_path.name}"
        output_path = self.output_dir / output_filename
        
        image.save(output_path, quality=95)
        print(f"💾 翻譯圖片已保存: {output_path}")
        
        return str(output_path)
    
    def _load_translation_data(self, json_path: Path) -> Optional[Dict[str, Any]]:
        """
        載入翻譯結果數據
        
        Args:
            json_path: JSON檔案路徑
            
        Returns:
            Optional[Dict]: 翻譯數據
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 讀取翻譯結果失敗: {e}")
            return None
    
    def _preprocess_text_for_direction(self, text: str, text_direction: str) -> str:
        """
        根據文字方向預處理文字內容
        
        Args:
            text: 原始文字
            text_direction: 文字方向 ('horizontal' 或 'vertical')
            
        Returns:
            str: 處理後的文字
        """
        if not text:
            return text
        
        # 統一省略號格式
        processed_text = self._normalize_ellipsis(text)
        
        # 如果是直書，需要特殊處理省略號
        if text_direction == 'vertical':
            processed_text = self._convert_ellipsis_for_vertical(processed_text)
        
        return processed_text
    
    def _normalize_ellipsis(self, text: str) -> str:
        """
        統一省略號格式 - 中文省略號應為六個點（兩個省略號符號）
        
        Args:
            text: 原始文字
            
        Returns:
            str: 格式化後的文字
        """
        import re
        
        # 將六個或以上連續半形點號轉換成標準中文省略號（六個點）
        text = re.sub(r'\.{6,}', '……', text)
        
        # 將三到五個連續半形點號轉換成標準中文省略號
        text = re.sub(r'\.{3,5}', '……', text)
        
        # 將兩個半形點號轉換成標準中文省略號（因為可能是簡化表示）
        text = re.sub(r'\.{2}', '……', text)
        
        # 將多個連續的全形點號轉換成標準中文省略號
        text = re.sub(r'[．。]{2,}', '……', text)
        
        # 將單個省略號符號轉換為標準中文省略號（兩個省略號符號）
        text = re.sub(r'(?<!…)…(?!…)', '……', text)  # 只轉換孤立的單個省略號
        
        # 將三個或以上連續的省略號符號簡化為兩個（保持標準六個點）
        text = re.sub(r'…{3,}', '……', text)
        
        # 將中間點「·」的多個連續出現也轉換為省略號
        text = re.sub(r'[·]{3,}', '……', text)
        
        return text
    
    def _convert_ellipsis_for_vertical(self, text: str) -> str:
        """
        將文字轉換為適合直書的格式
        
        Args:
            text: 原始文字
            
        Returns:
            str: 轉換後的文字
        """
        # 對於垂直文字的字符轉換
        # 1. 將水平省略號轉換為垂直省略號
        # 中文標準省略號"……"（六個點）轉換為垂直形式
        text = text.replace('……', '⋮⋮')  # 兩個垂直省略號表示六個點
        
        # 處理單個省略號（如果還有的話）
        text = text.replace('…', '⋮')
        
        # 2. 將長橫線轉換為長直線（垂直排版）
        # 優先處理多字符的情況
        
        # 雙Box Drawing橫線 → 垂直線
        text = text.replace('──', '│')  # U+2500*2 → U+2502 (Box Drawing垂直線)
        
        # 雙破折號
        text = text.replace('——', '│')  # 雙破折號變成單垂直線
        
        # 多個片假名長音符
        text = text.replace('ーーー', '│')  # 三個長音符
        text = text.replace('ーー', '│')   # 兩個長音符
        
        # 單字符轉換
        # 片假名長音符
        text = text.replace('ー', '│')  # U+30FC → U+2502
        
        # 破折號轉換為垂直線
        text = text.replace('—', '│')  # U+2014 → U+2502
        text = text.replace('─', '│')  # U+2500 → U+2502 (Box Drawing)
        
        # 連字符在垂直排版中也轉換
        text = text.replace('－', '│')  # U+FF0D (全形連字符) → U+2502
        
        return text
    
    def _overlay_text_enhanced(self, draw: ImageDraw.ImageDraw, text_item: Dict[str, Any], image: Image.Image):
        """
        增強版文字覆蓋，支援垂直文字和智能背景處理
        
        Args:
            draw: 繪圖對象
            text_item: 翻譯文字項目
            image: 原始圖片對象
        """
        bbox = text_item.get('bbox')
        translated_text = text_item.get('translated', '')
        text_direction = text_item.get('text_direction', 'horizontal')
        bubble_type = text_item.get('bubble_type', 'pure_white')
        estimated_font_size = text_item.get('estimated_font_size', 16)
        
        if not bbox or not translated_text:
            return
        
        # 預處理文字內容（處理省略號等）
        processed_text = self._preprocess_text_for_direction(translated_text, text_direction)
        
        # bbox格式: [x, y, width, height]
        x, y, width, height = bbox
        
        # 確保座標在圖片範圍內
        x = max(0, min(x, image.size[0] - 1))
        y = max(0, min(y, image.size[1] - 1))
        width = min(width, image.size[0] - x)
        height = min(height, image.size[1] - y)
        
        # 根據對話框類型處理背景
        self._process_background(image, x, y, width, height, bubble_type)
        
        # 計算字體大小（參考估計值）
        font_size = self._calculate_font_size_enhanced(
            processed_text, width, height, text_direction, estimated_font_size
        )
        font = self._load_font(font_size)
        
        # 根據文字方向繪製文字
        if text_direction == 'vertical':
            self._draw_vertical_text(draw, processed_text, x, y, width, height, font)
        else:
            self._draw_horizontal_text(draw, processed_text, x, y, width, height, font)
    
    def _process_background(self, image: Image.Image, x: int, y: int, width: int, height: int, bubble_type: str):
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
    
    def _calculate_font_size_enhanced(self, text: str, width: int, height: int, 
                                    text_direction: str, estimated_size: int) -> int:
        """
        使用迭代方法計算最適字體大小
        
        Args:
            text: 文字內容
            width: 可用寬度
            height: 可用高度
            text_direction: 文字方向
            estimated_size: 估計的原始字體大小
            
        Returns:
            int: 計算出的字體大小
        """
        text_length = len(text.strip())
        if text_length == 0:
            return 24
        
        if text_direction == 'horizontal':
            return self._calculate_horizontal_font_size_iterative(text, width, height)
        else:
            return self._calculate_vertical_font_size_iterative(text, width, height)
    
    def _calculate_horizontal_font_size_iterative(self, text: str, width: int, height: int) -> int:
        """
        橫書字體大小迭代計算 - 考慮正確的行間距
        
        Args:
            text: 文字內容
            width: 可用寬度
            height: 可用高度
            
        Returns:
            int: 最適字體大小
        """
        min_font_size = 16
        max_font_size = 60
        
        # 從大字體開始迭代
        for font_size in range(max_font_size, min_font_size - 1, -2):
            font = self._load_font(font_size)
            
            # 計算每行能放多少字
            chars_per_row = self._calculate_chars_per_row(text, width * 0.9, font)
            if chars_per_row == 0:
                continue
            
            # 計算需要多少行
            total_chars = len(text)
            required_rows = (total_chars + chars_per_row - 1) // chars_per_row
            
            # 獲取字體實際高度
            try:
                bbox = font.getbbox("測試Ag")
                font_height = bbox[3] - bbox[1]
            except:
                font_height = font_size
            
            # 計算行間距和總高度
            line_spacing = font_height * 0.4  # 行間距為字體高度的40%
            required_height = required_rows * font_height + (required_rows - 1) * line_spacing
            
            # 如果能放入，就是最適字體大小
            if required_height <= height:
                print(f"   📏 橫書: {width}x{height}, 字體: {font_size}, 每行: {chars_per_row}字, 行數: {required_rows}, 總高: {required_height:.1f}")
                return font_size
        
        return min_font_size
    
    def _calculate_vertical_font_size_iterative(self, text: str, width: int, height: int) -> int:
        """
        直書字體大小迭代計算
        
        Args:
            text: 文字內容
            width: 可用寬度
            height: 可用高度
            
        Returns:
            int: 最適字體大小
        """
        min_font_size = 16
        max_font_size = 60
        
        # 從大字體開始迭代
        for font_size in range(max_font_size, min_font_size - 1, -2):
            font = self._load_font(font_size)
            
            # 計算每列能放多少字
            chars_per_column = self._calculate_chars_per_column(height, font_size)
            if chars_per_column == 0:
                continue
            
            # 計算需要多少列
            total_chars = len(text)
            required_columns = (total_chars + chars_per_column - 1) // chars_per_column
            
            # 計算需要的總寬度
            column_width = font_size * 1.2  # 列寬係數
            required_width = required_columns * column_width
            
            # 如果能放入，就是最適字體大小
            if required_width <= width:
                print(f"   📏 直書: {width}x{height}, 字體: {font_size}, 每列: {chars_per_column}字, 列數: {required_columns}")
                return font_size
        
        return min_font_size
    
    def _calculate_chars_per_row(self, text: str, max_width: int, font: ImageFont.ImageFont) -> int:
        """
        計算每行能放多少字符
        
        Args:
            text: 文字內容
            max_width: 最大寬度
            font: 字體對象
            
        Returns:
            int: 每行字符數
        """
        if not text:
            return 0
        
        current_line = ""
        for i, char in enumerate(text):
            test_line = current_line + char
            
            try:
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(test_line) * (font.size * 0.7)
            
            if text_width > max_width:
                return max(1, len(current_line))
            
            current_line = test_line
        
        return len(text)  # 所有字符都能放在一行
    
    def _calculate_chars_per_column(self, max_height: int, font_size: int) -> int:
        """
        計算每列能放多少字符
        
        Args:
            max_height: 最大高度
            font_size: 字體大小
            
        Returns:
            int: 每列字符數
        """
        char_height = font_size * 1.2  # 字符高度係數
        return max(1, int(max_height // char_height))
    
    def _draw_horizontal_text(self, draw: ImageDraw.ImageDraw, text: str, x: int, y: int, 
                             width: int, height: int, font: ImageFont.ImageFont):
        """
        繪製水平文字（橫書）- 逐字符處理Unicode
        
        Args:
            draw: 繪圖對象
            text: 文字內容  
            x, y: 左上角座標
            width, height: 區域尺寸
            font: 字體對象
        """
        # 計算每行能放多少字
        chars_per_row = self._calculate_chars_per_row(text, width * 0.9, font)
        
        # 分割文字成行
        lines = []
        for i in range(0, len(text), chars_per_row):
            line = text[i:i + chars_per_row]
            lines.append(line)
        
        if not lines:
            return
        
        # 獲取字體的實際高度信息
        try:
            bbox = font.getbbox("測試Ag")
            font_height = bbox[3] - bbox[1]
        except:
            font_height = font.size
        
        # 計算正確的行間距
        line_spacing = font_height * 0.4
        line_height = font_height + line_spacing
        
        # 計算總文字高度
        total_text_height = len(lines) * font_height + (len(lines) - 1) * line_spacing
        
        # 垂直居中
        start_y = y + max(0, (height - total_text_height) // 2)
        
        # 預載入Unicode字型
        unicode_font = self._load_unicode_font(font.size)
        
        for i, line in enumerate(lines):
            # 每行的y座標
            line_y = start_y + i * line_height
            line_y = max(y, min(line_y, y + height - font_height))
            
            # 計算整行寬度以實現水平居中
            total_line_width = self._calculate_line_width(line, font, unicode_font)
            line_x = x + (width - total_line_width) // 2
            line_x = max(x, line_x)
            
            # 逐字符渲染
            current_x = line_x
            for char in line:
                if self._is_special_unicode_char(char):
                    # Unicode字符用專門字型
                    try:
                        draw.text((current_x, line_y), char, font=unicode_font, fill='black')
                        char_width = self._get_char_width(char, unicode_font)
                    except:
                        draw.text((current_x, line_y), char, font=font, fill='black')
                        char_width = self._get_char_width(char, font)
                else:
                    # 普通字符用標準字型
                    draw.text((current_x, line_y), char, font=font, fill='black')
                    char_width = self._get_char_width(char, font)
                
                current_x += char_width
            
            # 調試信息
            if i == 0:
                print(f"   📐 行間距計算: 字體高度={font_height:.1f}, 行間距={line_spacing:.1f}")
    
    def _calculate_line_width(self, line: str, font: ImageFont.ImageFont, unicode_font: ImageFont.ImageFont) -> int:
        """
        計算一行文字的總寬度（考慮混合字型）
        
        Args:
            line: 文字行
            font: 標準字型
            unicode_font: Unicode字型
            
        Returns:
            int: 總寬度
        """
        total_width = 0
        for char in line:
            if self._is_special_unicode_char(char):
                total_width += self._get_char_width(char, unicode_font)
            else:
                total_width += self._get_char_width(char, font)
        return total_width
    
    def _get_char_width(self, char: str, font: ImageFont.ImageFont) -> int:
        """
        獲取字符寬度
        
        Args:
            char: 字符
            font: 字型
            
        Returns:
            int: 字符寬度
        """
        try:
            bbox = font.getbbox(char)
            return bbox[2] - bbox[0]
        except:
            return int(font.size * 0.7)
    
    def _draw_vertical_text(self, draw: ImageDraw.ImageDraw, text: str, x: int, y: int, 
                           width: int, height: int, font: ImageFont.ImageFont):
        """
        繪製垂直文字（直書）- 逐字符處理Unicode，支援標點符號置中
        
        Args:
            draw: 繪圖對象
            text: 文字內容（已經過預處理）
            x, y: 起始位置
            width, height: 可用區域
            font: 字體對象
        """
        if not text:
            return
        
        # 計算每列的字符數
        chars_per_column = self._calculate_chars_per_column(height, font.size)
        if chars_per_column == 0:
            return
        
        # 分割文字為多列
        columns = []
        for i in range(0, len(text), chars_per_column):
            column = text[i:i + chars_per_column]
            columns.append(column)
        
        # 計算列間距
        if len(columns) > 1:
            column_spacing = max(width // len(columns), font.size)
        else:
            column_spacing = width
        
        # 預載入Unicode字型
        unicode_font = self._load_unicode_font(font.size)
        
        # 繪製每一列
        for col_idx, column in enumerate(columns):
            # 計算此列的x位置（從右到左）
            col_x = x + width - (col_idx + 1) * column_spacing + (column_spacing - font.size) // 2
            col_x = max(x, min(col_x, x + width - font.size))
            
            # 繪製此列的每個字符
            for char_idx, char in enumerate(column):
                char_y = y + char_idx * font.size
                
                # 確保不超出下邊界
                if char_y + font.size > y + height:
                    break
                
                # 計算字符的實際繪製位置
                char_draw_x = col_x
                char_draw_y = char_y
                
                # 標點符號置中處理
                if self._is_punctuation_char(char):
                    # 標點符號需要置中顯示
                    char_draw_x = col_x + font.size // 4  # 向右偏移以達到置中效果
                
                # 特殊處理垂直省略號
                if char in ['⋮', '︙', '⁞']:
                    # 垂直省略號也需要置中
                    char_draw_x = col_x + font.size // 4
                    try:
                        # 嘗試用Unicode字型繪製垂直省略號
                        draw.text((char_draw_x, char_draw_y), char, font=unicode_font, fill='black')
                    except:
                        try:
                            # 回退到標準字型
                            draw.text((char_draw_x, char_draw_y), char, font=font, fill='black')
                        except:
                            # 手動繪製三個小點
                            self._draw_manual_vertical_dots(draw, char_draw_x, char_draw_y, font.size)
                else:
                    # 普通字符逐個處理
                    if self._is_special_unicode_char(char):
                        # Unicode字符用專門字型
                        print('偵測到Unicode字符', char)
                        try:
                            draw.text((char_draw_x, char_draw_y), char, font=unicode_font, fill='black')
                        except:
                            draw.text((char_draw_x, char_draw_y), char, font=font, fill='black')
                    else:
                        # 普通字符用標準字型
                        draw.text((char_draw_x, char_draw_y), char, font=font, fill='black')
            
            print(f"   📏 直書列{col_idx+1}: x={col_x}, 字符數={len(column)}")
    
    def _is_punctuation_char(self, char: str) -> bool:
        """
        檢測是否為標點符號（需要置中顯示）
        
        Args:
            char: 字符
            
        Returns:
            bool: 是否為標點符號
        """
        # 常見的標點符號範圍
        punctuation_chars = {
            '。', '，', '、', '；', '：', '？', '！', 
            '「', '」', '『', '』', '（', '）', '〈', '〉',
            '《', '》', '【', '】', '〔', '〕', '〖', '〗',
            '．', '‧', '·', '…', '⋮', '︙',
            # 垂直排版的線條符號
            '｜', '|', '─', '—', '－', 'ー', '│'
        }
        
        return char in punctuation_chars
    
    def _draw_manual_vertical_dots(self, draw: ImageDraw.ImageDraw, x: int, y: int, font_size: int):
        """
        手動繪製垂直三點省略號（置中版本）
        
        Args:
            draw: 繪圖對象
            x, y: 位置
            font_size: 字體大小
        """
        point_radius = max(2, font_size // 15)
        point_spacing = font_size // 4
        total_dots_height = point_spacing * 2
        
        # 垂直置中
        start_y = y + (font_size - total_dots_height) // 2
        # 水平置中
        center_x = x + font_size // 2
        
        for point_idx in range(3):
            point_y = start_y + point_idx * point_spacing
            draw.ellipse([
                center_x - point_radius, point_y - point_radius,
                center_x + point_radius, point_y + point_radius
            ], fill='black')
    
    def batch_render_folder(self, folder_path: str) -> List[str]:
        """
        批量渲染資料夾中的翻譯結果
        
        Args:
            folder_path: 包含原始圖片的資料夾路徑
            
        Returns:
            List[str]: 成功渲染的輸出路徑列表
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"資料夾不存在: {folder_path}")
        
        # 獲取所有圖片檔案
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
        
        image_files.sort(key=lambda x: x.name.lower())
        
        print(f"📁 開始批量渲染資料夾: {folder_path}")
        print(f"🖼️ 找到 {len(image_files)} 個圖片檔案")
        
        rendered_files = []
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n🎨 渲染第 {i}/{len(image_files)} 張: {image_file.name}")
            
            try:
                output_path = self.render_translated_image(str(image_file))
                if output_path:
                    rendered_files.append(output_path)
                    print(f"✅ 渲染成功: {Path(output_path).name}")
                else:
                    print(f"⚠️ 渲染跳過: {image_file.name}")
                    
            except Exception as e:
                print(f"❌ 渲染失敗: {e}")
        
        print(f"\n🎉 批量渲染完成: {len(rendered_files)}/{len(image_files)} 成功")
        return rendered_files
    
    def get_info(self) -> Dict[str, Any]:
        """
        獲取渲染器資訊
        
        Returns:
            Dict: 渲染器資訊
        """
        return {
            'output_directory': str(self.output_dir.absolute()),
            'font_loaded': self.font is not None,
            'font_size': getattr(self.font, 'size', 'unknown')
        }
    
    def _is_special_unicode_char(self, char: str) -> bool:
        """
        檢測是否為特殊Unicode字符（不包括正常的中日韓文字）
        
        Args:
            char: 字符
            
        Returns:
            bool: 是否為特殊字符
        """
        # 檢查空字符
        if not char:
            return False
            
        # 檢測特殊字符範圍
        code = ord(char)
        
        # 先排除正常的文字範圍
        normal_text_ranges = [
            (0x4E00, 0x9FFF),   # CJK統一漢字
            (0x3400, 0x4DBF),   # CJK擴展A
            (0x3040, 0x309F),   # 平假名
            (0x30A0, 0x30FF),   # 片假名
            (0xFF00, 0xFFEF),   # 全形ASCII、半形片假名
            (0x0020, 0x007F),   # 基本拉丁字母
            (0x00A0, 0x00FF),   # 拉丁字母補充
        ]
        
        # 如果是正常文字，不是特殊字符
        if any(start <= code <= end for start, end in normal_text_ranges):
            return False
        
        # 只有真正的特殊符號才需要特殊處理
        special_ranges = [
            (0x2000, 0x206F),   # 一般標點符號（包含…等）
            (0x2200, 0x22FF),   # 數學運算符號（包含⋮等）
            (0x2600, 0x26FF),   # 雜項符號（包含♪等音樂符號）
            (0x2700, 0x27BF),   # 裝飾符號
            (0x1F300, 0x1F5FF), # 雜項符號和象形文字
            (0x1F600, 0x1F64F), # 表情符號
            (0x1F680, 0x1F6FF), # 交通和地圖符號
            (0x1F900, 0x1F9FF), # 補充符號和象形文字
            (0x2190, 0x21FF),   # 箭頭
            (0x25A0, 0x25FF),   # 幾何圖形
            (0xFE10, 0xFE1F),   # 垂直格式（包含︙）
        ]
        
        is_special = any(start <= code <= end for start, end in special_ranges)
        
        # 調試信息：對特殊字符輸出詳細信息
        if is_special:
            print(f"   🎯 檢測到特殊Unicode字符: '{char}' (U+{code:04X})")
        
        return is_special
    
    def _draw_text_with_unicode_support(self, draw: ImageDraw.ImageDraw, text: str, 
                                       x: int, y: int, font: ImageFont.ImageFont):
        """
        使用Unicode支援繪製文字
        
        Args:
            draw: 繪圖對象
            text: 文字
            x, y: 座標
            font: 主字型
        """
        unicode_font = None
        current_x = x
        
        for char in text:
            if self._is_special_unicode_char(char):
                # 對特殊字符使用Unicode字型
                if unicode_font is None:
                    unicode_font = self._load_unicode_font(font.size)
                
                try:
                    # 先嘗試用Unicode字型繪製
                    draw.text((current_x, y), char, font=unicode_font, fill='black')
                except:
                    # 如果失敗，使用主字型
                    draw.text((current_x, y), char, font=font, fill='black')
            else:
                # 普通字符使用主字型
                draw.text((current_x, y), char, font=font, fill='black')
            
            # 計算下一個字符的x位置
            try:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
            except:
                char_width = font.size * 0.7
            
            current_x += char_width 