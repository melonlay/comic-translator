#!/usr/bin/env python3
"""
漫畫翻譯器 - 渲染執行檔案
Comic Translator - Rendering Runner

將翻譯結果渲染到原始圖片上：
- 讀取翻譯結果JSON
- 強化textured背景處理
- 精確的橫書/直書文字排版
- 正確的行間距計算
- 智能字體大小調整

用法:
    python run/render.py <image_path>
    python run/render.py test_images/manga.jpg
    python run/render.py test_images/manga.jpg --output custom_output
"""

import sys
import os
from pathlib import Path
import argparse

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from comic_translator.rendering import TextOverlay


class ComicRenderer:
    """漫畫渲染器主類"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化渲染器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.stage4_dir = self.output_dir / "stage4_translate"
        self.rendered_dir = self.output_dir / "rendered"
        
        # 確保目錄存在
        self.output_dir.mkdir(exist_ok=True)
        self.rendered_dir.mkdir(exist_ok=True)
        
        # 初始化渲染器
        self.overlay = TextOverlay(output_dir=str(self.rendered_dir))
        
        print(f"✅ 漫畫渲染器初始化完成")
        print(f"📁 輸出目錄: {self.output_dir}")
        print(f"🌏 Stage4 目錄: {self.stage4_dir}")
        print(f"🎨 渲染結果目錄: {self.rendered_dir}")
    
    def render_image(self, image_path: str) -> str:
        """
        渲染單張圖片
        
        Args:
            image_path: 原始圖片路徑
            
        Returns:
            str: 渲染後的圖片路徑，失敗返回None
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            print(f"❌ 圖片不存在: {image_path}")
            return None
        
        # 檢查翻譯結果是否存在
        stage4_json = self.stage4_dir / f"{image_path.stem}_stage4_translate.json"
        if not stage4_json.exists():
            print(f"❌ 翻譯結果不存在: {stage4_json}")
            print("💡 請先運行: python run/translate.py <image_path>")
            return None
        
        print(f"\n🎨 開始渲染圖片: {image_path.name}")
        print("=" * 70)
        print(f"📄 使用翻譯結果: {stage4_json.name}")
        
        try:
            # 執行渲染
            output_path = self.overlay.render_translated_image(
                str(image_path), 
                str(stage4_json)
            )
            
            if output_path and Path(output_path).exists():
                print(f"\n✅ 渲染完成: {Path(output_path).name}")
                print(f"💾 保存位置: {output_path}")
                
                # 顯示文件信息
                file_size = Path(output_path).stat().st_size // 1024
                print(f"📁 文件大小: {file_size} KB")
                
                return output_path
            else:
                print("\n❌ 渲染失敗")
                return None
                
        except Exception as e:
            print(f"\n❌ 渲染過程出錯: {e}")
            return None
    
    def batch_render_folder(self, folder_path: str) -> list:
        """
        批量渲染資料夾中的圖片
        
        Args:
            folder_path: 包含圖片的資料夾路徑
            
        Returns:
            list: 成功渲染的圖片路徑列表
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
                # 檢查是否有對應的翻譯結果
                stage4_json = self.stage4_dir / f"{file_path.stem}_stage4_translate.json"
                if stage4_json.exists():
                    image_files.append(file_path)
        
        image_files.sort(key=lambda x: x.name.lower())
        
        print(f"\n📁 批量渲染資料夾: {folder_path}")
        print("=" * 70)
        print(f"🖼️ 找到 {len(image_files)} 個可渲染的圖片")
        
        rendered_files = []
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n🎨 渲染第 {i}/{len(image_files)} 張: {image_file.name}")
            
            output_path = self.render_image(str(image_file))
            if output_path:
                rendered_files.append(output_path)
                print(f"✅ 渲染成功")
            else:
                print(f"⚠️ 渲染失敗")
        
        print(f"\n🎉 批量渲染完成: {len(rendered_files)}/{len(image_files)} 成功")
        return rendered_files
    
    def get_available_images(self) -> list:
        """
        獲取可渲染的圖片列表（有翻譯結果的圖片）
        
        Returns:
            list: 可渲染的圖片名稱列表
        """
        if not self.stage4_dir.exists():
            return []
        
        available_images = []
        
        # 查找所有stage4翻譯結果
        for json_file in self.stage4_dir.glob("*_stage4_translate.json"):
            image_name = json_file.stem.replace("_stage4_translate", "")
            available_images.append(image_name)
        
        return sorted(available_images)


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description='漫畫渲染器')
    parser.add_argument('target', nargs='?', help='要渲染的圖片路徑或資料夾路徑')
    parser.add_argument('--output', '-o', default='output', help='輸出目錄 (預設: output)')
    parser.add_argument('--batch', '-b', action='store_true', help='批量渲染模式')
    parser.add_argument('--list', '-l', action='store_true', help='列出可渲染的圖片')
    
    args = parser.parse_args()
    
    print("🎨 漫畫翻譯器 - 渲染模式")
    print("=" * 70)
    
    # 初始化渲染器
    renderer = ComicRenderer(output_dir=args.output)
    
    # 列出可渲染的圖片
    if args.list:
        available_images = renderer.get_available_images()
        if available_images:
            print("\n📋 可渲染的圖片:")
            for i, image_name in enumerate(available_images, 1):
                print(f"   {i:2d}. {image_name}")
            print(f"\n💡 總共 {len(available_images)} 張圖片可渲染")
        else:
            print("\n⚠️ 沒有找到可渲染的圖片")
            print("💡 請先運行: python run/translate.py <image_path>")
        return True
    
    if not args.target:
        print("❌ 請指定要渲染的圖片或資料夾路徑")
        print("💡 用法: python run/render.py <image_path>")
        print("💡 或者: python run/render.py --list 查看可渲染的圖片")
        return False
    
    # 批量渲染模式
    if args.batch:
        rendered_files = renderer.batch_render_folder(args.target)
        success = len(rendered_files) > 0
    else:
        # 單張圖片渲染
        output_path = renderer.render_image(args.target)
        success = output_path is not None
    
    if success:
        print("\n🎉 渲染任務完成！")
        print(f"📁 查看結果: {renderer.rendered_dir}")
    else:
        print("\n❌ 渲染失敗")
        print("💡 請檢查:")
        print("   - 圖片路徑是否正確")
        print("   - 翻譯結果是否存在")
        print("   - 使用 --list 查看可渲染的圖片")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 