# API Schemas - OCR.space

The project interacts with the [OCR.space API](https://ocr.space/OCRAPI). Below is the expected JSON structure as handled by `main.py`.

## Request Configuration (`helper.py`)
- **Endpoint**: `https://api.ocr.space/parse/image`
- **Method**: POST
- **Payload**:
  - `apikey`: Your OCR.space API key (default: `helloworld`).
  - `language`: Target language (default: `eng`).
  - `isOverlayRequired`: Whether to return text coordinates (default: `False`).

## Expected Response Structure
The `extract_text_from_image` function in `main.py` parses the following structure:

```json
{
  "ParsedResults": [
    {
      "TextOverlay": {
        "Lines": [],
        "HasOverlay": false,
        "Message": ""
      },
      "TextOrientation": "0",
      "FileParseExitCode": 1,
      "ParsedText": "This is the extracted text from the image.\r\nIt may contain line breaks.",
      "ErrorMessage": "",
      "ErrorDetails": ""
    }
  ],
  "OCRExitCode": 1,
  "IsErroredOnProcessing": false,
  "ProcessingTimeInMilliseconds": "500",
  "SearchablePDFURL": ""
}
```

## Key Parsing Logic
- `main.py` looks for the `ParsedResults` key.
- It iterates through each result and extracts the `ParsedText` field.
- If the JSON is malformed or an error occurs during `json.loads()`, the function returns an empty string.
