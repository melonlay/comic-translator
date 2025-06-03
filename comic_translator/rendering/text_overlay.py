"""
Text Overlay Renderer
文字覆蓋渲染器

讀取翻譯結果並將翻譯文字覆蓋到原始圖片的對話框上
支援橫書/直書和不同類型的對話框背景處理
原子化設計：組合各個專門的功能模組
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from .font_loader import FontLoader
from .text_preprocessor import TextPreprocessor
from .font_calculator import FontCalculator
from .unicode_handler import UnicodeHandler
from .background_processor import BackgroundProcessor


class TextOverlay:
    """文字覆蓋渲染器 - 原子化組合器"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化文字覆蓋渲染器
        
        Args:
            output_dir: 輸出資料夾路徑
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化各個原子化模組
        self.font_loader = FontLoader()
        self.text_preprocessor = TextPreprocessor()
        self.font_calculator = FontCalculator(self.font_loader)
        self.unicode_handler = UnicodeHandler()
        self.background_processor = BackgroundProcessor()
        
        # 嘗試載入中文字體
        self.font = self.font_loader.load_font()
        
        print(f"✅ 文字覆蓋渲染器初始化完成，輸出目錄: {self.output_dir}")
    
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
    
    def _overlay_text_enhanced(self, draw: ImageDraw.ImageDraw, text_item: Dict[str, Any], image: Image.Image):
        """
        高級文字覆蓋方法，支援旋轉文字渲染
        
        Args:
            draw: 繪圖對象
            text_item: 翻譯文字項目
            image: 原始圖片對象
        """
        # 優先使用rendered_bbox，如果沒有則使用原始bbox
        bbox = text_item.get('rendered_bbox') or text_item.get('bbox')
        translated_text = text_item.get('translated', '')
        text_direction = text_item.get('text_direction', 'horizontal')
        bubble_type = text_item.get('bubble_type', 'pure_white')
        estimated_font_size = text_item.get('estimated_font_size', 16)
        angle = text_item.get('angle', 0.0)
        was_rotated = text_item.get('was_rotated', False)
        
        if not bbox or not translated_text:
            return
        
        # 顯示旋轉信息
        if was_rotated and abs(angle) > 0.1:
            print(f"   🔄 渲染旋轉文字: 角度 {angle:.1f}°, 使用校正後邊界框")
        
        # 預處理文字內容（處理省略號等）
        processed_text = self.text_preprocessor.preprocess_for_direction(translated_text, text_direction)
        
        # bbox格式: [x, y, width, height]
        x, y, width, height = bbox
        
        # 確保座標在圖片範圍內
        x = max(0, min(x, image.size[0] - 1))
        y = max(0, min(y, image.size[1] - 1))
        width = min(width, image.size[0] - x)
        height = min(height, image.size[1] - y)
        
        # 根據對話框類型處理背景
        self.background_processor.process_background(image, x, y, width, height, bubble_type)
        
        # 如果有旋轉角度，使用旋轉渲染
        if abs(angle) > 0.1:
            self._render_rotated_text(image, processed_text, x, y, width, height, 
                                    angle, text_direction, estimated_font_size)
        else:
            # 沒有旋轉，使用正常渲染
            # 計算字體大小（參考估計值）
            font_size = self.font_calculator.calculate_font_size_enhanced(
                processed_text, width, height, text_direction, estimated_font_size
            )
            font = self.font_loader.load_font(font_size)
            
            # 根據文字方向繪製文字
            if text_direction == 'vertical':
                self._draw_vertical_text(draw, processed_text, x, y, width, height, font)
            else:
                self._draw_horizontal_text(draw, processed_text, x, y, width, height, font)
    
    def _render_rotated_text(self, image: Image.Image, text: str, x: int, y: int, 
                           width: int, height: int, angle: float, text_direction: str, 
                           estimated_font_size: int):
        """
        渲染旋轉的文字 - 使用rendered_bbox的尺寸來計算字體，然後旋轉回原始角度
        
        Args:
            image: 原始圖片
            text: 文字內容
            x, y: rendered_bbox的左上角座標
            width, height: rendered_bbox的尺寸（旋轉校正後的尺寸）
            angle: 旋轉角度（度）
            text_direction: 文字方向
            estimated_font_size: 估計字體大小
        """
        # 直接使用rendered_bbox的尺寸計算字體大小
        font_size = self.font_calculator.calculate_font_size_enhanced(
            text, width, height, text_direction, estimated_font_size
        )
        font = self.font_loader.load_font(font_size)
        
        print(f"   📐 使用校正後尺寸 {width}x{height} 計算字體大小: {font_size}")
        
        # 創建適合校正後尺寸的文字圖像
        text_image = self._create_text_image_for_size(text, font, text_direction, width, height)
        
        if text_image is None:
            return
        
        print(f"   📏 創建的文字圖像尺寸: {text_image.size}")
        
        # 旋轉文字圖像回原始角度
        rotated_text_image = text_image.rotate(-angle, expand=True, fillcolor=(255, 255, 255, 0))
        
        print(f"   🔄 旋轉後文字圖像尺寸: {rotated_text_image.size}")
        
        # 計算在rendered_bbox內的居中位置
        paste_x = x + (width - rotated_text_image.size[0]) // 2
        paste_y = y + (height - rotated_text_image.size[1]) // 2
        
        # 確保座標在圖像範圍內
        paste_x = max(0, min(paste_x, image.size[0] - rotated_text_image.size[0]))
        paste_y = max(0, min(paste_y, image.size[1] - rotated_text_image.size[1]))
        
        print(f"   📍 最終貼上位置: ({paste_x}, {paste_y})")
        
        # 將旋轉後的文字貼到原圖上
        if rotated_text_image.mode == 'RGBA':
            image.paste(rotated_text_image, (paste_x, paste_y), rotated_text_image)
        else:
            image.paste(rotated_text_image, (paste_x, paste_y))
        
        print(f"   🎯 旋轉文字渲染完成: {text[:15]}... (角度: {angle:.1f}°)")
    
    def _create_text_image_for_size(self, text: str, font: ImageFont.ImageFont, 
                                   text_direction: str, target_width: int, target_height: int) -> Image.Image:
        """
        創建指定尺寸的文字圖像
        
        Args:
            text: 文字內容
            font: 字體
            text_direction: 文字方向
            target_width, target_height: 目標尺寸
            
        Returns:
            Image.Image: 文字圖像
        """
        if not text:
            return None
        
        # 創建指定尺寸的透明背景圖像
        text_image = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)
        
        # 繪製文字
        if text_direction == 'vertical':
            self._draw_vertical_text_on_image(text_draw, text, 0, 0, target_width, target_height, font)
        else:
            self._draw_horizontal_text_on_image(text_draw, text, 0, 0, target_width, target_height, font)
        
        return text_image
    
    def _draw_horizontal_text(self, draw: ImageDraw.ImageDraw, text: str, x: int, y: int, 
                             width: int, height: int, font: ImageFont.ImageFont):
        """
        繪製水平文字（橫書）- 使用原子化的Unicode處理器
        """
        # 計算每行能放多少字
        chars_per_row = self.font_calculator._calculate_chars_per_row(text, width * 0.9, font)
        
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
        unicode_font = self.font_loader.load_unicode_font(font.size)
        
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
                if self.unicode_handler.is_special_unicode_char(char):
                    # Unicode字符用專門字型
                    try:
                        draw.text((current_x, line_y), char, font=unicode_font, fill='black')
                        char_width = self.unicode_handler.get_char_width(char, unicode_font)
                    except:
                        draw.text((current_x, line_y), char, font=font, fill='black')
                        char_width = self.unicode_handler.get_char_width(char, font)
                else:
                    # 普通字符用標準字型
                    draw.text((current_x, line_y), char, font=font, fill='black')
                    char_width = self.unicode_handler.get_char_width(char, font)
                
                current_x += char_width
    
    def _draw_vertical_text(self, draw: ImageDraw.ImageDraw, text: str, x: int, y: int,
                           width: int, height: int, font: ImageFont.ImageFont):
        """
        繪製垂直文字（直書）- 使用原子化的Unicode處理器
        """
        if not text:
            return
        
        # 計算每列的字符數
        chars_per_column = self.font_calculator._calculate_chars_per_column(height, font.size)
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
        unicode_font = self.font_loader.load_unicode_font(font.size)
        
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
                if self.unicode_handler.is_punctuation_char(char):
                    # 標點符號需要置中顯示
                    char_draw_x = col_x + font.size // 4
                
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
                            self.unicode_handler.draw_manual_vertical_dots(draw, char_draw_x, char_draw_y, font.size)
                else:
                    # 普通字符逐個處理
                    if self.unicode_handler.is_special_unicode_char(char):
                        # Unicode字符用專門字型
                        try:
                            draw.text((char_draw_x, char_draw_y), char, font=unicode_font, fill='black')
                        except:
                            draw.text((char_draw_x, char_draw_y), char, font=font, fill='black')
                    else:
                        # 普通字符用標準字型
                        draw.text((char_draw_x, char_draw_y), char, font=font, fill='black')
    
    def _draw_horizontal_text_on_image(self, draw: ImageDraw.ImageDraw, text: str, 
                                     x: int, y: int, width: int, height: int, 
                                     font: ImageFont.ImageFont):
        """在圖像上繪製水平文字（用於創建文字圖像）- 支持換行"""
        # 使用與主渲染相同的邏輯
        self._draw_horizontal_text(draw, text, x, y, width, height, font)
    
    def _draw_vertical_text_on_image(self, draw: ImageDraw.ImageDraw, text: str, 
                                   x: int, y: int, width: int, height: int, 
                                   font: ImageFont.ImageFont):
        """在圖像上繪製垂直文字（用於創建文字圖像）"""
        # 使用與主渲染相同的邏輯
        self._draw_vertical_text(draw, text, x, y, width, height, font)
    
    def _calculate_line_width(self, line: str, font: ImageFont.ImageFont, unicode_font: ImageFont.ImageFont) -> int:
        """
        計算一行文字的總寬度（考慮混合字型）
        """
        total_width = 0
        for char in line:
            if self.unicode_handler.is_special_unicode_char(char):
                total_width += self.unicode_handler.get_char_width(char, unicode_font)
            else:
                total_width += self.unicode_handler.get_char_width(char, font)
        return total_width
    
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