"""
Terminology Manager
專有名詞管理器

管理日文到中文的專有名詞字典
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class TerminologyManager:
    """專有名詞管理器"""
    
    def __init__(self, dict_file: str = "terminology_dict.json"):
        """
        初始化專有名詞管理器
        
        Args:
            dict_file: 字典檔案路徑
        """
        self.dict_file = Path(dict_file)
        self.terminology_data = {}
        self.load_dictionary()
    
    def load_dictionary(self) -> bool:
        """
        載入專有名詞字典
        
        Returns:
            bool: 是否成功載入
        """
        try:
            if self.dict_file.exists():
                with open(self.dict_file, 'r', encoding='utf-8') as f:
                    self.terminology_data = json.load(f)
                print(f"📖 已載入 {len(self.terminology_data.get('ja_to_zh', {}))} 個專有名詞")
            else:
                self._create_new_dictionary()
                print("📖 建立新的專有名詞字典")
            
            return True
            
        except Exception as e:
            print(f"⚠️ 載入專有名詞字典失敗: {e}")
            self._create_new_dictionary()
            return False
    
    def _create_new_dictionary(self):
        """創建新的字典結構"""
        self.terminology_data = {
            "ja_to_zh": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0",
                "total_terms": 0
            }
        }
    
    def save_dictionary(self) -> bool:
        """
        保存專有名詞字典
        
        Returns:
            bool: 是否成功保存
        """
        try:
            # 更新元數據
            self.terminology_data["metadata"]["updated_at"] = datetime.now().isoformat()
            self.terminology_data["metadata"]["total_terms"] = len(self.terminology_data.get("ja_to_zh", {}))
            
            with open(self.dict_file, 'w', encoding='utf-8') as f:
                json.dump(self.terminology_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 專有名詞字典已更新 ({self.terminology_data['metadata']['total_terms']} 個詞彙)")
            return True
            
        except Exception as e:
            print(f"⚠️ 保存專有名詞字典失敗: {e}")
            return False
    
    def add_term(self, japanese: str, chinese: str) -> bool:
        """
        添加專有名詞
        
        Args:
            japanese: 日文詞彙
            chinese: 中文翻譯
            
        Returns:
            bool: 是否成功添加（新詞彙）
        """
        if not self.terminology_data.get("ja_to_zh"):
            self.terminology_data["ja_to_zh"] = {}
        
        # 檢查是否已存在
        if japanese in self.terminology_data["ja_to_zh"]:
            existing = self.terminology_data["ja_to_zh"][japanese]
            if existing != chinese:
                print(f"⚠️ 詞彙已存在且翻譯不同: {japanese} → {existing} (新: {chinese})")
            return False
        
        # 添加新詞彙
        self.terminology_data["ja_to_zh"][japanese] = chinese
        print(f"➕ 新增專有名詞: {japanese} → {chinese}")
        return True
    
    def update_terms(self, new_terminology: Dict[str, str]) -> int:
        """
        批量更新專有名詞
        
        Args:
            new_terminology: 新的專有名詞字典
            
        Returns:
            int: 新增的詞彙數量
        """
        if not new_terminology:
            return 0
        
        added_count = 0
        for japanese, chinese in new_terminology.items():
            if self.add_term(japanese, chinese):
                added_count += 1
        
        if added_count > 0:
            self.save_dictionary()
        
        return added_count
    
    def get_term(self, japanese: str) -> Optional[str]:
        """
        獲取專有名詞翻譯
        
        Args:
            japanese: 日文詞彙
            
        Returns:
            Optional[str]: 中文翻譯，如果不存在則返回None
        """
        return self.terminology_data.get("ja_to_zh", {}).get(japanese)
    
    def remove_term(self, japanese: str) -> bool:
        """
        移除專有名詞
        
        Args:
            japanese: 日文詞彙
            
        Returns:
            bool: 是否成功移除
        """
        ja_to_zh = self.terminology_data.get("ja_to_zh", {})
        if japanese in ja_to_zh:
            removed_translation = ja_to_zh.pop(japanese)
            print(f"🗑️ 移除專有名詞: {japanese} → {removed_translation}")
            self.save_dictionary()
            return True
        
        return False
    
    def search_terms(self, keyword: str) -> Dict[str, str]:
        """
        搜尋專有名詞
        
        Args:
            keyword: 搜尋關鍵字
            
        Returns:
            Dict[str, str]: 符合的專有名詞
        """
        ja_to_zh = self.terminology_data.get("ja_to_zh", {})
        results = {}
        
        for japanese, chinese in ja_to_zh.items():
            if keyword in japanese or keyword in chinese:
                results[japanese] = chinese
        
        return results
    
    def get_all_terms(self) -> Dict[str, str]:
        """
        獲取所有專有名詞
        
        Returns:
            Dict[str, str]: 所有專有名詞字典
        """
        return self.terminology_data.get("ja_to_zh", {}).copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取字典統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        ja_to_zh = self.terminology_data.get("ja_to_zh", {})
        metadata = self.terminology_data.get("metadata", {})
        
        return {
            "total_terms": len(ja_to_zh),
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
            "version": metadata.get("version"),
            "file_path": str(self.dict_file.absolute()),
            "file_exists": self.dict_file.exists()
        }
    
    def export_dictionary(self, output_file: str, format_type: str = "json") -> bool:
        """
        匯出字典
        
        Args:
            output_file: 輸出檔案路徑
            format_type: 格式類型 (json, csv, txt)
            
        Returns:
            bool: 是否成功匯出
        """
        try:
            output_path = Path(output_file)
            ja_to_zh = self.terminology_data.get("ja_to_zh", {})
            
            if format_type.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.terminology_data, f, ensure_ascii=False, indent=2)
                    
            elif format_type.lower() == "csv":
                import csv
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Japanese", "Chinese"])
                    for ja, zh in ja_to_zh.items():
                        writer.writerow([ja, zh])
                        
            elif format_type.lower() == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    for ja, zh in ja_to_zh.items():
                        f.write(f"{ja}\t{zh}\n")
            
            else:
                raise ValueError(f"不支援的格式類型: {format_type}")
            
            print(f"📤 字典已匯出到: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 匯出字典失敗: {e}")
            return False 