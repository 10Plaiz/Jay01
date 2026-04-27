"""Parse OCR-extracted schedule CSV into structured schedule entries."""

import csv
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ScheduleEntry:
    """A single class entry in someone's schedule."""
    person: str
    day: str
    time_start: str
    time_end: str
    course: str
    section: str
    room: str


# Canonical time slots from the schedule images
TIME_SLOTS: list[tuple[str, str]] = [
    ("07:00AM", "08:10AM"),
    ("08:10AM", "09:20AM"),
    ("09:20AM", "10:30AM"),
    ("10:30AM", "11:40AM"),
    ("11:40AM", "12:50PM"),
    ("12:50PM", "02:00PM"),
    ("02:00PM", "03:10PM"),
    ("03:10PM", "04:20PM"),
    ("04:20PM", "05:30PM"),
    ("05:30PM", "06:40PM"),
    ("06:40PM", "07:50PM"),
    ("07:50PM", "09:00PM"),
]

DAYS: list[str] = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


def person_from_filename(filename: str) -> str:
    """Extract person name from image filename (strip extension)."""
    return os.path.splitext(os.path.basename(filename))[0]


def load_csv(csv_path: str) -> list[dict]:
    """Load the schedule CSV file and return rows as dicts."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def parse_with_gemini(client, raw_rows: list[dict]) -> list[ScheduleEntry]:
    """Use Gemini to parse raw OCR text into structured schedule entries.

    :param client: An initialized google.genai.Client.
    :param raw_rows: Rows from the CSV, each with 'filename' and 'text' keys.
    :return: A list of ScheduleEntry objects.
    """
    import time

    from google.genai import types

    # Build the prompt with all raw texts
    texts_block = ""
    for row in raw_rows:
        person = person_from_filename(row.get("filename", "Unknown"))
        text = row.get("text", "")
        texts_block += f"\n--- Schedule for {person} ---\n{text}\n"

    prompt = f"""Parse the following OCR text extracted from class schedule images into structured JSON.

Each schedule is a weekly timetable grid with:
- Rows: Time slots (70-minute blocks from 07:00AM to 09:00PM)
- Columns: Monday through Sunday
- Each occupied cell has 3 values stacked: Course Code, Section/Block, Room

The exact time slots are:
07:00AM-08:10AM, 08:10AM-09:20AM, 09:20AM-10:30AM, 10:30AM-11:40AM,
11:40AM-12:50PM, 12:50PM-02:00PM, 02:00PM-03:10PM, 03:10PM-04:20PM,
04:20PM-05:30PM, 05:30PM-06:40PM, 06:40PM-07:50PM, 07:50PM-09:00PM

Return a JSON array of objects. Each object represents ONE occupied cell:
- "person": the schedule owner (e.g., "E", "L", "Ze")
- "day": full day name (e.g., "Monday")
- "time_start": slot start (e.g., "07:00AM")
- "time_end": slot end (e.g., "08:10AM")
- "course": course code (e.g., "CSS152P", "ITS150P", "GED102", "FW04-2")
- "section": section or block (e.g., "BM2", "BM6", "BM10")
- "room": room code (e.g., "MPO304", "ONLINE", "MPOGYM3")

Only include OCCUPIED slots. Skip empty cells.

RAW OCR TEXT:
{texts_block}

Return ONLY a valid JSON array. No markdown fences, no explanation."""

    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    response = None
    last_error = None

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                    contents=prompt,
                )
                if response:
                    break
            except Exception as e:
                last_error = e
                # Check for 503 or "high demand" in error message
                if "503" in str(e) or "high demand" in str(e).lower():
                    print(f"Attempt {attempt+1} failed for {model_name}: 503 Service Unavailable. Retrying...")
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                else:
                    # If it's another error, don't retry this model, maybe try next model
                    print(f"Error with {model_name}: {e}")
                    break
        if response:
            break

    if not response:
        print(f"Gemini API call failed after trying multiple models: {last_error}")
        return []

    entries: list[ScheduleEntry] = []
    try:
        data = json.loads(response.text)
        for item in data:
            entries.append(ScheduleEntry(
                person=str(item.get("person", "Unknown")),
                day=str(item.get("day", "")),
                time_start=str(item.get("time_start", "")),
                time_end=str(item.get("time_end", "")),
                course=str(item.get("course", "")),
                section=str(item.get("section", "")),
                room=str(item.get("room", "")),
            ))
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error parsing Gemini response: {e}")

    return entries


def entries_to_dicts(entries: list[ScheduleEntry]) -> list[dict]:
    """Convert a list of ScheduleEntry to a list of dicts."""
    return [asdict(e) for e in entries]


def build_schedule_context(entries: list[ScheduleEntry]) -> str:
    """Build a human-readable schedule summary for use in LLM prompts.

    Produces a compact, per-person, per-day listing of classes.
    """
    if not entries:
        return "No schedule data available."

    lines: list[str] = []
    persons = sorted(set(e.person for e in entries))

    for person in persons:
        person_entries = [e for e in entries if e.person == person]
        lines.append(f"\n=== Schedule for {person} ===")

        for day in DAYS:
            day_entries = sorted(
                [e for e in person_entries if e.day == day],
                key=lambda x: x.time_start,
            )
            if day_entries:
                lines.append(f"  {day}:")
                for e in day_entries:
                    lines.append(
                        f"    {e.time_start}-{e.time_end}: "
                        f"{e.course} ({e.section}) @ {e.room}"
                    )
            else:
                lines.append(f"  {day}: (no classes)")

    return "\n".join(lines)
