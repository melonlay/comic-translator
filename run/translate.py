#!/usr/bin/env python3
"""
漫畫翻譯器 - 翻譯執行檔案
Comic Translator - Translation Runner

整合五階段翻譯流程：
1. 文字檢測 (Text Detection)
2. 文字識別 (OCR)  
3. 文字重排 (Text Reordering)
4. 文字翻譯 (Translation)
5. 結果輸出 (Output)

用法:
    python run/translate.py <image_path>               # 單張圖片
    python run/translate.py test_images/ --batch      # 批量處理
"""

import sys
import os
from pathlib import Path
import argparse
import datetime

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from comic_translator.detection import ComicTextDetector
from comic_translator.extraction import MangaOCRExtractor  
from comic_translator.translation import TextReorder, TextTranslator
from comic_translator.utils import GeminiClient
import json


class ComicTranslator:
    """漫畫翻譯器主類"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化翻譯器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        
        # 創建各階段的輸出目錄
        self.stage1_dir = self.output_dir / "stage1_detection"
        self.stage2_dir = self.output_dir / "stage2_ocr"
        self.stage3_dir = self.output_dir / "stage3_reorder"
        self.stage4_dir = self.output_dir / "stage4_translate"
        
        # 確保所有輸出目錄存在
        self.output_dir.mkdir(exist_ok=True)
        self.stage1_dir.mkdir(exist_ok=True)
        self.stage2_dir.mkdir(exist_ok=True)
        self.stage3_dir.mkdir(exist_ok=True)
        self.stage4_dir.mkdir(exist_ok=True)
        
        # 初始化各階段組件
        print("🔧 初始化組件...")
        self.detector = ComicTextDetector()
        self.ocr = MangaOCRExtractor()
        
        # 初始化Gemini客戶端和翻譯器
        self.gemini_client = GeminiClient()
        self.reorder = TextReorder(self.gemini_client)
        self.translator = TextTranslator(self.gemini_client)
        
        # 載入terminology字典
        self.terminology_dict = self._load_terminology_dict()
        
        print(f"✅ 漫畫翻譯器初始化完成")
        print(f"📁 輸出目錄: {self.output_dir}")
        print(f"🔍 Stage1 目錄: {self.stage1_dir}")
        print(f"📝 Stage2 目錄: {self.stage2_dir}")
        print(f"🔄 Stage3 目錄: {self.stage3_dir}")
        print(f"🌏 Stage4 目錄: {self.stage4_dir}")
        print(f"📚 專有名詞: {len(self.terminology_dict)} 個詞彙")
    
    def _load_terminology_dict(self) -> dict:
        """載入專有名詞字典"""
        terminology_file = Path("terminology_dict.json")
        
        if terminology_file.exists():
            try:
                with open(terminology_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    terminology = data.get('ja_to_zh', {})
                    print(f"📚 載入專有名詞字典: {len(terminology)} 個詞彙")
                    return terminology
            except Exception as e:
                print(f"⚠️ 載入專有名詞字典失敗: {e}")
                return {}
        else:
            print("⚠️ 專有名詞字典不存在: terminology_dict.json")
            return {}
    
    def _save_terminology_dict(self, new_terminology: dict):
        """保存新的專有名詞到字典"""
        if not new_terminology:
            return
        
        terminology_file = Path("terminology_dict.json")
        
        try:
            # 讀取現有字典
            current_data = {}
            if terminology_file.exists():
                with open(terminology_file, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            
            # 獲取現有的專有名詞字典
            terminology = current_data.get('ja_to_zh', {})
            
            added_count = 0
            updated_count = 0
            
            # 處理新的專有名詞
            for jp_term, cn_term in new_terminology.items():
                if not jp_term or not cn_term:
                    continue
                
                if jp_term in terminology:
                    if terminology[jp_term] != cn_term:
                        print(f"🔄 更新專有名詞: {jp_term}")
                        print(f"   舊: {terminology[jp_term]}")
                        print(f"   新: {cn_term}")
                        terminology[jp_term] = cn_term
                        updated_count += 1
                else:
                    print(f"📝 新增專有名詞: {jp_term} → {cn_term}")
                    terminology[jp_term] = cn_term
                    added_count += 1
            
            if added_count > 0 or updated_count > 0:
                # 更新數據結構
                current_data['ja_to_zh'] = terminology
                current_data.setdefault('metadata', {})
                current_data['metadata']['updated_at'] = datetime.datetime.now().isoformat()
                current_data['metadata']['total_terms'] = len(terminology)
                current_data['metadata']['version'] = '1.0'
                
                # 保存文件
                with open(terminology_file, 'w', encoding='utf-8') as f:
                    json.dump(current_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 專有名詞字典已更新: +{added_count} 新增, {updated_count} 更新")
                
                # 更新內存中的字典
                self.terminology_dict = terminology
                
        except Exception as e:
            print(f"⚠️ 保存專有名詞字典失敗: {e}")
    
    def translate_image(self, image_path: str) -> bool:
        """
        翻譯單張圖片
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            bool: 翻譯是否成功
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            print(f"❌ 圖片不存在: {image_path}")
            return False
        
        print(f"\n🎨 開始翻譯圖片: {image_path.name}")
        print("=" * 70)
        
        try:
            # 階段1: 文字檢測
            print("🔍 階段1: 文字檢測")
            stage1_result = self._stage1_detection(image_path)
            if not stage1_result:
                return False
            
            # 階段2: 文字識別  
            print("📝 階段2: 文字識別")
            stage2_result = self._stage2_ocr(image_path, stage1_result)
            if not stage2_result:
                return False
            
            # 階段3: 文字重排
            print("🔄 階段3: 文字重排")
            stage3_result = self._stage3_reorder(image_path, stage2_result)
            if not stage3_result:
                return False
            
            # 階段4: 文字翻譯
            print("🌏 階段4: 文字翻譯")
            stage4_result = self._stage4_translate(image_path, stage3_result)
            if not stage4_result:
                return False
            
            print(f"✅ 翻譯完成: {image_path.name}")
            print(f"📄 結果保存在: {self.output_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 翻譯過程出錯: {e}")
            return False
    
    def batch_translate_folder(self, folder_path: str) -> list:
        """
        批量翻譯資料夾中的圖片
        
        Args:
            folder_path: 包含圖片的資料夾路徑
            
        Returns:
            list: 成功翻譯的圖片路徑列表
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            print(f"❌ 資料夾不存在: {folder_path}")
            return []
        
        # 獲取所有圖片檔案
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
        
        image_files.sort(key=lambda x: x.name.lower())
        
        print(f"\n📁 批量翻譯資料夾: {folder_path}")
        print("=" * 70)
        print(f"🖼️ 找到 {len(image_files)} 個圖片檔案")
        
        translated_files = []
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n🎨 翻譯第 {i}/{len(image_files)} 張: {image_file.name}")
            
            success = self.translate_image(str(image_file))
            if success:
                translated_files.append(str(image_file))
                print(f"✅ 翻譯成功")
            else:
                print(f"⚠️ 翻譯失敗")
        
        print(f"\n🎉 批量翻譯完成: {len(translated_files)}/{len(image_files)} 成功")
        return translated_files
    
    def _stage1_detection(self, image_path: Path) -> dict:
        """階段1: 文字檢測"""
        result = self.detector.detect_with_metadata(str(image_path))
        
        if result and result.get('text_boxes'):
            # 保存結果
            output_file = self.stage1_dir / f"{image_path.stem}_stage1_detection.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 檢測到 {result['total_boxes']} 個文字區域")
            print(f"   💾 結果保存: {output_file.name}")
            return result
        else:
            print("   ❌ 文字檢測失敗")
            return None
    
    def _stage2_ocr(self, image_path: Path, stage1_result: dict) -> dict:
        """階段2: 文字識別"""
        result_data = self.ocr.extract_from_boxes(str(image_path), stage1_result['text_boxes'])
        
        result = {
            'extracted_texts': result_data,
            'total_texts': len(result_data),
            'source_image': str(image_path)
        }
        
        if result and result.get('extracted_texts'):
            # 保存結果
            output_file = self.stage2_dir / f"{image_path.stem}_stage2_ocr.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 識別到 {len(result['extracted_texts'])} 段文字")
            print(f"   💾 結果保存: {output_file.name}")
            return result
        else:
            print("   ❌ 文字識別失敗")
            return None
    
    def _stage3_reorder(self, image_path: Path, stage2_result: dict) -> dict:
        """階段3: 文字重排"""
        reordered_texts = self.reorder.reorder_texts_with_image(str(image_path), stage2_result['extracted_texts'])
        
        result = {
            'reordered_texts': reordered_texts,
            'total_texts': len(reordered_texts),
            'source_image': str(image_path)
        }
        
        if result and result.get('reordered_texts'):
            # 保存結果
            output_file = self.stage3_dir / f"{image_path.stem}_stage3_reorder.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 重排完成 {len(result['reordered_texts'])} 段文字")
            print(f"   💾 結果保存: {output_file.name}")
            return result
        else:
            print("   ❌ 文字重排失敗")
            return None
    
    def _stage4_translate(self, image_path: Path, stage3_result: dict) -> dict:
        """階段4: 文字翻譯"""
        reordered_texts = stage3_result['reordered_texts']
        
        # 準備文字列表和對應的bbox信息
        texts_to_translate = []
        bbox_mapping = []
        
        for item in reordered_texts:
            if isinstance(item, dict):
                text = item.get('text', '')
                bbox = item.get('bbox', [])
                if text and bbox:
                    texts_to_translate.append(text)
                    bbox_mapping.append(bbox)
            elif isinstance(item, str):
                texts_to_translate.append(item)
                bbox_mapping.append([0, 0, 100, 50])  # 默認bbox
        
        if not texts_to_translate:
            print("   ⚠️ 沒有找到需要翻譯的文字")
            return None
        
        # 執行翻譯（傳遞terminology和圖片路徑）
        translation_result = self.translator.translate_texts_with_history(
            texts_to_translate,
            terminology_dict=self.terminology_dict,
            translation_history=None,  # 可以後續添加歷史支持
            image_path=str(image_path)
        )
        
        if not translation_result or not translation_result.get('translated_texts'):
            print("   ❌ 翻譯失敗")
            return None
        
        # 合併翻譯結果與bbox信息
        translated_texts = []
        translations = translation_result['translated_texts']
        
        for i, translation_item in enumerate(translations):
            # 確保有對應的bbox
            bbox = bbox_mapping[i] if i < len(bbox_mapping) else [0, 0, 100, 50]
            
            translated_item = {
                'original': translation_item.get('original', ''),
                'translated': translation_item.get('translated', ''),
                'bbox': bbox,
                'text_direction': translation_item.get('text_direction', 'horizontal'),
                'bubble_type': translation_item.get('bubble_type', 'pure_white'),
                'estimated_font_size': translation_item.get('estimated_font_size', 16)
            }
            translated_texts.append(translated_item)
        
        # 構建完整結果
        result = {
            'translated_texts': translated_texts,
            'new_terminology': translation_result.get('new_terminology', {}),
            'total_texts': len(translated_texts),
            'source_image': str(image_path),
            'success': True
        }
        
        # 保存新發現的專有名詞
        if translation_result.get('new_terminology'):
            self._save_terminology_dict(translation_result['new_terminology'])
        
        # 保存結果
        output_file = self.stage4_dir / f"{image_path.stem}_stage4_translate.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 翻譯完成 {len(result['translated_texts'])} 段文字")
        if translation_result.get('new_terminology'):
            print(f"   📝 發現新專有名詞: {len(translation_result['new_terminology'])} 個")
        print(f"   💾 結果保存: {output_file.name}")
        return result


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description='漫畫翻譯器')
    parser.add_argument('target', help='要翻譯的圖片路徑或資料夾路徑')
    parser.add_argument('--output', '-o', default='output', help='輸出目錄 (預設: output)')
    parser.add_argument('--batch', '-b', action='store_true', help='批量翻譯模式')
    
    args = parser.parse_args()
    
    print("🎨 漫畫翻譯器 - 翻譯模式")
    print("=" * 70)
    
    # 初始化翻譯器
    translator = ComicTranslator(output_dir=args.output)
    
    # 批量翻譯模式
    if args.batch:
        translated_files = translator.batch_translate_folder(args.target)
        success = len(translated_files) > 0
        
        if success:
            print(f"\n🎉 批量翻譯完成！共翻譯 {len(translated_files)} 張圖片")
            print("💡 下一步: 使用 python run/render.py --batch 批量渲染")
        else:
            print("\n❌ 批量翻譯失敗")
    else:
        # 單張圖片翻譯
        success = translator.translate_image(args.target)
        
        if success:
            print("\n🎉 翻譯任務完成！")
            print("💡 下一步: 使用 python run/render.py 渲染圖片")
        else:
            print("\n❌ 翻譯失敗")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 