---
name: general-rules
description: Use when prompted with "Antigravity Agent", when modifying ANY code in the 1000 JAY project, or when making architectural decisions.
---

# 1000 JAY: Antigravity Agent Core Directives

## Overview
This skill enforces the absolute rules for the 1000 JAY project under the "Antigravity Agent" persona. It guarantees zero-defect code changes, strict API handling, and surgical precision in edits. This skill is your operating system when working on 1000 JAY.

## When to Use
- You receive a prompt mentioning "Antigravity Agent".
- You are modifying `main.py`, `helper.py`, or any core system file.
- You are implementing new features from the Roadmap (Phase 1-4).
- You are writing tests or adding OCR data extraction features.

## The Antigravity Flow
```dot
digraph antigravity_flow {
    "Task Received" [shape=diamond];
    "Is it a code change?" [shape=diamond];
    "Check .env & PRD" [shape=box];
    "Surgical Edits Only" [shape=box];
    "Run Validation" [shape=box];
    "Answer Directly" [shape=box];

    "Task Received" -> "Is it a code change?";
    "Is it a code change?" -> "Check .env & PRD" [label="yes"];
    "Is it a code change?" -> "Answer Directly" [label="no"];
    "Check .env & PRD" -> "Surgical Edits Only";
    "Surgical Edits Only" -> "Run Validation";
}
```

## Core Engineering Mandates (The Iron Law)

### 1. Surgical Edits & Context Efficiency
**Rule:** NEVER rewrite entire files for small logic changes. Use targeted `replace` operations.
**Why:** Full rewrites break existing functionality, introduce unintended bugs, and waste context window tokens.

### 2. Absolute Security
**Rule:** NEVER hardcode API keys. Always use `os.environ.get("OCR_API_KEY")`.
**Why:** Committing `.env` files or hardcoded keys compromises the system. Security is non-negotiable.

### 3. Bulletproof OCR Validation
**Rule:** Always verify the JSON response structure from OCR.space (specifically the nested `ParsedResults` array).
**Why:** The OCR.space API returns deeply nested JSON that can fail silently or return HTML error pages if rate limits are hit. Parse defensively.

### 4. Resilient Error Handling
**Rule:** Every API call (e.g., in `helper.py`) MUST handle `requests.exceptions.RequestException`.
**Why:** Network calls fail. Unhandled exceptions will crash the batch processor when handling multiple schedule images.

### 5. Strict Type Hinting
**Rule:** All new functions require comprehensive Python type hints.
**Why:** Enables static analysis, improves maintainability, and is crucial for the planned Phase 3 RAG integration with `google-genai`.

### 6. Evidence-Based Testing
**Rule:** Any change to text extraction logic MUST be verified with a mock JSON response or a sample image from the `schedule_images/` directory.
**Why:** Parsing changes cannot be validated by reading code alone. You must observe the output.

## Quick Reference

| Action | Antigravity Requirement |
|--------|-------------------------|
| Adding a function | Must include type hints (`-> str`, `: int`) and docstrings. |
| Making an API call | Must wrap in `try...except requests.exceptions.RequestException`. |
| Updating an existing file | Must use targeted replacements, not full rewrites. |
| Handling credentials | Must use `os.environ.get()` or `.env` file reading. |

## Rationalization Table

Agents under pressure rationalize bad decisions. Do not fall for these.

| Excuse | Reality |
|--------|---------|
| "It's just a small script, I don't need type hints." | Phase 3 RAG integration requires strict schemas. Type hints are mandatory. |
| "The API key is only for testing, I'll hardcode it." | Hardcoded keys leak. Use `.env` or `os.environ`. |
| "I'll rewrite the file to make it cleaner." | Surgical edits only. Full rewrites violate context efficiency and risk regressions. |
| "The OCR JSON is standard, `json.loads` is enough." | OCR.space can return HTML error pages or nested error structures. Validate defensively. |
| "I'll test it later once the whole feature is built." | Evidence-based testing is required immediately for extraction logic. |

## Red Flags - STOP and Start Over

If you catch yourself doing any of the following, STOP immediately, delete your planned changes, and start over:
- You are about to write a full file replacement for a minor logic tweak.
- You are ignoring `requests.exceptions` during network operations.
- You are testing parsing logic without a mock JSON response or sample image.
- You are not checking alignment with the `PRD/Project Proposal (PRD).pdf` or `docs/api_schemas.md`.

**All of these mean: Delete the change. Start over with Antigravity precision.**