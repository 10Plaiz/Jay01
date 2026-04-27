---
name: general-rules
description: Enforcement of project-specific development rules for 1000 JAY. Use this skill when planning new changes, verifying implementation necessity, or validating work against the Project Proposal (PRD).
---

# 1000 JAY General Rules

Follow these rules strictly before and after any code modifications.

## Before Implementing Changes
1. **Environment Check**: Verify `.env` exists and contains the required `OCR_API_KEY`.
2. **Necessity Check**: Evaluate if the proposed changes are truly necessary for the current task.
3. **PRD Alignment**: Ensure changes align with the Project Proposal (PRD) located in the `PRD/` directory.

## After Implementing Changes
1. **Validation**: Run the project and verify it functions without errors before considering the task complete.
2. **Standardization**: Ensure all new code adheres to the standards defined in `GEMINI.md`.
