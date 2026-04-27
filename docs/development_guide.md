# Development Guide

This guide explains how to maintain and extend the 1000 JAY OCR tool.

## Core Workflow
1. **Scanning**: `main.py` uses `os.listdir` to find images in the `schedule_images/` folder.
2. **Extraction**: For each image, `extract_text_from_image` is called.
3. **API Call**: `helper.py` handles the low-level `requests` call to the OCR.space service.
4. **Aggregation**: Results are appended to `schedule_texts.csv` using the `csv` module.

## How to Extend

### Supporting New File Formats
To add support for more formats (like PDF), update the `files` list comprehension in `main.py`:
```python
files = sorted(f for f in os.listdir(IMAGES_DIR)
               if f.lower().endswith((".png", ".jpg", ".pdf")))
```
*Note: OCR.space free tier has specific limits for PDF processing.*

### Adding Text Coordinates
If you need to know *where* the text is in the image:
1. Modify `ocr_space_file` in `helper.py` to set `overlay=True`.
2. Update `extract_text_from_image` in `main.py` to parse the `TextOverlay` object in the JSON response.

### Improving Error Handling
Currently, `main.py` suppresses errors to keep the CSV generation running. For production use, consider logging `j.get("ErrorMessage")` when `IsErroredOnProcessing` is `true`.

## Coding Standards
- **Functionality**: Keep `helper.py` as a thin wrapper for the API.
- **Environment**: Always prefer `os.environ` for sensitive configurations like API keys.
- **Cross-Platform**: Use `os.path.join` for all file path operations.
