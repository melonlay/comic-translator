"""
Font Calculator
字體計算器

專門負責字體大小的計算功能
"""

from PIL import ImageFont
from .font_loader import FontLoader


class FontCalculator:
    """字體計算器"""
    
    def __init__(self, font_loader: FontLoader):
        """
        初始化字體計算器
        
        Args:
            font_loader: 字體載入器
        """
        self.font_loader = font_loader
    
    def calculate_font_size_enhanced(self, text: str, width: int, height: int, 
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
            font = self.font_loader.load_font(font_size)
            
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