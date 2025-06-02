#!/usr/bin/env python3
"""
漫畫翻譯器命令列介面
Comic Translator Command Line Interface

提供簡單易用的命令列介面進行漫畫翻譯
Provides an easy-to-use command line interface for comic translation
"""

import argparse
import os
import sys
from pathlib import Path

from comic_translator import ComicTranslator, TranslationPipeline


def create_parser():
    """
    創建命令列參數解析器
    Create command line argument parser
    """
    parser = argparse.ArgumentParser(
        description="漫畫翻譯器 / Comic Translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例 / Usage Examples:
  翻譯單張圖片 / Translate single image:
    python main.py single input.jpg output.jpg

  批量翻譯 / Batch translate:
    python main.py batch input_folder output_folder

  使用不同語言 / Use different languages:
    python main.py single input.jpg output.jpg --source en --target zh-CN

  生成預覽 / Generate preview:
    python main.py single input.jpg output.jpg --preview
        """
    )
    
    # 子命令 / Subcommands
    subparsers = parser.add_subparsers(dest='command', help='可用的命令 / Available commands')
    
    # 單張圖片翻譯 / Single image translation
    single_parser = subparsers.add_parser('single', help='翻譯單張圖片 / Translate single image')
    single_parser.add_argument('input', help='輸入圖片路徑 / Input image path')
    single_parser.add_argument('output', help='輸出圖片路徑 / Output image path')
    single_parser.add_argument('--source', '-s', default='ja', help='來源語言 / Source language (default: ja)')
    single_parser.add_argument('--target', '-t', default='zh-TW', help='目標語言 / Target language (default: zh-TW)')
    single_parser.add_argument('--preview', '-p', action='store_true', help='生成預覽圖 / Generate preview image')
    single_parser.add_argument('--config', '-c', help='配置檔案路徑 / Configuration file path')
    
    # 批量翻譯 / Batch translation
    batch_parser = subparsers.add_parser('batch', help='批量翻譯圖片 / Batch translate images')
    batch_parser.add_argument('input_dir', help='輸入目錄 / Input directory')
    batch_parser.add_argument('output_dir', help='輸出目錄 / Output directory')
    batch_parser.add_argument('--source', '-s', default='ja', help='來源語言 / Source language (default: ja)')
    batch_parser.add_argument('--target', '-t', default='zh-TW', help='目標語言 / Target language (default: zh-TW)')
    batch_parser.add_argument('--preview', '-p', action='store_true', help='生成預覽圖 / Generate preview images')
    batch_parser.add_argument('--config', '-c', help='配置檔案路徑 / Configuration file path')
    batch_parser.add_argument('--extensions', nargs='+', default=['.jpg', '.jpeg', '.png'], 
                             help='支援的檔案副檔名 / Supported file extensions (default: .jpg .jpeg .png)')
    
    # 專有名詞管理 / Terminology management
    term_parser = subparsers.add_parser('terminology', help='專有名詞管理 / Terminology management')
    term_subparsers = term_parser.add_subparsers(dest='term_action', help='專有名詞操作 / Terminology actions')
    
    # 匯入專有名詞 / Import terminology
    import_parser = term_subparsers.add_parser('import', help='匯入專有名詞 / Import terminology')
    import_parser.add_argument('file', help='專有名詞檔案路徑 / Terminology file path')
    import_parser.add_argument('--language', '-l', default='ja', help='語言代碼 / Language code (default: ja)')
    
    # 匯出專有名詞 / Export terminology
    export_parser = term_subparsers.add_parser('export', help='匯出專有名詞 / Export terminology')
    export_parser.add_argument('--language', '-l', default='ja', help='語言代碼 / Language code (default: ja)')
    export_parser.add_argument('--format', '-f', choices=['yaml', 'json'], default='yaml', 
                              help='匯出格式 / Export format (default: yaml)')
    
    # 顯示統計 / Show statistics
    term_subparsers.add_parser('stats', help='顯示專有名詞統計 / Show terminology statistics')
    
    # 測試功能 / Test functionality
    test_parser = subparsers.add_parser('test', help='執行測試 / Run tests')
    test_parser.add_argument('--skip-api', action='store_true', help='跳過需要 API 的測試 / Skip tests requiring API')
    
    # 進度管理 / Progress management
    progress_parser = subparsers.add_parser('progress', help='進度管理 / Progress management')
    progress_subparsers = progress_parser.add_subparsers(dest='progress_action', help='進度操作 / Progress actions')
    
    # 查看進度 / View progress
    view_progress_parser = progress_subparsers.add_parser('view', help='查看進度 / View progress')
    view_progress_parser.add_argument('image_path', help='圖片路徑 / Image path')
    
    # 清理快取 / Clear cache
    clear_cache_parser = progress_subparsers.add_parser('clear', help='清理快取 / Clear cache')
    clear_cache_parser.add_argument('--image', help='特定圖片的快取 / Specific image cache')
    clear_cache_parser.add_argument('--all', action='store_true', help='清理所有快取 / Clear all cache')
    
    # 繼續處理 / Resume processing
    resume_parser = progress_subparsers.add_parser('resume', help='繼續處理 / Resume processing')
    resume_parser.add_argument('input', help='輸入圖片路徑 / Input image path')
    resume_parser.add_argument('output', help='輸出圖片路徑 / Output image path')
    resume_parser.add_argument('--source', '-s', default='ja', help='來源語言 / Source language (default: ja)')
    resume_parser.add_argument('--target', '-t', default='zh-TW', help='目標語言 / Target language (default: zh-TW)')
    
    return parser


def cmd_single_image(args):
    """
    處理單張圖片翻譯命令
    Handle single image translation command
    """
    try:
        # 檢查 API Key / Check API Key
        if not os.getenv('genaikey'):
            print("⚠️  請先設定 Google API Key:")
            print("   Windows: set GOOGLE_API_KEY=your_api_key")
            print("   Linux/Mac: export GOOGLE_API_KEY=your_api_key")
            return 1
        
        # 檢查輸入檔案 / Check input file
        if not Path(args.input).exists():
            print(f"✗ 輸入檔案不存在: {args.input}")
            return 1
        
        # 確保輸出目錄存在 / Ensure output directory exists
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"開始翻譯: {args.input} -> {args.output}")
        print(f"語言: {args.source} -> {args.target}")
        
        # 初始化翻譯器 / Initialize translator
        translator = ComicTranslator(args.config)
        
        # 執行翻譯 / Perform translation
        result = translator.translate_comic(
            input_path=args.input,
            output_path=args.output,
            source_language=args.source,
            target_language=args.target
        )
        
        # 生成預覽 / Generate preview
        if args.preview and result.get('success'):
            preview_path = str(Path(args.output).with_suffix('_preview' + Path(args.output).suffix))
            translator.image_processor.preview_text_placement(
                args.input, result['translated_texts'], preview_path
            )
            print(f"預覽圖已生成: {preview_path}")
        
        # 顯示結果 / Display results
        if result['success']:
            print(f"✓ 翻譯成功！")
            print(f"  偵測到文字框: {result['text_boxes_count']} 個")
            print(f"  翻譯文字數量: {len(result['translated_texts'])} 個")
            return 0
        else:
            print(f"✗ 翻譯失敗: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"✗ 執行失敗: {str(e)}")
        return 1


def cmd_batch_translate(args):
    """
    處理批量翻譯命令
    Handle batch translation command
    """
    try:
        # 檢查 API Key / Check API Key
        if not os.getenv('genaikey'):
            print("⚠️  請先設定 Google API Key")
            return 1
        
        # 檢查輸入目錄 / Check input directory
        if not Path(args.input_dir).exists():
            print(f"✗ 輸入目錄不存在: {args.input_dir}")
            return 1
        
        print(f"開始批量翻譯: {args.input_dir} -> {args.output_dir}")
        print(f"語言: {args.source} -> {args.target}")
        print(f"支援的副檔名: {args.extensions}")
        
        # 初始化流水線 / Initialize pipeline
        pipeline = TranslationPipeline(args.config)
        
        # 執行批量翻譯 / Perform batch translation
        results = pipeline.process_batch_images(
            input_directory=args.input_dir,
            output_directory=args.output_dir,
            source_language=args.source,
            target_language=args.target,
            file_extensions=args.extensions,
            preview=args.preview
        )
        
        # 顯示結果 / Display results
        print(f"\n✓ 批量翻譯完成！")
        print(f"  總檔案數: {results['total_files']}")
        print(f"  成功: {results['successful']}")
        print(f"  失敗: {results['failed']}")
        print(f"  總耗時: {results['total_time']:.2f} 秒")
        print(f"  平均耗時: {results['average_time']:.2f} 秒/張")
        
        return 0 if results['failed'] == 0 else 1
        
    except Exception as e:
        print(f"✗ 批量翻譯失敗: {str(e)}")
        return 1


def cmd_terminology(args):
    """
    處理專有名詞管理命令
    Handle terminology management command
    """
    try:
        translator = ComicTranslator()
        
        if args.term_action == 'import':
            success = translator.terminology_manager.import_terminology(args.file, args.language)
            if success:
                print(f"✓ 專有名詞匯入成功: {args.file}")
                return 0
            else:
                print(f"✗ 專有名詞匯入失敗: {args.file}")
                return 1
                
        elif args.term_action == 'export':
            export_path = translator.terminology_manager.export_terminology(args.language, args.format)
            print(f"✓ 專有名詞已匯出至: {export_path}")
            return 0
            
        elif args.term_action == 'stats':
            stats = translator.terminology_manager.get_statistics()
            print("專有名詞統計 / Terminology Statistics:")
            print(f"  總語言數: {stats['total_languages']}")
            print(f"  總詞彙數: {stats['total_terms']}")
            print("  各語言詞彙數:")
            for lang, count in stats['languages'].items():
                print(f"    {lang}: {count}")
            return 0
            
    except Exception as e:
        print(f"✗ 專有名詞操作失敗: {str(e)}")
        return 1


def cmd_test(args):
    """
    處理測試命令
    Handle test command
    """
    try:
        # 匯入測試模組 / Import test module
        sys.path.insert(0, str(Path(__file__).parent))
        from tests.test_comic_translator import run_all_tests
        
        print("執行漫畫翻譯器測試...")
        run_all_tests()
        return 0
        
    except Exception as e:
        print(f"✗ 測試執行失敗: {str(e)}")
        return 1


def cmd_progress(args):
    """
    處理進度管理命令
    Handle progress management command
    """
    try:
        translator = ComicTranslator()
        
        if args.progress_action == 'view':
            # 查看進度 / View progress
            if not Path(args.image_path).exists():
                print(f"✗ 圖片檔案不存在: {args.image_path}")
                return 1
            
            progress = translator.get_progress_info(args.image_path)
            print(f"圖片處理進度: {args.image_path}")
            print(f"文字框偵測: {'✓ 完成' if progress['detection_completed'] else '✗ 未完成'}")
            print(f"總文字框數: {progress['total_boxes']}")
            print(f"文字萃取進度: {progress['extraction_progress']}/{progress['total_boxes']}")
            print(f"文字翻譯進度: {progress['translation_progress']}/{progress['extraction_progress']}")
            
            if progress['total_boxes'] > 0:
                extraction_rate = progress['extraction_progress'] / progress['total_boxes'] * 100
                print(f"萃取完成率: {extraction_rate:.1f}%")
                
                if progress['extraction_progress'] > 0:
                    translation_rate = progress['translation_progress'] / progress['extraction_progress'] * 100
                    print(f"翻譯完成率: {translation_rate:.1f}%")
            
            return 0
            
        elif args.progress_action == 'clear':
            # 清理快取 / Clear cache
            if args.all:
                translator.clear_cache()
                print("✓ 已清理所有快取檔案")
            elif args.image:
                if not Path(args.image).exists():
                    print(f"✗ 圖片檔案不存在: {args.image}")
                    return 1
                translator.clear_cache(args.image)
                print(f"✓ 已清理 {args.image} 的快取檔案")
            else:
                print("請指定 --all 或 --image 參數")
                return 1
            
            return 0
            
        elif args.progress_action == 'resume':
            # 繼續處理 / Resume processing
            if not Path(args.input).exists():
                print(f"✗ 輸入檔案不存在: {args.input}")
                return 1
            
            # 確保輸出目錄存在 / Ensure output directory exists
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            
            # 先查看進度 / First view progress
            progress = translator.get_progress_info(args.input)
            print(f"繼續處理: {args.input}")
            print(f"當前進度: 萃取 {progress['extraction_progress']}/{progress['total_boxes']}, "
                  f"翻譯 {progress['translation_progress']}/{progress['extraction_progress']}")
            
            # 執行翻譯 / Perform translation
            result = translator.translate_comic(
                input_path=args.input,
                output_path=args.output,
                source_language=args.source,
                target_language=args.target,
                resume=True
            )
            
            if result['success']:
                print(f"✓ 翻譯完成！")
                print(f"  偵測到文字框: {result['text_boxes_count']} 個")
                print(f"  成功萃取: {result['extracted_count']} 個")
                print(f"  翻譯文字數量: {len(result['translated_texts'])} 個")
                return 0
            else:
                print(f"✗ 翻譯失敗: {result['error']}")
                if result.get('temp_files_saved'):
                    print("暫存檔案已保存，可使用 progress resume 命令繼續")
                return 1
            
    except Exception as e:
        print(f"✗ 進度管理操作失敗: {str(e)}")
        return 1


def main():
    """
    主函式
    Main function
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 路由到對應的命令處理函式 / Route to corresponding command handler
    if args.command == 'single':
        return cmd_single_image(args)
    elif args.command == 'batch':
        return cmd_batch_translate(args)
    elif args.command == 'terminology':
        return cmd_terminology(args)
    elif args.command == 'test':
        return cmd_test(args)
    elif args.command == 'progress':
        return cmd_progress(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 