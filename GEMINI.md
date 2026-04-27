# Gemini CLI Rules - 1000 JAY

This file defines the foundational mandates and persistent instructions for the Gemini CLI agent within this workspace. These rules take absolute precedence over general defaults.

## 1. Safety & Security
- **API Keys**: NEVER hardcode API keys. Always use `os.environ.get("OCR_API_KEY")`.
- **Secrets**: Do not commit `.env` files or any file containing credentials.

## 2. Context Efficiency
- **Surgical Edits**: When modifying `main.py` or `helper.py`, use targeted `replace` calls. Do not rewrite entire files for small logic changes.
- **Parallel Reading**: When investigating, read multiple files in parallel to save turns.

## 3. Engineering Standards
- **OCR Validation**: When adding new OCR features, always verify the JSON response structure from OCR.space as it can be deeply nested.
- **Error Handling**: Every API call in `helper.py` must handle potential `requests.exceptions`.
- **Type Hinting**: Prefer adding type hints to new functions in `helper.py`.

## 4. Testing
- **New Features**: Any change to the text extraction logic must be verified with a mock response or a sample image from `schedule_images/`.
