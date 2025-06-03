"""
Prompt Manager
提示詞管理器

負責生成各種翻譯提示詞的原子化模組
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class PromptManager:
    """
    提示詞管理器
    Prompt Manager
    
    負責生成結構化翻譯提示詞
    """
    
    def __init__(self):
        """初始化提示詞管理器"""
        pass
    
    def create_visual_translation_prompt(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        創建包含圖片視覺分析的翻譯提示詞
        
        Args:
            texts: 待翻譯文字
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史
            
        Returns:
            str: 翻譯提示詞
        """
        # 準備歷史上下文
        history_context = self._build_history_context(translation_history)
        
        # 準備專有名詞
        terminology_context = self._build_terminology_context(terminology_dict)

        return f"""你是專業的日文漫畫翻譯專家和 OCR 校正專家。請分析提供的 OCR 識別文字，校正可能的錯誤，然後將正確的日文翻譯為繁體中文。

**重要：請同時分析提供的漫畫圖片，進行OCR校正和視覺特徵分析**

**嚴格規則：絕對不可刪除任何段落！**
- 必須為每個提供的 OCR 文字提供對應的校正和翻譯結果
- 即使 OCR 文字看起來有問題，也要嘗試理解並校正，不可跳過或刪除
- 輸出的翻譯數量必須與輸入的 OCR 文字數量完全一致

圖片分析要求：
1. **OCR 校正功能**：
   - 將提供的 OCR 識別文字與圖片中的實際文字進行對比
   - 識別可能的 OCR 錯誤（如相似字符混淆、缺字、多字等）
   - 校正錯誤的文字，確保準確理解原文含義
   - 常見 OCR 錯誤示例：
     * 「ロ」與「口」、「力」與「刀」、「ー」與「一」的混淆
     * 手寫字體可能導致的識別錯誤
     * 特殊字體、斜體文字的識別問題
   - **注意**：即使無法完全理解 OCR 文字，也要提供最合理的校正版本

2. **對話框背景分析**：
   - pure_white：純白色背景，邊緣清晰的對話框
   - textured：有漸變、陰影、紋理的對話框背景
   - transparent：透明或半透明的對話框

3. **字體大小估計**：
   - 根據圖片中文字的實際大小估計像素值（通常8-40像素）
   - 考慮文字與對話框的比例關係

翻譯和校正原則：
- **絕對禁止**：刪除任何輸入的文字段落！必須為每個輸入提供對應的輸出
- **首要任務**：校正 OCR 識別錯誤，確保理解正確的原文
- 保持漫畫對話的自然性和流暢性
- 維持角色的語調和個性
- 專有名詞必須保持一致性
- 考慮上下文連貫性

**關鍵翻譯邏輯**：
1. **檢查專有名詞字典**：查看字典中是否有該詞彙的翻譯
2. **敬語翻譯規則**：
   - 如果字典中有「人名(男性)」，則「人名さん」翻譯為「人名先生」
   - 如果字典中有「人名(女性)」，則「人名さん」翻譯為「人名小姐」
   - 例如：字典中「キクル(男性)」→「キクルさん」翻譯為「奇庫魯先生」
   - 例如：字典中「エノメ(女性)」→「エノメさん」翻譯為「艾諾梅小姐」
3. **新角色處理**：如果字典中沒有該角色，根據圖片和上下文判斷性別，然後正確翻譯敬語，並在new_terminology中記錄為「人名(性別)」

待處理的 OCR 識別文字：
{json.dumps(texts, ensure_ascii=False, indent=2)}
{terminology_context}
{history_context}

**重要約束：輸出的翻譯數量必須等於輸入文字數量 ({len(texts)} 個)**

請為每個文字提供：
1. **校正後的正確日文原文**（如果 OCR 有錯誤）
2. 準確的繁體中文翻譯（注意性別正確性）
3. 對話框類型判斷（pure_white/textured/transparent）
4. 估計的字體大小（像素值）
5. 發現的新專有名詞（格式：日文->中文，如果是人名請在中文後加(男性)或(女性)）

注意：在 "original" 欄位中請提供校正後的正確日文，而不是 OCR 的錯誤識別結果。

輸出必須是有效的JSON格式。"""
    
    def create_text_only_translation_prompt(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        創建純文字翻譯提示詞（不涉及圖片分析）
        
        Args:
            texts: 待翻譯文字
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史
            
        Returns:
            str: 翻譯提示詞
        """
        # 準備歷史上下文
        history_context = self._build_history_context(translation_history)
        
        # 準備專有名詞
        terminology_context = self._build_terminology_context(terminology_dict)

        return f"""你是專業的日文漫畫翻譯專家。請將提供的日文文字翻譯為繁體中文。

**嚴格規則：絕對不可刪除任何段落！**
- 必須為每個提供的文字提供對應的翻譯結果
- 輸出的翻譯數量必須與輸入的文字數量完全一致

翻譯原則：
- **絕對禁止**：刪除任何輸入的文字段落！必須為每個輸入提供對應的輸出
- 保持漫畫對話的自然性和流暢性
- 維持角色的語調和個性
- 專有名詞必須保持一致性
- 考慮上下文連貫性

**關鍵翻譯邏輯**：
1. **檢查專有名詞字典**：查看字典中是否有該詞彙的翻譯
2. **敬語翻譯規則**：
   - 如果字典中有「人名(男性)」，則「人名さん」翻譯為「人名先生」
   - 如果字典中有「人名(女性)」，則「人名さん」翻譯為「人名小姐」
   - 例如：字典中「キクル(男性)」→「キクルさん」翻譯為「奇庫魯先生」
   - 例如：字典中「エノメ(女性)」→「エノメさん」翻譯為「艾諾梅小姐」
3. **新角色處理**：如果字典中沒有該角色，根據上下文判斷性別，然後正確翻譯敬語，並在new_terminology中記錄為「人名(性別)」

待翻譯的文字：
{json.dumps(texts, ensure_ascii=False, indent=2)}
{terminology_context}
{history_context}

**重要約束：輸出的翻譯數量必須等於輸入文字數量 ({len(texts)} 個)**

請為每個文字提供：
1. 原始日文文字
2. 準確的繁體中文翻譯（注意性別正確性）
3. 對話框類型（預設為pure_white）
4. 估計的字體大小（預設為16像素）
5. 發現的新專有名詞（格式：日文->中文，如果是人名請在中文後加(男性)或(女性)）

輸出必須是有效的JSON格式。"""
    
    def _build_history_context(self, translation_history: List[Dict[str, str]] = None) -> str:
        """
        構建翻譯歷史上下文
        
        Args:
            translation_history: 翻譯歷史
            
        Returns:
            str: 歷史上下文字串
        """
        if not translation_history or len(translation_history) == 0:
            return ""
        
        recent_history = translation_history[-10:]  # 最近10條
        history_context = "\n\n前文翻譯參考：\n"
        for i, item in enumerate(recent_history, 1):
            history_context += f"{i}. 「{item.get('original', '')}」→「{item.get('translated', '')}」\n"
        
        return history_context
    
    def _build_terminology_context(self, terminology_dict: Dict[str, str] = None) -> str:
        """
        構建專有名詞上下文
        
        Args:
            terminology_dict: 專有名詞字典
            
        Returns:
            str: 專有名詞上下文字串
        """
        if not terminology_dict:
            return ""
        
        terminology_context = "\n\n專有名詞字典（必須使用一致翻譯）：\n"
        for jp, cn in terminology_dict.items():
            terminology_context += f"「{jp}」→「{cn}」\n"
        
        return terminology_context
    
    def get_response_schema(self) -> Dict[str, Any]:
        """
        獲取翻譯回應的JSON Schema
        
        Returns:
            Dict: JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "translations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "original": {"type": "string"},
                            "translated": {"type": "string"},
                            "text_direction": {
                                "type": "string",
                                "enum": ["horizontal", "vertical"],
                                "description": "文字排版方向：horizontal(橫書)或vertical(直書)"
                            },
                            "bubble_type": {
                                "type": "string", 
                                "enum": ["pure_white", "textured", "transparent"],
                                "description": "對話框類型：pure_white(純白)、textured(有紋理/漸變)或transparent(透明)"
                            },
                            "estimated_font_size": {
                                "type": "integer",
                                "description": "估計的原始字體大小(像素)"
                            }
                        },
                        "required": ["original", "translated", "text_direction", "bubble_type", "estimated_font_size"]
                    }
                },
                "new_terminology": {
                    "type": "array",
                    "description": "發現的新專有名詞列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "japanese": {"type": "string", "description": "日文原文"},
                            "chinese": {"type": "string", "description": "中文翻譯"}
                        },
                        "required": ["japanese", "chinese"]
                    }
                }
            },
            "required": ["translations", "new_terminology"]
        } 