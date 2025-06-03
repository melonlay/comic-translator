"""
Text Preprocessor
文字預處理器

專門負責文字內容的預處理功能
"""

import re


class TextPreprocessor:
    """文字預處理器"""
    
    def __init__(self):
        """初始化文字預處理器"""
        pass
    
    def preprocess_for_direction(self, text: str, text_direction: str) -> str:
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
        processed_text = self.normalize_ellipsis(text)
        
        # 如果是直書，需要特殊處理省略號
        if text_direction == 'vertical':
            processed_text = self.convert_ellipsis_for_vertical(processed_text)
        
        return processed_text
    
    def normalize_ellipsis(self, text: str) -> str:
        """
        統一省略號格式 - 中文省略號應為六個點（兩個省略號符號）
        
        Args:
            text: 原始文字
            
        Returns:
            str: 格式化後的文字
        """
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
    
    def convert_ellipsis_for_vertical(self, text: str) -> str:
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