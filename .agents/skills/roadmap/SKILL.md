# Implementation Plan and Methodology (Roadmap)

The project is executed over five focused phases, starting with the foundational data extraction.

## 3.0 Phase 0: OCR Data Extraction (Current State)

*   **A. OCR Engine Implementation:**
    *   Develop `helper.py` to wrap the OCR.space API for robust image-to-text conversion.
    *   Implement `main.py` to batch process schedule images from `schedule_images/`.
*   **B. Data Serialization:**
    *   Extract unstructured schedule text and serialize it into `schedule_texts.csv` for downstream processing.
*   **C. Validation:**
    *   Ensure high accuracy in text extraction from various image formats (.jpg, .png).

## 3.1 Phase 1: Data Initialization and User Input

*   **A. Initial Data Import & Schema Definition:** 
    *   Transform OCR-extracted text from `schedule_texts.csv` into structured member/officer availability data.
    *   Define the exact data model/classes for handling the CSV data in memory.
    *   Develop the parsing logic to load the file accurately.
*   **B. User Segmentation:** 
    *   Implement logic to tag users as Officer or Member for weighted availability analysis, incorporating data from the CSV import.
*   **C. User Onboarding Interface:** 
    *   Develop the front-end file uploader for executive staff to easily load and update the master CSV schedule.

## 3.2 Phase 2: Scheduling Logic (Retrieval/Aggregation) Development

*   **A. Aggregation Engine:** 
    *   Develop the core Python logic to run complex time-slot calculations against the in-memory data structure.
*   **B. Constraint Handling:** 
    *   Implement logic to filter based on user-defined parameters (e.g., minimum duration, required officer presence, preferred days).

## 3.3 Phase 3: RAG Integration and Conversational Layer

*   **A. Query Interpretation:** 
    *   Connect the user's natural language query to the scheduling logic, using Gemini 2.5 Flash to accurately extract scheduling parameters.
*   **B. Response Generation:** 
    *   Integrate the LLM to synthesize the calculated aggregated report into a conversational, actionable recommendation.
*   **C. Alpha Testing:** 
    *   Internal testing by executive staff on real-world scheduling needs to test accuracy and conversational flow.

## 3.4 Phase 4: Final Deployment and Metrics

*   **A. Performance Metrics:** 
    *   Measure key KPIs, including query latency, and Maximization Score (the percentage of potential attendance achieved).
*   **B. Training and Documentation:** 
    *   Create simple guides for all members on how to maintain their availability in the system and for executives on how to update the master CSV file.
*   **C. Production Launch:** 
    *   Deploy the application to all officers and members for daily scheduling operations.
