# Agent Context - 1000 JAY

This file provides high-level context and "rules of engagement" for AI agents (Gemini, Claude, etc.) working on this project.

## Project Summary
A Python-based OCR utility that extracts text from schedule images using the OCR.space API and aggregates results into a CSV.

## Tech Stack
- **Language**: Python 3.12+
- **Libraries**: `requests` (for API calls), `csv`, `json`, `os`.
- **External Service**: OCR.space API.

## Critical Commands
- **Run Extraction**: `python main.py`
- **Install Dependencies**: `pip install requests`
- **Environment Setup**: Create a `.env` file with `OCR_API_KEY=your_key_here`.

## Project Structure
- `main.py`: Entry point, orchestrates file scanning and CSV writing.
- `helper.py`: Wrapper for OCR.space API calls.
- `schedule_images/`: Input directory for source images.
- `schedule_texts.csv`: Output file generated after a run.
- `docs/`: Technical documentation and API references.

## Coding Standards
- Use `snake_case` for all functions and variables.
- Keep `helper.py` purely functional (stateless).
- Ensure all file paths are handled using `os.path.join` for cross-platform compatibility.
