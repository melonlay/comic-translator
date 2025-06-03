"""
Font Loader
字體載入器

專門負責字體的載入功能
"""

from PIL import ImageFont
from typing import Optional


class FontLoader:
    """字體載入器"""
    
    def __init__(self):
        """初始化字體載入器"""
        pass
    
    def load_font(self, size: int = 20) -> ImageFont.ImageFont:
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
    
    def load_unicode_font(self, size: int = 20) -> ImageFont.ImageFont:
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
        return self.load_font(size) 