"""
Text Translator
文字翻譯器

使用Gemini進行文字翻譯，支援歷史上下文和圖片分析
"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from ..utils.gemini_client import GeminiClient
from pathlib import Path


class TextTranslator:
    """
    文字翻譯器
    Text Translator
    
    使用Gemini進行智能翻譯，支援歷史上下文和圖片分析
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化翻譯器
        
        Args:
            gemini_client: Gemini客戶端實例
        """
        self.gemini_client = gemini_client
        self.api_call_count = 0
        self.translation_cache = {}
        
        print("✅ 文字翻譯器初始化完成")
    
    def translate_texts_with_history(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        translation_history: List[Dict[str, str]] = None,
        image_path: str = None
    ) -> Dict[str, Any]:
        """
        翻譯文字列表（使用歷史上下文和圖片分析）
        
        Args:
            texts: 待翻譯的文字列表
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            image_path: 圖片路徑，用於視覺分析（必須提供）
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return {'translated_texts': [], 'new_terminology': {}, 'success': False}
        
        if not image_path or not Path(image_path).exists():
            print("❌ 所有翻譯都必須提供有效的圖片路徑")
            return {'translated_texts': [], 'new_terminology': {}, 'success': False}
        
        print(f"🌐 開始翻譯 {len(texts)} 個文字...")
        print(f"📷 使用圖片分析: {Path(image_path).name}")
        
        # 使用structured output進行翻譯
        response_schema = {
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
        
        prompt = self._create_translation_prompt(texts, terminology_dict, translation_history, image_path)
        
        try:
            result = self.gemini_client.generate_structured_content_with_image(
                prompt, image_path, response_schema
            )
            print("✅ 使用圖片視覺分析進行翻譯")
            
            translations = result.get('translations', [])
            new_terminology = result.get('new_terminology', [])
            
            # 將new_terminology從array轉換為dict格式
            terminology_dict = {}
            for term in new_terminology:
                if isinstance(term, dict) and 'japanese' in term and 'chinese' in term:
                    terminology_dict[term['japanese']] = term['chinese']
            
            # 轉換為標準格式
            translated_texts = []
            for translation in translations:
                translated_texts.append({
                    'original': translation['original'],
                    'translated': translation['translated'],
                    'text_direction': translation['text_direction'],
                    'bubble_type': translation['bubble_type'],
                    'estimated_font_size': translation['estimated_font_size']
                })
            
            # 驗證輸出數量
            if len(translated_texts) != len(texts):
                print(f"⚠️ 翻譯數量不匹配: 輸入 {len(texts)} 個，輸出 {len(translated_texts)} 個")
                print("📝 AI可能刪除了某些段落，將使用簡單翻譯方法")
                return self._simple_translation(texts, terminology_dict, translation_history, image_path)
            
            print(f"✅ 翻譯完成: {len(translated_texts)} 個文字")
            
            return {
                'translated_texts': translated_texts,
                'new_terminology': terminology_dict,
                'success': True
            }
            
        except Exception as e:
            print(f"⚠️ Structured翻譯失敗，使用簡單方法: {e}")
            return self._simple_translation(texts, terminology_dict, translation_history, image_path)
    
    def _create_translation_prompt(self, texts: List[str], terminology_dict: Dict[str, str], 
                                  translation_history: List[Dict[str, str]] = None, 
                                  image_path: str = None) -> str:
        """
        創建翻譯提示詞
        
        Args:
            texts: 待翻譯文字
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史
            image_path: 圖片路徑
            
        Returns:
            str: 翻譯提示詞
        """
        # 準備歷史上下文
        history_context = ""
        if translation_history and len(translation_history) > 0:
            recent_history = translation_history[-10:]  # 最近10條
            history_context = "\n\n前文翻譯參考：\n"
            for i, item in enumerate(recent_history, 1):
                history_context += f"{i}. 「{item.get('original', '')}」→「{item.get('translated', '')}」\n"
        
        # 準備專有名詞
        terminology_context = ""
        if terminology_dict:
            terminology_context = "\n\n專有名詞字典（必須使用一致翻譯）：\n"
            for jp, cn in terminology_dict.items():
                terminology_context += f"「{jp}」→「{cn}」\n"

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

2. **實際觀察文字排版**：
   - 仔細觀察每個文字區域的文字是橫向排列還是縱向排列
   - horizontal：文字從左到右水平排列
   - vertical：文字從上到下垂直排列
   
   **漫畫中常見的排版規律**：
   - **對話框內的長句子**：通常是 vertical（直書），文字從上到下、從右到左排列
   - **短句感嘆詞**：可能是 horizontal（橫書），特別是很短的詞語
   - **旁白說明文字**：通常是 vertical（直書）
   - **音效文字**：通常是 horizontal（橫書），但要看實際排列方向
   - **標題或大字**：可能是 horizontal（橫書）
   
   **判斷技巧**：
   - 觀察文字在對話框中的實際排列方向，而不是對話框的形狀
   - 長句子（超過5個字符）在漫畫中通常採用 vertical（直書）
   - 如果文字看起來是一行一行從上到下排列，就是 vertical
   - 如果文字看起來是從左到右在同一水平線上，就是 horizontal

3. **對話框背景分析**：
   - pure_white：純白色背景，邊緣清晰的對話框
   - textured：有漸變、陰影、紋理的對話框背景
   - transparent：透明或半透明的對話框

4. **字體大小估計**：
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
3. 文字排版方向判斷（horizontal/vertical）
4. 對話框類型判斷（pure_white/textured/transparent）
5. 估計的字體大小（像素值）
6. 發現的新專有名詞（格式：日文->中文，如果是人名請在中文後加(男性)或(女性)）

注意：在 "original" 欄位中請提供校正後的正確日文，而不是 OCR 的錯誤識別結果。

輸出必須是有效的JSON格式。"""
    
    def _simple_translation(self, texts: List[str], terminology_dict: Dict[str, str], 
                           translation_history: List[Dict[str, str]] = None, 
                           image_path: str = None) -> Dict[str, Any]:
        """
        簡單翻譯方法（當structured方法失敗時使用）
        
        Args:
            texts: 要翻譯的文字列表
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            image_path: 圖片路徑
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return {
                'translated_texts': [],
                'new_terminology': [],
                'success': False
            }
        
        print(f"🔄 開始簡單翻譯 {len(texts)} 個文字")
        if translation_history:
            print(f"📚 使用 {len(translation_history)} 條歷史翻譯作為上下文")
        print(f"📷 使用圖片進行 OCR 校正: {Path(image_path).name}")
        
        start_time = time.time()
        
        try:
            # 準備翻譯提示詞，包含歷史上下文
            prompt = self._create_simple_prompt(texts, terminology_dict or {}, translation_history or [], image_path)
            
            # 呼叫Gemini API
            self.api_call_count += 1
            print(f"💰 API 呼叫 #{self.api_call_count} - 模型: {self.gemini_client.model_name}")
            
            response = self.gemini_client.generate_content_with_image(prompt, image_path)
            print("✅ 使用圖片進行 OCR 校正翻譯")
            
            if not response:
                print("❌ API 回應為空")
                return {
                    'translated_texts': self._create_fallback_translations(texts),
                    'new_terminology': [],
                    'success': False,
                    'error': 'Empty API response'
                }
            
            # 解析翻譯結果
            result = self._parse_simple_response(response, texts)
            
            processing_time = time.time() - start_time
            
            print(f"✅ 翻譯完成，耗時: {processing_time:.2f}秒")
            print(f"📝 成功翻譯: {len(result['translated_texts'])}/{len(texts)}")
            print(f"🆕 發現新專有名詞: {len(result['new_terminology'])}")
            
            return {
                'translated_texts': result['translated_texts'],
                'new_terminology': result['new_terminology'],
                'success': True
            }
            
        except Exception as e:
            print(f"❌ 翻譯過程出錯: {e}")
            return {
                'translated_texts': self._create_fallback_translations(texts),
                'new_terminology': [],
                'success': False,
                'error': str(e)
            }
    
    def _create_simple_prompt(self, texts: List[str], terminology_dict: Dict[str, str],
                             translation_history: List[Dict[str, str]], image_path: str) -> str:
        """
        創建簡單翻譯提示詞
        
        Args:
            texts: 要翻譯的文字
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史
            image_path: 圖片路徑
            
        Returns:
            str: 翻譯提示詞
        """
        base_prompt = """你是一個專業的日文漫畫翻譯師和 OCR 校正專家，擅長將日文漫畫對話翻譯成繁體中文。

**嚴格規則：絕對不可刪除任何段落！**
- 必須為每個提供的 OCR 文字提供對應的校正和翻譯結果
- 即使 OCR 文字看起來有問題，也要嘗試理解並校正，不可跳過或刪除
- 輸出的翻譯數量必須與輸入的 OCR 文字數量完全一致

**重要：OCR 校正功能**
請首先觀察提供的漫畫圖片，對比 OCR 識別的文字與圖片中的實際文字：
1. 識別可能的 OCR 錯誤（如相似字符混淆、缺字、多字等）
2. 校正錯誤的文字，確保準確理解原文含義
3. 常見 OCR 錯誤：「ロ」與「口」、「力」與「刀」、「ー」與「一」的混淆等
4. **注意**：即使無法完全理解 OCR 文字，也要提供最合理的校正版本

**文字排版方向判斷**：
- 仔細觀察圖片中每個文字區域的實際排列方向
- **漫畫常見規律**：
  * 對話框內的長句子：通常是直書（從上到下排列）
  * 短句感嘆詞：可能是橫書
  * 音效文字：通常是橫書，但要看實際方向
- **判斷方法**：
  * 長句子（超過5個字）在漫畫中通常是直書
  * 觀察文字實際排列，不要被對話框形狀誤導
  * 一行一行從上到下 = 直書
  * 從左到右在同一水平線 = 橫書

**專有名詞處理**：
- 檢查字典中是否有該詞彙的翻譯
- 如果字典中有「人名(男性)」，則「人名さん」翻譯為「人名先生」
- 如果字典中有「人名(女性)」，則「人名さん」翻譯為「人名小姐」
- 新發現的人名請在中文後標記(男性)或(女性)

翻譯原則：
1. **絕對禁止**：刪除任何輸入的文字段落！必須為每個輸入提供對應的輸出
2. **首要任務**：校正 OCR 識別錯誤，確保理解正確的原文
3. 保持漫畫對話的自然語調和情感
4. 使用台灣常用的繁體中文表達方式
5. 保留角色的說話特色和個性
6. 適當處理擬聲詞和感嘆詞
7. 確保翻譯符合漫畫的語境和氛圍
8. 發現並標記新的專有名詞（人名、地名、特殊術語等）

輸出格式：
請按照以下格式輸出（注意：在第一行請提供校正後的正確日文）：
1. 校正後的正確日文 → 翻譯結果
2. 校正後的正確日文 → 翻譯結果
...

如果發現新專有名詞，請在最後列出：
新專有名詞：
- 日文原文: 中文翻譯
- 日文原文: 中文翻譯"""

        # 添加專有名詞字典
        if terminology_dict:
            terminology_section = "\n\n現有專有名詞字典：\n"
            for jp_term, zh_term in terminology_dict.items():
                terminology_section += f"- {jp_term}: {zh_term}\n"
            base_prompt += terminology_section
        
        # 添加翻譯歷史上下文
        if translation_history:
            history_section = "\n\n翻譯歷史上下文（用於保持角色和劇情的一致性）：\n"
            
            # 只顯示最近的20條歷史記錄，避免提示詞過長
            recent_history = translation_history[-20:] if len(translation_history) > 20 else translation_history
            
            for i, hist_item in enumerate(recent_history, 1):
                if isinstance(hist_item, dict) and 'original' in hist_item and 'translated' in hist_item:
                    history_section += f"{i}. {hist_item['original']} → {hist_item['translated']}\n"
            
            history_section += "\n請參考以上翻譯歷史，保持角色名稱、說話風格和劇情的一致性。"
            base_prompt += history_section
        
        # 添加待翻譯文字
        texts_section = f"\n\n待校正和翻譯的 OCR 識別文字（共 {len(texts)} 個，必須全部處理）：\n"
        for i, text in enumerate(texts, 1):
            texts_section += f"{i}. {text}\n"
        
        base_prompt += texts_section
        base_prompt += f"\n\n**重要提醒：必須輸出 {len(texts)} 個翻譯結果，絕對不可少於這個數量！**\n\n請開始校正和翻譯："
        
        return base_prompt
    
    def _parse_simple_response(self, response: str, original_texts: List[str]) -> Dict[str, Any]:
        """
        解析簡單翻譯回應
        
        Args:
            response: API回應
            original_texts: 原始文字列表
            
        Returns:
            Dict: 解析後的結果
        """
        lines = response.strip().split('\n')
        translated_texts = []
        new_terminology_list = []
        
        # 查找翻譯行和新專有名詞
        in_terminology_section = False
        translation_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '新專有名詞' in line or 'new terminology' in line.lower():
                in_terminology_section = True
                continue
            
            if in_terminology_section:
                # 解析專有名詞
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) == 2:
                        jp_term = parts[0].strip().lstrip('- ')
                        cn_term = parts[1].strip()
                        if jp_term and cn_term:
                            new_terminology_list.append({
                                'japanese': jp_term,
                                'chinese': cn_term
                            })
            else:
                # 解析翻譯行
                if '→' in line:
                    translation_lines.append(line)
                elif re.match(r'^\d+\.', line):
                    translation_lines.append(line)
        
        # 轉換new_terminology為dict格式
        new_terminology = {}
        for term in new_terminology_list:
            new_terminology[term['japanese']] = term['chinese']
        
        print(f"🔍 簡單解析: 找到 {len(translation_lines)} 行翻譯，需要 {len(original_texts)} 個結果")
        
        for i, original in enumerate(original_texts):
            if i < len(translation_lines):
                line = translation_lines[i]
                # 解析翻譯行
                if '→' in line:
                    parts = line.split('→', 1)
                    if len(parts) == 2:
                        corrected_original = parts[0].strip()
                        # 移除數字開頭
                        corrected_original = re.sub(r'^\d+[\.\)]\s*', '', corrected_original)
                        translated = parts[1].strip()
                    else:
                        corrected_original = original
                        translated = line.strip()
                else:
                    # 移除數字開頭
                    translated = re.sub(r'^\d+[\.\)]\s*', '', line)
                    corrected_original = original
                
                # 如果翻譯結果為空或太短，使用原文
                if not translated or len(translated) < 1:
                    translated = original
                    corrected_original = original
            else:
                # 如果沒有對應翻譯，使用原文
                translated = original
                corrected_original = original
                print(f"⚠️ 第 {i+1} 個文字沒有找到翻譯，使用原文: {original}")
            
            translated_texts.append({
                'original': corrected_original,
                'translated': translated,
                'text_direction': 'horizontal',
                'bubble_type': 'pure_white',
                'estimated_font_size': 16
            })
        
        print(f"✅ 簡單解析完成: {len(translated_texts)} 個結果")
        
        return {
            'translated_texts': translated_texts,
            'new_terminology': new_terminology
        }
    
    def _create_fallback_translations(self, texts: List[str]) -> List[Dict[str, str]]:
        """
        創建備用翻譯結果（當翻譯失敗時使用）
        
        Args:
            texts: 原始文字列表
            
        Returns:
            List[Dict]: 備用翻譯結果
        """
        return [
            {
                'original': text,
                'translated': text,
                'text_direction': 'horizontal',
                'bubble_type': 'pure_white',
                'estimated_font_size': 16
            }
            for text in texts
        ]
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """
        獲取翻譯統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        return {
            'total_api_calls': self.api_call_count,
            'model_used': self.gemini_client.model,
            'cache_size': len(self.translation_cache)
        } 