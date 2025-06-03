# Comic Translator v2.0

A comprehensive comic translation tool that supports automatic text detection, extraction, translation, and re-embedding. v2.0 features a complete refactoring with atomic architecture and intelligent fallback mechanisms.

## Features

1. **Text Detection** - Automatically detect text regions in manga
2. **Text Extraction** - Extract text using OCR technology
3. **OCR Correction** - Intelligently correct OCR recognition errors for accurate translation
4. **Smart Translation** - Context-aware translation using Google Gemini API
5. **Image Filtering Fallback** - Automatically switch to text-only mode when image content is filtered by Gemini
6. **Terminology Management** - Maintain translation dictionaries for character names, locations, cultural settings
7. **Gender-sensitive Translation** - Automatically identify character gender for correct honorific translation
8. **Intelligent Caching** - Automatically save translation results to avoid duplicate translations
9. **Intelligent Background Repair** - Use image inpainting techniques to completely remove original text and naturally reconstruct backgrounds
10. **Multi-directional Text Support** - Support both horizontal and vertical text layouts
11. **Speech Bubble Type Recognition** - Automatically identify different types of speech bubbles (pure white, textured, transparent)
12. **Translation Proofreading Support** - Manual editing of translation results with re-rendering support

## v2.0 Refactoring Highlights

### Atomic Architecture Design
- **Modular Design**: Each function is split into independent atomic modules for easy maintenance and extension
- **Low Coupling**: Reduced dependencies between modules for improved system stability
- **Tree Structure**: Program library uses clear tree structure for management

### Translation System Refactoring
- **PromptManager**: Specialized management of various translation prompts
- **ResponseParser**: Responsible for parsing and validating API response results
- **TranslationCore**: Execute specific translation operations
- **TranslationFlow**: Manage translation flow, including intelligent fallback mechanisms
- **TextTranslator**: Unified translation interface

### Intelligent Fallback Mechanism
When Gemini API fails due to content filtering:
1. **Automatic Detection**: Identify API call failure reasons (content filtering, safety policies, etc.)
2. **Automatic Switching**: Seamlessly switch to text-only translation mode
3. **Uninterrupted Service**: Ensure translation process can continue to completion

## Installation Steps

### 1. Clone this repository (with submodules)

```bash
git clone --recurse-submodules https://github.com/melonlay/comic-translator.git
cd comic_translator
```

Or if you've already cloned the main repository:

```bash
git clone https://github.com/melonlay/comic-translator.git
cd comic_translator
git submodule update --init --recursive
```

### 2. Download pre-trained models

According to [comic-text-detector](https://github.com/dmMaze/comic-text-detector) instructions, you need to download the following model files:

Download from [manga-image-translator releases](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.2.1) or [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing):

- `comictextdetector.pt` - Text detection model
- `comictextdetector.pt.onnx` - ONNX format model
- `detect.ckpt` - Detection weights
- `ocr.ckpt` - OCR weights  
- `inpainting.ckpt` - Image inpainting weights

Place these files in the `comic-text-detector/data/` directory:

```
comic-text-detector/
└── data/
    ├── comictextdetector.pt
    ├── comictextdetector.pt.onnx
    ├── detect.ckpt
    ├── ocr.ckpt
    └── inpainting.ckpt
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API key

Set up Google Gemini API key:
```bash
export genaikey="your_api_key_here"
```

Or in Windows PowerShell:
```powershell
$env:genaikey="your_api_key_here"
```

## Usage

### Translation Stage

Use `run/translate.py` for text detection, OCR, reordering, and translation:

```bash
# Single image translation
python run/translate.py input_image.jpg

# Batch translation
python run/translate.py input_folder/ --batch

# Force re-translation (ignore existing results)
python run/translate.py input_image.jpg --force

# Batch force translation
python run/translate.py input_folder/ --batch --force
```

**Translation Mode Description:**
- **Smart Mode** (default): Automatically check if translation results exist, skip translation process if available
- **Force Mode** (`--force` or `-f`): Ignore existing translation results, force complete re-execution of translation process

### Rendering Stage

Use `run/render.py` to render translation results onto the original image:

```bash
# Single image rendering
python run/render.py input_image.jpg

# Batch rendering
python run/render.py input_folder/ --batch

# List available images for rendering
python run/render.py --list
```

### Translation Proofreading and Correction

#### Manual Correction of Stage4 Translation Results

After translation is complete, you can manually edit translation results for proofreading:

1. **Find Translation Result Files**
   ```bash
   # Translation results are saved in output/stage4_translate/ directory
   ls output/stage4_translate/
   # Example: manga_page_01_stage4_translate.json
   ```

2. **Edit Translation Results**
   ```bash
   # Use any text editor to edit the JSON file
   code output/stage4_translate/manga_page_01_stage4_translate.json
   ```

3. **JSON Structure Description**
   ```json
   {
     "translated_texts": [
       {
         "original": "こんにちは",           // Original Japanese
         "translated": "Hello",             // Chinese translation (editable)
         "text_direction": "horizontal",    // Text direction: horizontal/vertical
         "bubble_type": "pure_white",       // Speech bubble type
         "estimated_font_size": 16          // Estimated font size
       }
     ],
     "new_terminology": {                   // Newly discovered terminology
       "キクル": "Kikuru(Male)"
     },
     "success": true
   }
   ```

4. **Editable Fields**
   - `translated`: Modify translation content
   - `text_direction`: Adjust text direction (`horizontal` or `vertical`)
   - `bubble_type`: Adjust bubble type (`pure_white`, `textured`, `transparent`)
   - `estimated_font_size`: Adjust font size (number)

5. **Save and Re-render**
   ```bash
   # After modification, re-render the image
   python run/render.py input_image.jpg
   ```

#### Common Correction Scenarios

- **Inaccurate Translation**: Directly modify the `translated` field
- **Wrong Text Direction**: Adjust `text_direction` to `horizontal` or `vertical`
- **Font Too Large/Small**: Adjust `estimated_font_size` value
- **Inappropriate Bubble Background**: Adjust `bubble_type`

#### Batch Proofreading Workflow

```bash
# 1. Batch translation
python run/translate.py manga_folder/ --batch

# 2. Proofread translation results one by one
# Edit all JSON files in output/stage4_translate/ directory

# 3. Batch re-render
python run/render.py manga_folder/ --batch
```

### Complete workflow example

```bash
# 1. Translate image
python run/translate.py test_images/manga.jpg

# 2. Proofread translation results (optional)
code output/stage4_translate/manga_stage4_translate.json

# 3. Render results
python run/render.py test_images/manga.jpg

# Results will be saved in output/rendered/ directory
```

## Programmatic Usage

```python
from comic_translator.core.translator import ComicTranslator

translator = ComicTranslator()
result = translator.translate_comic("input.jpg")
```

## Project Structure

```
comic_translator/
├── core/                    # Core translation pipeline
├── detection/              # Text box detection (using comic-text-detector)
├── extraction/             # Text extraction (OCR)
├── translation/            # Translation functionality (Google Gemini) - v2.0 refactored
│   ├── prompt_manager.py   # Prompt manager
│   ├── response_parser.py  # Response parser
│   ├── translation_core.py # Translation core
│   ├── translation_flow.py # Translation flow manager (with fallback)
│   ├── text_translator.py # Unified translation interface
│   └── text_reorder.py    # Text reordering
├── terminology/            # Terminology management
├── rendering/              # Text rendering and background repair
├── config/                 # Configuration management
├── utils/                  # Utility functions
├── run/                    # Execution scripts
│   ├── translate.py        # Translation pipeline
│   └── render.py          # Rendering pipeline
├── comic-text-detector/    # Text detection module (GPLv3)
└── tests/                  # Test files
```

## Technical Highlights

- **OCR Correction**: Automatically identify and correct common OCR errors, such as similar character confusion (「ロ」vs「口」, 「力」vs「刀」, etc.)
- **Intelligent Fallback**: Automatically switch to text-only translation mode when image calls fail, ensuring uninterrupted service
- **Intelligent Background Repair**: Use OpenCV image inpainting algorithms to completely eliminate text traces
- **Multi-language Support**: Support OCR and translation for Chinese, Japanese, and other languages
- **Text Direction Detection**: Automatically identify horizontal/vertical layouts and handle accordingly
- **Speech Bubble Type Analysis**: Use different background processing strategies for different types of speech bubbles
- **Terminology Consistency**: Maintain terminology dictionaries to ensure translation consistency
- **Intelligent Caching**: Automatically save translation results to avoid duplicate translations and improve efficiency
- **Context-aware Translation**: Combine visual image information and translation history for context-aware translation
- **Gender-sensitive Translation**: Automatically identify character gender for correct honorific translation (e.g., "さん" → "Mr."/"Ms.")
- **Atomic Architecture**: Modular design with low coupling, easy to maintain and extend

### Terminology Management

The system automatically maintains a terminology dictionary (`terminology_dict.json`), including:

- **Character Name Translation**: Record character names with gender information (e.g., "キクル(Male)" → "Kikuru Mr.")
- **Location Settings**: Unified translation of place names
- **Organizations**: Consistent translation of guild, club names, etc.
- **Skills & Items**: Unified translation of game/story-related terminology

Dictionary format example:
```json
{
  "ja_to_zh": {
    "キクル": "Kikuru(Male)",
    "エノメ": "Enome(Female)",
    "狩人サークル": "Hunter Circle",
    "ギルド": "Guild"
  }
}
```

### Context Consistency

- **Unified Character Addressing**: Ensure consistent honorific translation based on gender information in terminology dictionary
- **Unified Terminology Translation**: Maintain consistent terminology translation throughout the work
- **Tone Style Maintenance**: Analyze character speaking characteristics to maintain translation style coherence
- **Plot Understanding**: Combine visual image information and preceding context to provide more accurate translation

### v2.0 Intelligent Fallback Mechanism

When Gemini API image calls fail:

1. **Failure Detection**: Automatically identify the following failure situations
   - Empty API response
   - Content blocked by safety filter
   - Policy violation alerts
   - Other API call-related errors

2. **Automatic Switching**:
   ```
   Image Translation ─fails─> Text-only Translation ─fails─> Fallback Translation (Original)
        ↓success                    ↓success                    ↓
      Complete Translation       Complete Translation      Keep Original Text
   ```

3. **User Experience**:
   - Uninterrupted translation process
   - Automatic degradation handling
   - Detailed status notifications

## Changelog

### v2.0.0 (2024-12)
- **Architecture Refactoring**: Adopted atomic design for improved code maintainability
- **Intelligent Fallback**: Automatically switch to text-only mode when image calls fail
- **Translation Proofreading Support**: Support manual editing of translation results and re-rendering
- **Modular Design**: Translation system split into multiple independent modules
- **Error Handling Optimization**: Better error detection and handling mechanisms

## License

This project is licensed under **GNU General Public License v3.0 (GPLv3)**.

Since this project uses the GPLv3-licensed comic-text-detector module, according to GPLv3's copyleft requirements, the entire project must use GPLv3 license.

This means:
- You are free to use, modify, and distribute this software
- Any derivative works based on this software must also use GPLv3 license
- You must provide the complete source code
- Please refer to the [LICENSE](LICENSE) file for detailed terms

## Author

Cursor IDE and claude-4-sonet, prompt by me 

## Contributing

Pull requests and issue reports are welcome. Please ensure your contributions comply with GPLv3 license terms.

## Related Projects

- [comic-text-detector](https://github.com/dmMaze/comic-text-detector) - Core module for text detection (GPLv3) 