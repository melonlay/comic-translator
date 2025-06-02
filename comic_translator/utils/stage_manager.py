"""
Stage Result Manager
階段結果管理器

管理5階段流程的結果儲存和載入
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class StageManager:
    """階段結果管理器"""
    
    def __init__(self, results_dir: str = "stages_results"):
        """
        初始化階段管理器
        
        Args:
            results_dir: 結果儲存目錄
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        self.stage_names = {
            1: 'detection',
            2: 'ocr', 
            3: 'reorder',
            4: 'translate',
            5: 'update'
        }
    
    def save_stage_result(self, stage: int, image_name: str, data: Dict[str, Any]) -> Path:
        """
        保存階段結果
        
        Args:
            stage: 階段編號 (1-5)
            image_name: 圖像名稱
            data: 結果資料
            
        Returns:
            Path: 儲存檔案路徑
        """
        if stage not in self.stage_names:
            raise ValueError(f"無效的階段編號: {stage}")
        
        # 添加時間戳
        data['timestamp'] = datetime.now().isoformat()
        data['stage'] = stage
        
        # 生成檔案名
        stage_name = self.stage_names[stage]
        filename = f"{image_name}_stage{stage}_{stage_name}.json"
        filepath = self.results_dir / filename
        
        # 保存檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_stage_result(self, stage: int, image_name: str) -> Optional[Dict[str, Any]]:
        """
        載入階段結果
        
        Args:
            stage: 階段編號 (1-5)
            image_name: 圖像名稱
            
        Returns:
            Optional[Dict]: 結果資料，如果不存在則返回None
        """
        if stage not in self.stage_names:
            raise ValueError(f"無效的階段編號: {stage}")
        
        stage_name = self.stage_names[stage]
        filename = f"{image_name}_stage{stage}_{stage_name}.json"
        filepath = self.results_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 載入階段{stage}結果失敗: {e}")
            return None
    
    def stage_exists(self, stage: int, image_name: str) -> bool:
        """
        檢查階段結果是否存在
        
        Args:
            stage: 階段編號 (1-5)
            image_name: 圖像名稱
            
        Returns:
            bool: 是否存在
        """
        return self.load_stage_result(stage, image_name) is not None
    
    def clear_stage_result(self, stage: int, image_name: str) -> bool:
        """
        清除階段結果
        
        Args:
            stage: 階段編號 (1-5)
            image_name: 圖像名稱
            
        Returns:
            bool: 是否成功清除
        """
        if stage not in self.stage_names:
            raise ValueError(f"無效的階段編號: {stage}")
        
        stage_name = self.stage_names[stage]
        filename = f"{image_name}_stage{stage}_{stage_name}.json"
        filepath = self.results_dir / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                return True
            except Exception as e:
                print(f"⚠️ 清除階段{stage}結果失敗: {e}")
                return False
        
        return True
    
    def clear_all_stages(self, image_name: str) -> int:
        """
        清除所有階段結果
        
        Args:
            image_name: 圖像名稱
            
        Returns:
            int: 清除的檔案數量
        """
        cleared_count = 0
        for stage in self.stage_names.keys():
            if self.clear_stage_result(stage, image_name):
                cleared_count += 1
        
        return cleared_count
    
    def save_final_result(self, image_name: str, data: Dict[str, Any]) -> Path:
        """
        保存最終結果
        
        Args:
            image_name: 圖像名稱
            data: 最終結果資料
            
        Returns:
            Path: 儲存檔案路徑
        """
        data['timestamp'] = datetime.now().isoformat()
        data['type'] = 'final_result'
        
        filename = f"{image_name}_final_result.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_progress(self, image_name: str) -> Dict[str, bool]:
        """
        獲取處理進度
        
        Args:
            image_name: 圖像名稱
            
        Returns:
            Dict: 各階段完成狀態
        """
        progress = {}
        for stage, name in self.stage_names.items():
            progress[f"stage{stage}_{name}"] = self.stage_exists(stage, image_name)
        
        return progress
    
    def list_results(self, image_name: str = None) -> Dict[str, Any]:
        """
        列出結果檔案
        
        Args:
            image_name: 圖像名稱，如果未提供則列出所有結果
            
        Returns:
            Dict: 結果檔案資訊
        """
        if image_name:
            pattern = f"{image_name}_*"
        else:
            pattern = "*"
        
        files = list(self.results_dir.glob(f"{pattern}.json"))
        
        results = {
            'total_files': len(files),
            'files': []
        }
        
        for file in files:
            file_info = {
                'name': file.name,
                'size': file.stat().st_size,
                'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            }
            results['files'].append(file_info)
        
        return results 