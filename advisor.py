"""Gemini 2.5 Flash integration — scheduling advisor LLM wrapper."""

import json
import os

from google import genai
from google.genai import types


def init_gemini_client() -> genai.Client:
    """Initialize the Gemini API client using GEMINI_API_KEY env var.

    :raises ValueError: If GEMINI_API_KEY is not set.
    :return: An authenticated genai.Client.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to your .env file or set it in your environment."
        )
    return genai.Client(api_key=api_key)


def build_system_prompt(schedule_context: str) -> str:
    """Build the system prompt that turns Gemini into a scheduling advisor.

    :param schedule_context: Human-readable schedule data string.
    :return: The full system prompt.
    """
    return f"""You are an intelligent scheduling advisor chatbot. You analyze university/college class schedule data and help users:
- Find available (free) time slots for specific people
- Check class schedules and conflicts
- Count slot attendance and occupancy
- Find common free time across multiple people
- Recommend the best meeting times or schedule changes

SCHEDULE DATA:
{schedule_context}

RESPONSE FORMAT:
You must ALWAYS respond with a valid JSON object containing these keys:

1. "query_params": A structured query object with:
   - "action": One of: "find_free_slots", "find_busy_slots", "search_course", "attendance_count", "common_free", "top_slots"
   - Additional fields depending on the action:
     - find_free_slots / find_busy_slots: "person" (required), "day" (optional, use full name like "Monday" or "all")
     - search_course: "course" (the course code to search)
     - attendance_count: no extra params needed
     - common_free: "persons" (optional list of names, omit to check all)
     - top_slots: "top_n" (optional, default 5)

2. "explanation": A friendly, detailed natural language explanation of your analysis and findings. Reference specific data from the schedules. Be thorough but concise.

3. "recommendations": An array of specific, actionable recommendation strings.

RULES:
- Person names are case-sensitive and must match exactly the names in the schedule data.
- For "day", use full day names (Monday, Tuesday, etc.) or "all" for every day.
- Always provide a meaningful explanation and at least one recommendation.
- If the user asks a conversational or general question, still pick the most relevant action and provide helpful schedule insights.
- Respond ONLY with valid JSON. No markdown code fences, no extra text outside the JSON."""


def ask_advisor(
    client: genai.Client,
    messages: list[dict],
    schedule_context: str,
) -> dict:
    """Send a user query to the Gemini scheduling advisor.

    :param client: An initialized genai.Client.
    :param messages: Chat history, each dict has 'role' and 'content'.
    :param schedule_context: The formatted schedule data string.
    :return: Parsed JSON response with query_params, explanation, recommendations.
    """
    system_prompt = build_system_prompt(schedule_context)

    # Build the contents list from chat history
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            )
        )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                response_mime_type="application/json",
            ),
            contents=contents,
        )
    except Exception as e:
        return {
            "query_params": {"action": "unknown"},
            "explanation": f"Sorry, I encountered an error contacting the Gemini API: {e}",
            "recommendations": ["Please check your API key and internet connection."],
        }

    try:
        result = json.loads(response.text)
        # Ensure all expected keys exist
        result.setdefault("query_params", {"action": "unknown"})
        result.setdefault("explanation", "")
        result.setdefault("recommendations", [])
        return result
    except (json.JSONDecodeError, TypeError):
        return {
            "query_params": {"action": "unknown"},
            "explanation": response.text if response.text else "No response received.",
            "recommendations": [],
        }
