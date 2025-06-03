"""
OCR Initializer
OCR初始化器

專門負責OCR模型的初始化
"""

import torch


class OCRInitializer:
    """OCR初始化器"""
    
    def __init__(self):
        """初始化"""
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.ocr_model = None
    
    def initialize_manga_ocr(self):
        """
        初始化Manga OCR模型
        
        Returns:
            manga_ocr.MangaOcr: 初始化的OCR模型
        """
        try:
            import manga_ocr
            self.ocr_model = manga_ocr.MangaOcr()
            print(f"✅ Manga OCR初始化完成 (設備: {self.device})")
            
            if self.device == 'cuda':
                print(f"🚀 GPU: {torch.cuda.get_device_name()}")
            
            return self.ocr_model
                
        except Exception as e:
            print(f"❌ Manga OCR初始化失敗: {e}")
            raise
    
    def get_device_info(self):
        """
        獲取設備資訊
        
        Returns:
            Dict: 設備資訊
        """
        info = {
            'device': self.device,
            'cuda_available': torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name()
            info['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory
        
        return info 