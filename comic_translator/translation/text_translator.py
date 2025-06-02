"""
Text Translator
文字翻譯器

使用Gemini進行文字翻譯，支援歷史上下文
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
    
    使用Gemini進行智能翻譯，支援歷史上下文
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
            image_path: 圖片路徑，用於視覺分析
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return {'translated_texts': [], 'new_terminology': {}, 'success': False}
        
        print(f"🌐 開始翻譯 {len(texts)} 個文字...")
        if image_path:
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
                    "description": "發現的新專有名詞",
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
        
        prompt = self._create_enhanced_translation_prompt(texts, terminology_dict, translation_history, image_path)
        
        try:
            # 如果有圖片，使用圖片分析功能
            if image_path and Path(image_path).exists():
                result = self.gemini_client.generate_structured_content_with_image(
                    prompt, image_path, response_schema
                )
                print("✅ 使用圖片視覺分析進行翻譯")
            else:
                # 沒有圖片時使用純文字分析
                result = self.gemini_client.generate_structured_content(prompt, response_schema)
                print("⚠️ 未提供圖片，使用純文字分析")
            
            translations = result.get('translations', [])
            new_terminology = result.get('new_terminology', [])
            
            # 將 new_terminology 從數組格式轉換為字典格式
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
            
            print(f"✅ 翻譯完成: {len(translated_texts)} 個文字")
            
            return {
                'translated_texts': translated_texts,
                'new_terminology': terminology_dict,
                'success': True
            }
            
        except Exception as e:
            print(f"⚠️ Structured翻譯失敗，使用備用方法: {e}")
            # 回退到舊方法
            return self._fallback_translation(texts, terminology_dict, translation_history, image_path)
    
    def _create_enhanced_translation_prompt(self, texts: List[str], terminology_dict: Dict[str, str], 
                                          translation_history: List[Dict[str, str]] = None, 
                                          image_path: str = None) -> str:
        """
        創建增強的翻譯提示詞（包含排版和對話框分析）
        
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
        
        # 根據是否有圖片調整提示詞
        if image_path:
            visual_analysis_instruction = """
**重要：請同時分析提供的漫畫圖片，進行OCR校正和視覺特徵分析**

圖片分析要求：
1. **OCR 校正功能**：
   - 將提供的 OCR 識別文字與圖片中的實際文字進行對比
   - 識別可能的 OCR 錯誤（如相似字符混淆、缺字、多字等）
   - 校正錯誤的文字，確保準確理解原文含義
   - 常見 OCR 錯誤示例：
     * 「ロ」與「口」、「力」與「刀」、「ー」與「一」的混淆
     * 手寫字體可能導致的識別錯誤
     * 特殊字體、斜體文字的識別問題

2. **實際觀察文字排版**：
   - 仔細觀察每個文字區域的文字是橫向排列還是縱向排列
   - horizontal：文字從左到右水平排列
   - vertical：文字從上到下垂直排列

3. **對話框背景分析**：
   - pure_white：純白色背景，邊緣清晰的對話框
   - textured：有漸變、陰影、紋理的對話框背景
   - transparent：透明或半透明的對話框

4. **字體大小估計**：
   - 根據圖片中文字的實際大小估計像素值（通常8-40像素）
   - 考慮文字與對話框的比例關係

**重要：如果發現 OCR 錯誤，請在翻譯結果中使用校正後的正確文字**"""
        else:
            visual_analysis_instruction = """
**注意：由於沒有提供圖片，無法進行 OCR 校正，請根據文字內容和常見漫畫排版規律進行判斷**

推斷規則：
1. **文字排版方向**：
   - 短句、對話通常用 horizontal
   - 長段落、旁白通常用 vertical
   
2. **對話框類型**：
   - 對話文字通常用 pure_white
   - 旁白、思考文字可能用 textured
   
3. **字體大小**：
   - 對話文字通常 12-20 像素
   - 旁白文字通常 10-16 像素"""

        return f"""你是專業的日文漫畫翻譯專家和 OCR 校正專家。請分析提供的 OCR 識別文字，校正可能的錯誤，然後將正確的日文翻譯為繁體中文。

{visual_analysis_instruction}

翻譯和校正原則：
- **首要任務**：如果提供了圖片，請先校正 OCR 識別錯誤，確保理解正確的原文
- 保持漫畫對話的自然性和流暢性
- 維持角色的語調和個性
- 專有名詞必須保持一致性
- 考慮上下文連貫性

待處理的 OCR 識別文字：
{json.dumps(texts, ensure_ascii=False, indent=2)}
{terminology_context}
{history_context}

請為每個文字提供：
1. **校正後的正確日文原文**（如果 OCR 有錯誤）
2. 準確的繁體中文翻譯
3. 文字排版方向判斷（horizontal/vertical）
4. 對話框類型判斷（pure_white/textured/transparent）
5. 估計的字體大小（像素值）
6. 發現的新專有名詞

注意：在 "original" 欄位中請提供校正後的正確日文，而不是 OCR 的錯誤識別結果。

輸出必須是有效的JSON格式。"""
    
    def translate_texts(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str] = None,
        image_path: str = None
    ) -> Dict[str, Any]:
        """
        翻譯文字列表（不使用歷史上下文）
        
        Args:
            texts: 要翻譯的文字列表
            terminology_dict: 專有名詞字典
            image_path: 圖片路徑，用於視覺分析
            
        Returns:
            Dict: 翻譯結果
        """
        return self.translate_texts_with_history(texts, terminology_dict, [], image_path)
    
    def _fallback_translation(self, texts: List[str], terminology_dict: Dict[str, str], 
                             translation_history: List[Dict[str, str]] = None, 
                             image_path: str = None) -> Dict[str, Any]:
        """
        備用翻譯方法（支援圖片 OCR 校正）
        
        Args:
            texts: 要翻譯的文字列表
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史上下文
            image_path: 圖片路徑，用於 OCR 校正
            
        Returns:
            Dict: 翻譯結果
        """
        if not texts:
            return {
                'translated_texts': [],
                'new_terminology': [],
                'success': False
            }
        
        print(f"🔄 開始翻譯 {len(texts)} 個文字")
        if translation_history:
            print(f"📚 使用 {len(translation_history)} 條歷史翻譯作為上下文")
        if image_path:
            print(f"📷 使用圖片進行 OCR 校正: {Path(image_path).name}")
        
        start_time = time.time()
        
        try:
            # 準備翻譯提示詞，包含歷史上下文
            prompt = self._prepare_translation_prompt_with_history(
                texts, terminology_dict or {}, translation_history or [], image_path
            )
            
            # 呼叫Gemini API
            self.api_call_count += 1
            print(f"💰 API 呼叫 #{self.api_call_count} - 模型: {self.gemini_client.model_name}")
            
            # 根據是否有圖片選擇 API 方法
            if image_path and Path(image_path).exists():
                response = self.gemini_client.generate_content_with_image(prompt, image_path)
                print("✅ 使用圖片進行 OCR 校正翻譯")
            else:
                response = self.gemini_client.generate_content(prompt)
                print("⚠️ 使用純文字翻譯（無 OCR 校正）")
            
            if not response:
                print("❌ API 回應為空")
                return {
                    'translated_texts': [],
                    'new_terminology': [],
                    'success': False,
                    'error': 'Empty API response'
                }
            
            # 解析翻譯結果
            result = self._parse_translation_response_with_terminology(response, texts)
            
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
                'new_terminology': {},
                'success': False,
                'error': str(e)
            }
    
    def _prepare_translation_prompt_with_history(
        self, 
        texts: List[str], 
        terminology_dict: Dict[str, str],
        translation_history: List[Dict[str, str]],
        image_path: str = None
    ) -> str:
        """
        準備包含歷史上下文的翻譯提示詞（支援 OCR 校正）
        
        Args:
            texts: 要翻譯的文字
            terminology_dict: 專有名詞字典
            translation_history: 翻譯歷史
            image_path: 圖片路徑
            
        Returns:
            str: 翻譯提示詞
        """
        
        # 根據是否有圖片調整基本提示詞
        if image_path:
            base_prompt = """你是一個專業的日文漫畫翻譯師和 OCR 校正專家，擅長將日文漫畫對話翻譯成繁體中文。

**重要：OCR 校正功能**
請首先觀察提供的漫畫圖片，對比 OCR 識別的文字與圖片中的實際文字：
1. 識別可能的 OCR 錯誤（如相似字符混淆、缺字、多字等）
2. 校正錯誤的文字，確保準確理解原文含義
3. 常見 OCR 錯誤：「ロ」與「口」、「力」與「刀」、「ー」與「一」的混淆等

翻譯原則：
1. **首要任務**：校正 OCR 識別錯誤，確保理解正確的原文
2. 保持漫畫對話的自然語調和情感
3. 使用台灣常用的繁體中文表達方式
4. 保留角色的說話特色和個性
5. 適當處理擬聲詞和感嘆詞
6. 確保翻譯符合漫畫的語境和氛圍
7. 發現並標記新的專有名詞（人名、地名、特殊術語等）

輸出格式：
請按照以下JSON格式輸出（注意：在 "original" 欄位中請提供校正後的正確日文）：
{
  "translated_texts": [
    {
      "original": "校正後的正確日文原文",
      "translated": "翻譯結果"
    }
  ],
  "new_terminology": [
    {
      "japanese": "日文原文",
      "chinese": "中文翻譯"
    }
  ]
}"""
        else:
            base_prompt = """你是一個專業的日文漫畫翻譯師，擅長將日文漫畫對話翻譯成繁體中文。

翻譯原則：
1. 保持漫畫對話的自然語調和情感
2. 使用台灣常用的繁體中文表達方式
3. 保留角色的說話特色和個性
4. 適當處理擬聲詞和感嘆詞
5. 確保翻譯符合漫畫的語境和氛圍
6. 發現並標記新的專有名詞（人名、地名、特殊術語等）

輸出格式：
請按照以下JSON格式輸出：
{
  "translated_texts": [
    {
      "original": "原文",
      "translated": "翻譯結果"
    }
  ],
  "new_terminology": [
    {
      "japanese": "日文原文",
      "chinese": "中文翻譯"
    }
  ]
}"""

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
        if image_path:
            texts_section = "\n\n待校正和翻譯的 OCR 識別文字：\n"
        else:
            texts_section = "\n\n待翻譯文字：\n"
            
        for i, text in enumerate(texts, 1):
            texts_section += f"{i}. {text}\n"
        
        base_prompt += texts_section
        
        base_prompt += "\n\n請開始校正和翻譯："
        
        return base_prompt
    
    def _parse_translation_response_with_terminology(self, response: str, original_texts: List[str]) -> Dict[str, Any]:
        """
        解析包含專有名詞的翻譯回應
        
        Args:
            response: API回應
            original_texts: 原始文字列表
            
        Returns:
            Dict: 解析後的結果
        """
        try:
            import json
            import re
            
            # 嘗試提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    
                    # 驗證結果格式
                    if 'translated_texts' in result:
                        translated_texts = result['translated_texts']
                        new_terminology = result.get('new_terminology', [])
                        
                        # 確保翻譯數量匹配
                        if len(translated_texts) == len(original_texts):
                            return {
                                'translated_texts': translated_texts,
                                'new_terminology': new_terminology
                            }
                        else:
                            print(f"⚠️ 翻譯數量不匹配: 期望 {len(original_texts)}, 得到 {len(translated_texts)}")
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析失敗: {e}")
                    
            # 如果JSON解析失敗，嘗試簡單文字解析
            print("⚠️ 使用備用解析方法")
            return self._fallback_parse_response(response, original_texts)
            
        except Exception as e:
            print(f"⚠️ 解析回應失敗: {e}")
            return self._fallback_parse_response(response, original_texts)
    
    def _fallback_parse_response(self, response: str, original_texts: List[str]) -> Dict[str, Any]:
        """
        備用解析方法
        
        Args:
            response: API回應
            original_texts: 原始文字列表
            
        Returns:
            Dict: 解析後的結果
        """
        lines = response.strip().split('\n')
        translated_texts = []
        
        # 簡單的行對行匹配
        translation_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#') and not line.startswith('```')]
        
        for i, original in enumerate(original_texts):
            if i < len(translation_lines):
                translated = translation_lines[i]
                # 清理翻譯文字
                translated = re.sub(r'^\d+[\.\)]\s*', '', translated)  # 移除開頭的數字
                translated = translated.strip()
            else:
                translated = original  # 如果沒有對應翻譯，使用原文
            
            translated_texts.append({
                'original': original,
                'translated': translated
            })
        
        return {
            'translated_texts': translated_texts,
            'new_terminology': []
        }
    
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
    
    def translate_single(self, text: str, terminology_dict: Dict[str, str] = None) -> Dict[str, Any]:
        """
        翻譯單個文字
        
        Args:
            text: 要翻譯的文字
            terminology_dict: 專有名詞字典
            
        Returns:
            Dict: 翻譯結果
        """
        result = self.translate_texts([text], terminology_dict)
        
        if result['success'] and result['translated_texts']:
            return {
                'original': result['translated_texts'][0]['original'],
                'translated': result['translated_texts'][0]['translated'],
                'success': True
            }
        else:
            return {
                'original': text,
                'translated': text,
                'success': False
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