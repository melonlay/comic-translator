"""
Unicode Handler
Unicode處理器

專門負責Unicode字符的檢測和處理功能
"""

from PIL import ImageDraw, ImageFont


class UnicodeHandler:
    """Unicode字符處理器"""
    
    def __init__(self):
        """初始化Unicode處理器"""
        pass
    
    def is_special_unicode_char(self, char: str) -> bool:
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
            print(f"   🔍 檢測到特殊Unicode字符: '{char}' (U+{code:04X})")
        
        return is_special
    
    def is_punctuation_char(self, char: str) -> bool:
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
    
    def get_char_width(self, char: str, font: ImageFont.ImageFont) -> int:
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
    
    def draw_manual_vertical_dots(self, draw: ImageDraw.ImageDraw, x: int, y: int, font_size: int):
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