# 漫畫翻譯器 (Comic Translator) v2.0

一個功能完整的漫畫翻譯工具，支援自動文字偵測、萃取、翻譯與重新嵌入。v2.0 版本全面重構，採用原子化架構和智能備用機制。

## 功能特色

1. **文字框偵測** - 自動偵測漫畫中的文字框區域
2. **文字萃取** - 使用 OCR 技術萃取文字內容
3. **OCR 校正** - 智能校正 OCR 識別錯誤，確保翻譯準確性
4. **智能翻譯** - 使用 Google Gemini API 進行上下文感知翻譯
5. **圖片過濾備用機制** - 當圖片內容被 Gemini 過濾時，自動切換到純文字翻譯模式
6. **專有名詞管理** - 記錄角色名字、地點、文化設定等翻譯對照表
7. **性別敏感翻譯** - 自動識別角色性別，正確翻譯敬語和稱呼
8. **智能緩存機制** - 自動保存翻譯結果，避免重複翻譯提高效率
9. **智能背景修復** - 使用圖像修復技術完全消除原文字並自然重建背景
10. **多方向文字支援** - 支援橫書、直書文字排版
11. **對話框類型識別** - 自動識別純白、有紋理、透明等不同類型對話框
12. **翻譯校對支援** - 手動編輯翻譯結果，支援重新渲染

## v2.0 重構亮點

### 原子化架構設計
- **模組化設計**：每個功能拆分為獨立的原子化模組，便於維護和擴展
- **低耦合**：模組間依賴降低，提高系統穩定性
- **樹狀結構**：程式庫使用清晰的樹狀結構進行管理

### 翻譯系統重構
- **PromptManager**：專門管理各種翻譯提示詞
- **ResponseParser**：負責解析和驗證API回應結果
- **TranslationCore**：執行具體的翻譯操作
- **TranslationFlow**：管理翻譯流程，包含智能備用機制
- **TextTranslator**：統一的翻譯介面

### 智能備用機制
當 Gemini API 因內容過濾失敗時：
1. **自動檢測**：識別API調用失敗原因（內容過濾、安全策略等）
2. **自動切換**：無縫切換到純文字翻譯模式
3. **不中斷服務**：確保翻譯流程能夠繼續完成

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

### 翻譯校對與修正

#### 手動修正 Stage4 翻譯結果

翻譯完成後，可以手動編輯翻譯結果進行校對：

1. **查找翻譯結果檔案**
   ```bash
   # 翻譯結果保存在 output/stage4_translate/ 目錄
   ls output/stage4_translate/
   # 例如：manga_page_01_stage4_translate.json
   ```

2. **編輯翻譯結果**
   ```bash
   # 使用任何文字編輯器編輯 JSON 檔案
   code output/stage4_translate/manga_page_01_stage4_translate.json
   ```

3. **JSON 結構說明**
   ```json
   {
     "translated_texts": [
       {
         "original": "こんにちは",           // 原始日文
         "translated": "你好",              // 中文翻譯（可修改）
         "text_direction": "horizontal",    // 文字方向：horizontal/vertical
         "bubble_type": "pure_white",       // 對話框類型
         "estimated_font_size": 16          // 估計字體大小
       }
     ],
     "new_terminology": {                   // 新發現的專有名詞
       "キクル": "奇庫魯(男性)"
     },
     "success": true
   }
   ```

4. **可修改的欄位**
   - `translated`：修改翻譯內容
   - `text_direction`：調整文字方向（`horizontal` 或 `vertical`）
   - `bubble_type`：調整對話框類型（`pure_white`、`textured`、`transparent`）
   - `estimated_font_size`：調整字體大小（數字）

5. **保存並重新渲染**
   ```bash
   # 修改完成後，重新渲染圖片
   python run/render.py input_image.jpg
   ```

#### 常見修正情況

- **翻譯不準確**：直接修改 `translated` 欄位
- **文字方向錯誤**：調整 `text_direction` 為 `horizontal` 或 `vertical`
- **字體太大/太小**：調整 `estimated_font_size` 數值
- **對話框背景不適合**：調整 `bubble_type` 類型

#### 批量校對工作流程

```bash
# 1. 批量翻譯
python run/translate.py manga_folder/ --batch

# 2. 逐一校對翻譯結果
# 編輯 output/stage4_translate/ 目錄下的所有 JSON 檔案

# 3. 批量重新渲染
python run/render.py manga_folder/ --batch
```

### 完整流程範例

```bash
# 1. 翻譯圖片
python run/translate.py test_images/manga.jpg

# 2. 校對翻譯結果（可選）
code output/stage4_translate/manga_stage4_translate.json

# 3. 渲染結果
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
├── translation/            # 翻譯功能 (Google Gemini) - v2.0 重構
│   ├── prompt_manager.py   # 提示詞管理器
│   ├── response_parser.py  # 回應解析器
│   ├── translation_core.py # 翻譯核心
│   ├── translation_flow.py # 翻譯流程管理器（含備用機制）
│   ├── text_translator.py # 統一翻譯介面
│   └── text_reorder.py    # 文字重排序
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
- **智能備用機制**：當圖片調用被過濾時，自動切換到純文字翻譯模式，確保服務不中斷
- **智能背景修復**：使用 OpenCV 圖像修復算法完全消除文字痕跡
- **多語言支援**：支援中文、日文等多種語言的 OCR 與翻譯
- **文字方向檢測**：自動識別橫書/直書排版並相應處理
- **對話框類型分析**：針對不同類型的對話框使用不同的背景處理策略
- **專有名詞一致性**：維護專有名詞對照表確保翻譯一致性
- **智能緩存機制**：自動保存翻譯結果，避免重複翻譯提高效率
- **上下文感知翻譯**：結合圖片視覺信息和翻譯歷史進行上下文感知翻譯
- **性別敏感翻譯**：自動識別角色性別，正確翻譯敬語（如「さん」→「先生」/「小姐」）
- **原子化架構**：模組化設計，低耦合，易於維護和擴展

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

### v2.0 智能備用機制

當 Gemini API 圖片調用失敗時：

1. **失敗檢測**：自動識別以下失敗情況
   - API 回應為空
   - 內容被安全過濾器攔截
   - 政策違反提醒
   - 其他 API 調用相關錯誤

2. **自動切換**：
   ```
   圖片翻譯 ─失敗─> 純文字翻譯 ─失敗─> 備用翻譯（原文）
        ↓成功              ↓成功         ↓
      完成翻譯          完成翻譯      保持原文
   ```

3. **用戶體驗**：
   - 翻譯過程無中斷
   - 自動降級處理
   - 詳細的狀態提示

## 更新日誌

### v2.0.0 (2024-12)
- **架構重構**：採用原子化設計，提高代碼可維護性
- **智能備用機制**：圖片調用失敗時自動切換到純文字模式
- **翻譯校對支援**：支援手動編輯翻譯結果並重新渲染
- **模組化設計**：翻譯系統拆分為多個獨立模組
- **錯誤處理優化**：更好的錯誤檢測和處理機制

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