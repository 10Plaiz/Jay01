# Troubleshooting Guide

Common issues and solutions for the 1000 JAY OCR tool.

## 1. "Processing..." hangs or fails
- **Cause**: Network connection issues or the OCR.space API is down.
- **Solution**: Check your internet connection and ensure `https://api.ocr.space` is reachable.

## 2. Empty Text in CSV
- **Cause**: The image might be too blurry, the text too small, or the file size is 0.
- **Solution**: 
  - Ensure images in `schedule_images/` are clear and legible.
  - Verify that the image format is one of: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`.
  - Check if the API returned an error message (this is currently silently handled by returning an empty string in `main.py`).

## 3. `json.decoder.JSONDecodeError`
- **Cause**: The API might have returned an HTML error page instead of JSON (common during server maintenance or when hitting rate limits).
- **Solution**: `main.py` includes a `try...except` block that catches this and returns an empty string, but you can check your API usage on the OCR.space dashboard.

## 4. API Key Issues
- **Cause**: Using the default `helloworld` key which has strict rate limits (typically 10-25 requests per day).
- **Solution**: Set your own API key in the environment:
  ```bash
  export OCR_API_KEY='your_own_key'
  ```
