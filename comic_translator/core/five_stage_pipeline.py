"""
Five Stage Manga Translation Pipeline
5階段漫畫翻譯流程管理器

整合所有模組，實現完整的5階段翻譯流程
"""

import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..detection.comic_text_detector import ComicTextDetector
from ..extraction.manga_ocr_extractor import MangaOCRExtractor
from ..translation.text_reorder import TextReorder
from ..translation.text_translator import TextTranslator
from ..terminology.terminology_manager import TerminologyManager
from ..utils.gemini_client import GeminiClient
from ..utils.stage_manager import StageManager


class FiveStagePipeline:
    """5階段漫畫翻譯流程管理器"""
    
    def __init__(self, gemini_api_key: str = None):
        """
        初始化5階段流程
        
        Args:
            gemini_api_key: Gemini API密鑰
        """
        print("🚀 正在初始化5階段漫畫翻譯流程...")
        
        self.initialized = False
        self.translation_history = []  # 翻譯歷史記錄
        
        try:
            # 初始化各個組件
            self.detector = ComicTextDetector()
            self.ocr_extractor = MangaOCRExtractor()
            self.terminology_manager = TerminologyManager()
            self.stage_manager = StageManager()
            
            # 初始化Gemini相關組件
            self.gemini_client = GeminiClient(gemini_api_key)
            self.text_reorder = TextReorder(self.gemini_client)
            self.text_translator = TextTranslator(self.gemini_client)
            
            self.initialized = True
            print("✅ 5階段流程初始化完成!")
            
        except Exception as e:
            print(f"❌ 5階段流程初始化失敗: {e}")
            self.initialized = False
    
    def batch_process_folder(self, input_folder: str, output_folder: str = None) -> Dict[str, Any]:
        """
        批量處理資料夾中的圖片
        
        Args:
            input_folder: 輸入資料夾路徑
            output_folder: 輸出資料夾路徑（可選）
            
        Returns:
            Dict: 批量處理結果
        """
        if not self.initialized:
            print("❌ 系統未初始化")
            return {"success": False, "error": "System not initialized"}
        
        input_path = Path(input_folder)
        if not input_path.exists() or not input_path.is_dir():
            print(f"❌ 輸入資料夾不存在: {input_folder}")
            return {"success": False, "error": f"Input folder not found: {input_folder}"}
        
        # 設定輸出資料夾
        if output_folder is None:
            output_path = input_path.parent / f"{input_path.name}_translated"
        else:
            output_path = Path(output_folder)
        
        output_path.mkdir(exist_ok=True)
        
        # 獲取所有圖片檔案並排序
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
        
        # 按檔案名稱排序（由小到大）
        image_files.sort(key=lambda x: x.name.lower())
        
        if not image_files:
            print(f"⚠️ 在資料夾中沒有找到圖片檔案: {input_folder}")
            return {"success": False, "error": "No image files found"}
        
        print(f"\n📁 開始批量處理資料夾: {input_folder}")
        print(f"📸 找到 {len(image_files)} 個圖片檔案")
        print(f"📤 輸出資料夾: {output_path}")
        print("=" * 80)
        
        # 重置翻譯歷史
        self.translation_history = []
        
        batch_results = {
            "success": True,
            "input_folder": str(input_path),
            "output_folder": str(output_path),
            "total_images": len(image_files),
            "processed_images": [],
            "failed_images": [],
            "start_time": time.time(),
            "translation_history": []
        }
        
        # 逐一處理每張圖片
        for i, image_file in enumerate(image_files, 1):
            print(f"\n🖼️  處理第 {i}/{len(image_files)} 張圖片: {image_file.name}")
            print("-" * 60)
            
            try:
                # 設定輸出檔案路徑
                output_file = output_path / f"translated_{image_file.name}"
                
                # 處理單張圖片
                result = self.process_manga_with_history(str(image_file), str(output_file))
                
                if result and result.get("success"):
                    batch_results["processed_images"].append({
                        "input_file": str(image_file),
                        "output_file": str(output_file),
                        "result": result
                    })
                    
                    # 更新翻譯歷史
                    if result.get("translated_texts"):
                        self.translation_history.extend(result["translated_texts"])
                        # 保持歷史記錄在合理範圍內（最多保留100個翻譯）
                        if len(self.translation_history) > 100:
                            self.translation_history = self.translation_history[-100:]
                    
                    print(f"✅ 第 {i} 張圖片處理成功")
                else:
                    batch_results["failed_images"].append({
                        "input_file": str(image_file),
                        "error": result.get("error", "Unknown error") if result else "No result"
                    })
                    print(f"❌ 第 {i} 張圖片處理失敗")
                
            except Exception as e:
                batch_results["failed_images"].append({
                    "input_file": str(image_file),
                    "error": str(e)
                })
                print(f"❌ 第 {i} 張圖片處理異常: {e}")
            
            # 顯示當前翻譯歷史狀態
            print(f"📚 當前翻譯歷史: {len(self.translation_history)} 條記錄")
            print(f"📖 專有名詞字典: {len(self.terminology_manager.get_all_terms())} 個詞彙")
        
        # 完成處理
        batch_results["end_time"] = time.time()
        batch_results["total_time"] = batch_results["end_time"] - batch_results["start_time"]
        batch_results["success_rate"] = len(batch_results["processed_images"]) / len(image_files)
        batch_results["translation_history"] = self.translation_history.copy()
        
        print("\n" + "=" * 80)
        print("🎉 批量處理完成!")
        print(f"📊 處理統計:")
        print(f"   總圖片數: {batch_results['total_images']}")
        print(f"   成功處理: {len(batch_results['processed_images'])}")
        print(f"   處理失敗: {len(batch_results['failed_images'])}")
        print(f"   成功率: {batch_results['success_rate']:.1%}")
        print(f"   總耗時: {batch_results['total_time']:.1f} 秒")
        print(f"   累積翻譯歷史: {len(batch_results['translation_history'])} 條")
        
        return batch_results
    
    def process_manga_with_history(self, image_path: str, output_path: str = None) -> Optional[Dict[str, Any]]:
        """
        處理單張漫畫，並使用翻譯歷史作為上下文
        
        Args:
            image_path: 漫畫圖像路徑
            output_path: 輸出路徑（可選）
            
        Returns:
            Optional[Dict]: 處理結果，失敗時返回None
        """
        if not self.initialized:
            print("❌ 系統未初始化")
            return None
        
        print(f"\n🎌 開始處理漫畫: {Path(image_path).name}")
        
        image_name = Path(image_path).stem
        start_time = time.time()
        
        try:
            # 執行前4個階段
            text_boxes = self.stage1_detect_text_boxes(image_path, image_name)
            if not text_boxes:
                print("⚠️ 未檢測到文字框")
                return {"success": False, "error": "No text boxes detected"}
            
            extracted_texts = self.stage2_ocr_extraction(image_path, text_boxes, image_name)
            if not extracted_texts:
                print("⚠️ 未擷取到文字")
                return {"success": False, "error": "No text extracted"}
            
            reordered_texts = self.stage3_reorder_text(extracted_texts, image_path, image_name)
            if not reordered_texts:
                print("⚠️ 文字重排序失敗")
                return {"success": False, "error": "Text reordering failed"}
            
            # 階段4：使用歷史上下文進行翻譯
            translation_result = self.stage4_translate_with_history(reordered_texts, image_name, image_path)
            if not translation_result.get("success"):
                print("⚠️ 翻譯失敗")
                return {"success": False, "error": "Translation failed"}
            
            # 階段5：更新專有名詞字典
            self.stage5_update_terminology(translation_result.get("new_terminology", {}))
            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            # 保存輸出（如果指定了輸出路徑）
            if output_path:
                self.save_translation_result(image_path, translation_result["translated_texts"], output_path)
            
            print(f"✅ 漫畫處理完成，耗時: {processing_time:.2f}秒")
            
            return {
                "success": True,
                "input_path": image_path,
                "output_path": output_path,
                "processing_time": processing_time,
                "text_boxes_count": len(text_boxes),
                "extracted_count": len(extracted_texts),
                "reordered_count": len(reordered_texts),
                "translated_count": len(translation_result["translated_texts"]),
                "new_terminology_count": len(translation_result.get("new_terminology", {})),
                "translated_texts": translation_result["translated_texts"],
                "stages": {
                    "stage1": len(text_boxes),
                    "stage2": len(extracted_texts),
                    "stage3": len(reordered_texts),
                    "stage4": len(translation_result["translated_texts"]),
                    "stage5": "completed"
                }
            }
            
        except Exception as e:
            print(f"❌ 處理失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def stage4_translate_with_history(self, reordered_texts: list, image_name: str, image_path: str = None) -> dict:
        """階段4：使用歷史上下文翻譯文字"""
        print("\n🌐 階段4：翻譯文字（使用歷史上下文和圖片分析）")
        
        # 檢查快取
        cached = self.stage_manager.load_stage_result(4, image_name)
        if cached:
            print(f"📁 載入快取結果: {len(cached['translated_texts'])} 個翻譯文字")
            return cached
        
        if not reordered_texts:
            return {'translated_texts': [], 'new_terminology': {}, 'success': False}
        
        # 讀取stage2的OCR結果以獲取vertical資訊
        stage2_result = self.stage_manager.load_stage_result(2, image_name)
        ocr_metadata = {}
        if stage2_result and stage2_result.get('extracted_texts'):
            # 建立box_index到OCR結果的映射
            for item in stage2_result['extracted_texts']:
                box_index = item.get('box_index')
                if box_index is not None:
                    ocr_metadata[box_index] = item
        
        # 提取文字字串列表（如果reordered_texts是字典列表的話）
        if reordered_texts and isinstance(reordered_texts[0], dict):
            # reordered_texts是字典列表，需要提取text欄位
            text_strings = [item.get('text', '') for item in reordered_texts if item.get('text')]
        else:
            # reordered_texts已經是字串列表
            text_strings = [str(text) for text in reordered_texts if text]
        
        if not text_strings:
            return {'translated_texts': [], 'new_terminology': {}, 'success': False}
        
        # 獲取現有專有名詞字典
        terminology_dict = self.terminology_manager.get_all_terms()
        
        # 執行翻譯（傳入歷史上下文和圖片路徑）
        result = self.text_translator.translate_texts_with_history(
            text_strings, 
            terminology_dict, 
            self.translation_history,
            image_path  # 傳遞圖片路徑
        )
        
        # 如果原始輸入是字典列表，需要合併位置資訊
        if reordered_texts and isinstance(reordered_texts[0], dict):
            final_translations = []
            for i, original_item in enumerate(reordered_texts):
                if i < len(result['translated_texts']):
                    translation_item = result['translated_texts'][i]
                    
                    # 從OCR結果中獲取vertical資訊
                    original_index = original_item.get('original_index')
                    ocr_info = ocr_metadata.get(original_index, {})
                    is_vertical = ocr_info.get('vertical', False)
                    
                    final_translations.append({
                        'original_index': original_item.get('original_index'),
                        'new_order': original_item.get('new_order'),
                        'bbox': original_item.get('bbox'),
                        'original': translation_item['original'],
                        'translated': translation_item['translated'],
                        'text_direction': 'vertical' if is_vertical else 'horizontal',  # 直接從OCR的vertical欄位決定
                        'bubble_type': translation_item.get('bubble_type', 'pure_white'),
                        'estimated_font_size': translation_item.get('estimated_font_size', 16)
                    })
            result['translated_texts'] = final_translations
        
        # 保存結果
        save_result = {
            'total_texts': len(reordered_texts),
            'translated_count': len(result['translated_texts']),
            'translated_texts': result['translated_texts'],
            'new_terminology': result['new_terminology'],
            'success': result['success'],
            'history_context_used': len(self.translation_history),
            'used_image_analysis': image_path is not None,
            'used_ocr_vertical_info': len(ocr_metadata) > 0
        }
        
        self.stage_manager.save_stage_result(4, image_name, save_result)
        analysis_method = "圖片視覺分析" if image_path else "純文字分析"
        ocr_info_used = f"，使用OCR垂直信息({len(ocr_metadata)}個)" if ocr_metadata else ""
        print(f"✅ 翻譯完成: {len(result['translated_texts'])} 個文字，使用 {analysis_method}{ocr_info_used}")
        print(f"📚 使用 {len(self.translation_history)} 條歷史上下文")
        print(f"🆕 發現 {len(result['new_terminology'])} 個新專有名詞")
        
        return result
    
    def stage1_detect_text_boxes(self, image_path: str, image_name: str) -> list:
        """階段1：偵測文字對話框"""
        print("\n🔍 階段1：偵測文字對話框")
        
        # 檢查快取
        cached = self.stage_manager.load_stage_result(1, image_name)
        if cached:
            print(f"📁 載入快取結果: {len(cached['text_boxes'])} 個文字框")
            return cached['text_boxes']
        
        # 執行檢測
        result = self.detector.detect_with_metadata(image_path)
        text_boxes = result['text_boxes']
        
        # 保存結果
        self.stage_manager.save_stage_result(1, image_name, result)
        print(f"✅ 檢測到 {len(text_boxes)} 個文字框")
        
        return text_boxes
    
    def stage2_ocr_extraction(self, image_path: str, text_boxes: list, image_name: str) -> list:
        """階段2：OCR擷取文字"""
        print("\n📝 階段2：OCR擷取文字")
        
        # 檢查快取
        cached = self.stage_manager.load_stage_result(2, image_name)
        if cached:
            print(f"📁 載入快取結果: {len(cached['extracted_texts'])} 個擷取文字")
            return cached['extracted_texts']
        
        # 執行OCR
        extracted_texts = self.ocr_extractor.extract_from_boxes(image_path, text_boxes)
        
        # 保存結果
        result = {
            'total_boxes': len(text_boxes),
            'successful_extractions': len(extracted_texts),
            'extraction_rate': len(extracted_texts) / len(text_boxes) if text_boxes else 0,
            'extracted_texts': extracted_texts
        }
        
        self.stage_manager.save_stage_result(2, image_name, result)
        print(f"✅ 成功擷取 {len(extracted_texts)}/{len(text_boxes)} 個文字框")
        
        return extracted_texts
    
    def stage3_reorder_text(self, extracted_texts: list, image_path: str, image_name: str) -> list:
        """階段3：重新排序文字（使用圖片）"""
        print("\n🔄 階段3：重新排序文字")
        
        # 檢查快取
        cached = self.stage_manager.load_stage_result(3, image_name)
        if cached:
            print(f"📁 載入快取結果: {len(cached['reordered_texts'])} 個重排序文字")
            return cached['reordered_texts']
        
        if not extracted_texts:
            return []
        
        # 執行重排序（使用新的圖片重排序功能）
        try:
            reordered_texts = self.text_reorder.reorder_texts_with_image(image_path, extracted_texts)
            
            result = {
                'total_texts': len(extracted_texts),
                'reordered_count': len(reordered_texts),
                'reordered_texts': reordered_texts,
                'success': len(reordered_texts) > 0,
                'method': 'image_based_structured_output'
            }
            
        except Exception as e:
            print(f"⚠️ 圖片重排序失敗，回退到舊方法: {e}")
            
            # 回退到舊的重排序方法
            result = self.text_reorder.reorder_with_metadata(extracted_texts)
            result['method'] = 'fallback_text_only'
            reordered_texts = result['reordered_texts']
        
        # 保存結果
        self.stage_manager.save_stage_result(3, image_name, result)
        print(f"✅ 重排序完成: {len(reordered_texts)} 個文字")
        
        return reordered_texts
    
    def stage5_update_terminology(self, new_terminology: dict):
        """階段5：更新專有名詞字典"""
        print("\n📚 階段5：更新專有名詞字典")
        
        if not new_terminology:
            print("⚠️ 沒有新的專有名詞需要更新")
            return
        
        # 更新專有名詞字典
        added_count = self.terminology_manager.update_terms(new_terminology)
        print(f"✅ 字典更新完成，新增 {added_count} 個詞彙")
    
    def process_manga(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        處理整個5階段流程（兼容性方法，不使用歷史上下文）
        
        Args:
            image_path: 漫畫圖像路徑
            
        Returns:
            Optional[Dict]: 處理結果，失敗時返回None
        """
        return self.process_manga_with_history(image_path, None)
    
    def get_progress(self, image_name: str) -> Dict[str, Any]:
        """
        獲取處理進度
        
        Args:
            image_name: 圖像名稱
            
        Returns:
            Dict: 進度資訊
        """
        progress = self.stage_manager.get_progress(image_name)
        
        completed_stages = sum(1 for completed in progress.values() if completed)
        
        return {
            'completed_stages': completed_stages,
            'total_stages': 5,
            'progress_percentage': (completed_stages / 5) * 100,
            'stage_details': progress
        }
    
    def clear_cache(self, image_name: str = None) -> int:
        """
        清除快取
        
        Args:
            image_name: 圖像名稱，如果未指定則清除所有快取
            
        Returns:
            int: 清除的檔案數量
        """
        if image_name:
            return self.stage_manager.clear_all_stages(image_name)
        else:
            # 清除所有快取需要列出所有檔案
            results = self.stage_manager.list_results()
            cleared_count = 0
            
            for file_info in results['files']:
                file_name = file_info['name']
                if '_stage' in file_name:
                    # 提取圖像名稱
                    parts = file_name.split('_stage')
                    if parts:
                        img_name = parts[0]
                        cleared_count += self.stage_manager.clear_all_stages(img_name)
            
            return cleared_count
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        獲取系統資訊
        
        Returns:
            Dict: 系統資訊
        """
        return {
            'initialized': self.initialized,
            'detector_config': self.detector.config if hasattr(self.detector, 'config') else {},
            'ocr_device_info': self.ocr_extractor.get_device_info(),
            'gemini_model_info': self.gemini_client.get_model_info(),
            'terminology_stats': self.terminology_manager.get_statistics(),
            'results_directory': str(self.stage_manager.results_dir.absolute())
        }
    
    def save_translation_result(self, input_path: str, translated_texts: list, output_path: str):
        """保存翻譯結果到檔案"""
        try:
            # 這裡可以實現保存翻譯結果的邏輯
            # 目前先簡單複製原圖
            import shutil
            shutil.copy2(input_path, output_path)
            
            # 同時保存翻譯文字到JSON檔案
            import json
            json_path = Path(output_path).with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'input_file': input_path,
                    'translated_texts': translated_texts,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"💾 翻譯結果已保存: {output_path}")
            print(f"📄 翻譯文字已保存: {json_path}")
            
        except Exception as e:
            print(f"⚠️ 保存翻譯結果失敗: {e}") 