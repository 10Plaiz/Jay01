"""Query engine for filtering and aggregating structured schedule data."""

from schedule_parser import ScheduleEntry, TIME_SLOTS, DAYS


def find_free_slots(
    entries: list[ScheduleEntry],
    person: str,
    day: str | None = None,
) -> list[dict]:
    """Find free (unoccupied) time slots for a given person.

    :param entries: All schedule entries.
    :param person: Person name to check.
    :param day: Optional day filter. None = all days.
    :return: List of free slot dicts.
    """
    results: list[dict] = []
    target_days = [day] if day else DAYS

    for d in target_days:
        occupied = {
            (e.time_start, e.time_end)
            for e in entries
            if e.person.lower() == person.lower()
            and e.day.lower() == d.lower()
        }
        for ts, te in TIME_SLOTS:
            if (ts, te) not in occupied:
                results.append({
                    "person": person,
                    "day": d,
                    "time_start": ts,
                    "time_end": te,
                    "status": "FREE",
                })

    return results


def find_busy_slots(
    entries: list[ScheduleEntry],
    person: str,
    day: str | None = None,
) -> list[dict]:
    """Find busy (occupied) time slots for a given person.

    :param entries: All schedule entries.
    :param person: Person name to check.
    :param day: Optional day filter. None = all days.
    :return: List of busy slot dicts with class details.
    """
    results: list[dict] = []
    target_days = [day] if day else DAYS

    for d in target_days:
        day_entries = [
            e for e in entries
            if e.person.lower() == person.lower()
            and e.day.lower() == d.lower()
        ]
        for e in sorted(day_entries, key=lambda x: x.time_start):
            results.append({
                "person": e.person,
                "day": e.day,
                "time_start": e.time_start,
                "time_end": e.time_end,
                "course": e.course,
                "section": e.section,
                "room": e.room,
                "status": "BUSY",
            })

    return results


def search_by_course(
    entries: list[ScheduleEntry],
    course_code: str,
) -> list[dict]:
    """Find all occurrences of a specific course across all schedules.

    :param entries: All schedule entries.
    :param course_code: Course code (or partial) to search for.
    :return: Matching entries as dicts.
    """
    return [
        {
            "person": e.person,
            "day": e.day,
            "time_start": e.time_start,
            "time_end": e.time_end,
            "course": e.course,
            "section": e.section,
            "room": e.room,
        }
        for e in entries
        if course_code.lower() in e.course.lower()
    ]


def get_attendance_by_slot(entries: list[ScheduleEntry]) -> list[dict]:
    """Count how many people have classes in each time slot per day.

    :param entries: All schedule entries.
    :return: Sorted list (descending by count) of slot attendance dicts.
    """
    counts: dict[tuple, dict] = {}
    for e in entries:
        key = (e.day, e.time_start, e.time_end)
        if key not in counts:
            counts[key] = {
                "day": e.day,
                "time_start": e.time_start,
                "time_end": e.time_end,
                "count": 0,
                "persons": [],
            }
        counts[key]["count"] += 1
        if e.person not in counts[key]["persons"]:
            counts[key]["persons"].append(e.person)

    return sorted(counts.values(), key=lambda x: x["count"], reverse=True)


def find_common_free_slots(
    entries: list[ScheduleEntry],
    persons: list[str] | None = None,
) -> list[dict]:
    """Find time slots where all specified persons are simultaneously free.

    :param entries: All schedule entries.
    :param persons: List of person names. None = all persons in the data.
    :return: List of commonly free slot dicts.
    """
    all_persons = persons or sorted(set(e.person for e in entries))
    results: list[dict] = []

    for day in DAYS:
        for ts, te in TIME_SLOTS:
            everyone_free = True
            for person in all_persons:
                is_occupied = any(
                    e.time_start == ts
                    and e.time_end == te
                    and e.day.lower() == day.lower()
                    for e in entries
                    if e.person.lower() == person.lower()
                )
                if is_occupied:
                    everyone_free = False
                    break
            if everyone_free:
                results.append({
                    "day": day,
                    "time_start": ts,
                    "time_end": te,
                    "free_persons": list(all_persons),
                    "status": "ALL_FREE",
                })

    return results


def get_top_slots(
    entries: list[ScheduleEntry],
    top_n: int = 5,
) -> list[dict]:
    """Get the top N busiest time slots ranked by attendance count.

    :param entries: All schedule entries.
    :param top_n: Number of top slots to return.
    :return: Top N attendance slot dicts.
    """
    attendance = get_attendance_by_slot(entries)
    return attendance[:top_n]


def execute_query(entries: list[ScheduleEntry], query_params: dict) -> dict:
    """Route structured query parameters to the appropriate engine function.

    :param entries: All schedule entries.
    :param query_params: Dict with 'action' and relevant filters.
    :return: Dict with 'action' and 'results' keys.
    """
    action = query_params.get("action", "")
    person = query_params.get("person", "")
    day = query_params.get("day")
    course = query_params.get("course", "")
    top_n = query_params.get("top_n", 5)
    persons = query_params.get("persons", [])

    # Treat "all" as no filter
    if day and day.lower() == "all":
        day = None

    dispatch = {
        "find_free_slots": lambda: {
            "action": action,
            "results": find_free_slots(entries, person, day),
        },
        "find_busy_slots": lambda: {
            "action": action,
            "results": find_busy_slots(entries, person, day),
        },
        "search_course": lambda: {
            "action": action,
            "results": search_by_course(entries, course),
        },
        "attendance_count": lambda: {
            "action": action,
            "results": get_attendance_by_slot(entries),
        },
        "common_free": lambda: {
            "action": action,
            "results": find_common_free_slots(
                entries, persons if persons else None
            ),
        },
        "top_slots": lambda: {
            "action": action,
            "results": get_top_slots(entries, top_n),
        },
    }

    handler = dispatch.get(action)
    if handler:
        return handler()

    return {
        "action": "unknown",
        "results": [],
        "error": f"Unknown action: {action}",
    }
