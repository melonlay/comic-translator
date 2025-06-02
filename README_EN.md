# Comic Translator

A comprehensive comic translation tool that supports automatic text detection, extraction, translation, and re-embedding.

## Features

1. **Text Box Detection** - Automatically detect text box regions in comics
2. **Text Extraction** - Extract text content using OCR technology
3. **Smart Translation** - Context-aware translation using Google Gemini API
4. **Terminology Management** - Maintain translation dictionaries for character names, locations, cultural settings
5. **Intelligent Background Repair** - Use image inpainting techniques to completely remove original text and naturally reconstruct backgrounds
6. **Multi-directional Text Support** - Support both horizontal and vertical text layouts
7. **Speech Bubble Type Recognition** - Automatically identify different types of speech bubbles (pure white, textured, transparent)

## Installation Steps

### 1. Clone this repository (with submodules)

```bash
git clone --recurse-submodules <repo URL>
cd comic_translator
```

Or if you've already cloned the main repository:

```bash
git clone <repo URL>
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
export GOOGLE_API_KEY="your_api_key_here"
```

Or in Windows PowerShell:
```powershell
$env:GOOGLE_API_KEY="your_api_key_here"
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

## Technical Features

- **Intelligent Background Repair**: Uses OpenCV image inpainting algorithms to completely remove text traces
- **Multi-language Support**: Supports OCR and translation for Chinese, Japanese, and other languages
- **Text Direction Detection**: Automatically recognizes horizontal/vertical layouts and processes accordingly
- **Speech Bubble Type Analysis**: Uses different background processing strategies for different types of speech bubbles
- **Terminology Consistency**: Maintains terminology dictionaries to ensure translation consistency

## Git Submodule Management

This project uses git submodule to manage the comic-text-detector dependency. Related commands:

```bash
# Initialize and update submodule
git submodule update --init --recursive

# Update submodule to latest version
git submodule update --remote

# Check submodule status
git submodule status

# Execute git operations within submodule directory
cd comic-text-detector
git log --oneline -5
```

## License

This project is licensed under **GNU General Public License v3.0 (GPLv3)**.

Since this project uses the GPLv3-licensed comic-text-detector module, according to GPLv3's copyleft requirements, the entire project must use GPLv3 license.

This means:
- You are free to use, modify, and distribute this software
- Any derivative works based on this software must also use GPLv3 license
- You must provide the complete source code
- Please refer to the [LICENSE](LICENSE) file for detailed terms

## Author

Professional Python Engineer

## Contributing

Pull requests and issue reports are welcome. Please ensure your contributions comply with GPLv3 license terms.

## Related Projects

- [comic-text-detector](https://github.com/dmMaze/comic-text-detector) - Core module for text detection (GPLv3) 