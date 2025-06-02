# 漫畫翻譯器 (Comic Translator)

一個功能完整的漫畫翻譯工具，支援自動文字偵測、萃取、翻譯與重新嵌入。

## 功能特色

1. **文字框偵測** - 自動偵測漫畫中的文字框區域
2. **文字萃取** - 使用 OCR 技術萃取文字內容
3. **OCR 校正** - 智能校正 OCR 識別錯誤，確保翻譯準確性
4. **智能翻譯** - 使用 Google Gemini API 進行上下文感知翻譯
5. **專有名詞管理** - 記錄角色名字、地點、文化設定等翻譯對照表
6. **性別敏感翻譯** - 自動識別角色性別，正確翻譯敬語和稱呼
7. **智能緩存機制** - 自動保存翻譯結果，避免重複翻譯提高效率
8. **智能背景修復** - 使用圖像修復技術完全消除原文字並自然重建背景
9. **多方向文字支援** - 支援橫書、直書文字排版
10. **對話框類型識別** - 自動識別純白、有紋理、透明等不同類型對話框

## 安裝步驟

### 1. Clone 本專案（包含 submodules）

```bash
git clone --recurse-submodules https://github.com/melonlay/comic-translator.git
cd comic_translator
```

或者如果已經 clone 了主專案：

```bash
git clone https://github.com/melonlay/comic-translator.git
cd comic_translator
git submodule update --init --recursive
```

### 2. 下載預訓練模型

根據 [comic-text-detector](https://github.com/dmMaze/comic-text-detector) 的說明，需要下載以下模型文件：

從 [manga-image-translator releases](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.2.1) 或 [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing) 下載：

- `comictextdetector.pt` - 文字偵測模型
- `comictextdetector.pt.onnx` - ONNX 格式模型
- `detect.ckpt` - 檢測權重
- `ocr.ckpt` - OCR 權重  
- `inpainting.ckpt` - 圖像修復權重

將這些文件放入 `comic-text-detector/data/` 目錄：

```
comic-text-detector/
└── data/
    ├── comictextdetector.pt
    ├── comictextdetector.pt.onnx
    ├── detect.ckpt
    ├── ocr.ckpt
    └── inpainting.ckpt
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 設定 API 金鑰

設定 Google Gemini API 金鑰：
```bash
export genaikey="your_api_key_here"
```

或在 Windows PowerShell 中：
```powershell
$env:genaikey="your_api_key_here"
```

## 使用方法

### 翻譯階段

使用 `run/translate.py` 進行文字偵測、OCR、重排和翻譯：

```bash
# 單張圖片翻譯
python run/translate.py input_image.jpg

# 批量翻譯
python run/translate.py input_folder/ --batch

# 強制重新翻譯（忽略現有結果）
python run/translate.py input_image.jpg --force

# 批量強制翻譯
python run/translate.py input_folder/ --batch --force
```

**翻譯模式說明：**
- **智能模式**（預設）：自動檢查是否已有翻譯結果，如有則跳過翻譯流程直接使用
- **強制模式**（`--force` 或 `-f`）：忽略現有翻譯結果，強制重新執行完整翻譯流程

### 渲染階段

使用 `run/render.py` 將翻譯結果渲染到原圖：

```bash
# 單張圖片渲染
python run/render.py input_image.jpg

# 批量渲染
python run/render.py input_folder/ --batch

# 列出可渲染的圖片
python run/render.py --list
```

### 完整流程範例

```bash
# 1. 翻譯圖片
python run/translate.py test_images/manga.jpg

# 2. 渲染結果
python run/render.py test_images/manga.jpg

# 結果將保存在 output/rendered/ 目錄
```

## 程序化使用

```python
from comic_translator.core.translator import ComicTranslator

translator = ComicTranslator()
result = translator.translate_comic("input.jpg")
```

## 專案結構

```
comic_translator/
├── core/                    # 核心翻譯流程
├── detection/              # 文字框偵測 (使用 comic-text-detector)
├── extraction/             # 文字萃取 (OCR)
├── translation/            # 翻譯功能 (Google Gemini)
├── terminology/            # 專有名詞管理
├── rendering/              # 文字渲染與背景修復
├── config/                 # 配置管理
├── utils/                  # 工具函式
├── run/                    # 執行腳本
│   ├── translate.py        # 翻譯流程
│   └── render.py          # 渲染流程
├── comic-text-detector/    # 文字偵測模組 (GPLv3)
└── tests/                  # 測試檔案
```

## 技術特色

- **OCR 校正**：自動識別和校正常見的 OCR 錯誤，如相似字符混淆（「ロ」與「口」、「力」與「刀」等）
- **智能背景修復**：使用 OpenCV 圖像修復算法完全消除文字痕跡
- **多語言支援**：支援中文、日文等多種語言的 OCR 與翻譯
- **文字方向檢測**：自動識別橫書/直書排版並相應處理
- **對話框類型分析**：針對不同類型的對話框使用不同的背景處理策略
- **專有名詞一致性**：維護專有名詞對照表確保翻譯一致性
- **智能緩存機制**：自動保存翻譯結果，避免重複翻譯提高效率
- **上下文感知翻譯**：結合圖片視覺信息和翻譯歷史進行上下文感知翻譯
- **性別敏感翻譯**：自動識別角色性別，正確翻譯敬語（如「さん」→「先生」/「小姐」）

### 專有名詞管理

系統會自動維護一個專有名詞字典 (`terminology_dict.json`)，包含：

- **人名翻譯**：記錄角色名稱並標記性別信息（如「キクル(男性)」→「奇庫魯先生」）
- **地名設定**：統一翻譯地點名稱
- **組織機構**：公會、社團等名稱的一致翻譯
- **技能道具**：遊戲/故事相關術語的統一翻譯

字典格式範例：
```json
{
  "ja_to_zh": {
    "キクル": "奇庫魯(男性)",
    "エノメ": "艾諾梅(女性)",
    "狩人サークル": "獵人社團",
    "ギルド": "公會"
  }
}
```

### 前後文一致性

- **角色稱呼統一**：根據專有名詞字典中的性別信息，確保敬語翻譯一致
- **術語翻譯統一**：在整個作品中保持專有名詞的一致翻譯
- **語調風格維持**：分析角色說話特色，保持翻譯風格的連貫性
- **劇情理解**：結合圖片視覺信息和前文脈絡，提供更準確的翻譯

## 授權

本專案使用 **GNU General Public License v3.0 (GPLv3)** 授權。

由於本專案使用了 GPLv3 授權的 comic-text-detector 模組，根據 GPLv3 的傳染性要求，整個專案必須使用 GPLv3 授權。

這意味著：
- 您可以自由使用、修改和分發本軟體
- 任何基於本軟體的衍生作品也必須使用 GPLv3 授權
- 您必須提供完整的原始碼
- 請參閱 [LICENSE](LICENSE) 文件了解詳細條款

## 作者

Cursor IDE and claude-4-sonet, prompt by me 

## 貢獻

歡迎提交 Pull Request 或回報問題。請確保您的貢獻符合 GPLv3 授權條款。

## 相關專案

- [comic-text-detector](https://github.com/dmMaze/comic-text-detector) - 用於文字偵測的核心模組 (GPLv3) 