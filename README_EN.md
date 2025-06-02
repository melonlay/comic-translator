# Comic Translator

A comprehensive comic translation tool that supports automatic text detection, extraction, translation, and re-embedding.

## Features

1. **Text Detection** - Automatically detect text regions in manga
2. **Text Extraction** - Extract text using OCR technology
3. **OCR Correction** - Intelligently correct OCR recognition errors for accurate translation
4. **Smart Translation** - Context-aware translation using Google Gemini API
5. **Terminology Management** - Maintain translation dictionaries for character names, locations, cultural settings
6. **Intelligent Background Repair** - Use image inpainting techniques to completely remove original text and naturally reconstruct backgrounds
7. **Multi-directional Text Support** - Support both horizontal and vertical text layouts
8. **Speech Bubble Type Recognition** - Automatically identify different types of speech bubbles (pure white, textured, transparent)

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
```

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

### Complete workflow example

```bash
# 1. Translate image
python run/translate.py test_images/manga.jpg

# 2. Render results
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
├── translation/            # Translation functionality (Google Gemini)
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
- **Intelligent Background Repair**: Use OpenCV image inpainting algorithms to completely eliminate text traces
- **Multi-language Support**: Support OCR and translation for Chinese, Japanese, and other languages
- **Text Direction Detection**: Automatically identify horizontal/vertical layouts and handle accordingly
- **Speech Bubble Type Analysis**: Use different background processing strategies for different types of speech bubbles
- **Terminology Consistency**: Maintain terminology dictionaries to ensure translation consistency


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