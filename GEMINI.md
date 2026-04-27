# Gemini CLI Mandates - 1000 JAY

This file defines the foundational mandates for all agents working in this workspace. These rules take absolute precedence.

## 1. Mandatory Skill Activation
- **CRITICAL**: You MUST activate the `general-rules` skill (`.agents/skills/general-rules/SKILL.md`) at the very beginning of EVERY session and before performing any code modification or architectural task.
- This skill contains the "Antigravity Agent" persona and core engineering mandates.

## 2. Foundational Safety (Always Active)
- **API Keys**: NEVER hardcode API keys. Always use `os.environ.get("OCR_API_KEY")`.
- **Secrets**: Do not commit `.env` files or any file containing credentials.

## 3. Context Efficiency
- **Surgical Edits**: Use targeted `replace` calls for all modifications. Avoid full file rewrites.
- **Parallel Reading**: Read multiple files in parallel to save turns.
