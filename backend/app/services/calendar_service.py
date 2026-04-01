from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.schemas.workspace import CalendarDayResponse, FixedBlock

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    Request = None
    Credentials = None
    build = None


def get_calendar_day(target_date: date | None = None) -> CalendarDayResponse:
    resolved_date = target_date or date.today()

    if _google_calendar_is_configured():
        try:
            google_blocks = _fetch_google_fixed_blocks(resolved_date)
        except Exception as exc:
            print(f"[google_calendar] Failed to fetch calendar events: {exc}")
            google_blocks = None

        if google_blocks is not None:
            return CalendarDayResponse(
                date=resolved_date.isoformat(),
                connected=True,
                source="google",
                fixed_blocks=google_blocks,
            )

    return CalendarDayResponse(
        date=resolved_date.isoformat(),
        connected=False,
        source="demo",
        fixed_blocks=_demo_fixed_blocks(),
    )


def get_calendar_upcoming(days_ahead: int = 7) -> CalendarDayResponse:
    """Fetch upcoming events that haven't happened yet."""
    today = date.today()

    if _google_calendar_is_configured():
        try:
            google_blocks = _fetch_google_upcoming_blocks(days_ahead)
        except Exception as exc:
            print(f"[google_calendar] Failed to fetch upcoming calendar events: {exc}")
            google_blocks = None

        if google_blocks is not None:
            return CalendarDayResponse(
                date=today.isoformat(),
                connected=True,
                source="google",
                fixed_blocks=google_blocks,
            )

    return CalendarDayResponse(
        date=today.isoformat(),
        connected=False,
        source="demo",
        fixed_blocks=_demo_fixed_blocks(),
    )


def _google_calendar_is_configured() -> bool:
    required_values = [
        os.getenv("GOOGLE_CALENDAR_ID"),
        os.getenv("GOOGLE_CALENDAR_TOKEN_PATH"),
    ]
    return (
        all(required_values)
        and Credentials is not None
        and Request is not None
        and build is not None
    )


def _fetch_google_fixed_blocks(target_date: date) -> list[FixedBlock] | None:
    token_path = os.getenv("GOOGLE_CALENDAR_TOKEN_PATH")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    timezone_name = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "America/Los_Angeles")

    if not token_path or not calendar_id:
        return None

    credentials = _load_google_credentials(token_path)
    service = build("calendar", "v3", credentials=credentials)

    start_of_day = datetime.combine(target_date, time.min, tzinfo=ZoneInfo(timezone_name))
    end_of_day = datetime.combine(target_date, time.max, tzinfo=ZoneInfo(timezone_name))

    response = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    items = response.get("items", [])
    now = datetime.now(tz=ZoneInfo(timezone_name))

    # Filter out events that have already ended
    future_events = []
    for event in items:
        end_value = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
        if end_value:
            end_time = datetime.fromisoformat(end_value.replace("Z", "+00:00"))
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=ZoneInfo(timezone_name))
            if end_time > now:
                future_events.append(event)

    return [
        _event_to_fixed_block(event, index, timezone_name)
        for index, event in enumerate(future_events, start=1)
    ]


def _fetch_google_upcoming_blocks(days_ahead: int = 7) -> list[FixedBlock] | None:
    """Fetch upcoming events from now until days_ahead."""
    token_path = os.getenv("GOOGLE_CALENDAR_TOKEN_PATH")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    timezone_name = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "America/Los_Angeles")

    if not token_path or not calendar_id:
        return None

    credentials = _load_google_credentials(token_path)
    service = build("calendar", "v3", credentials=credentials)

    # Start from now
    now = datetime.now(tz=ZoneInfo(timezone_name))
    # End at end of day N days from now
    end_date = date.today() + timedelta(days=days_ahead)
    end_of_period = datetime.combine(end_date, time.max, tzinfo=ZoneInfo(timezone_name))

    response = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=end_of_period.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    items = response.get("items", [])
    return [
        _event_to_fixed_block(event, index, timezone_name)
        for index, event in enumerate(items, start=1)
    ]



def _load_google_credentials(token_path: str) -> Credentials:
    if Credentials is None or Request is None:
        raise RuntimeError("Google Calendar dependencies are not installed.")

    if not os.path.exists(token_path):
        raise FileNotFoundError(f"Google token file not found: {token_path}")

    credentials = Credentials.from_authorized_user_file(token_path, GOOGLE_CALENDAR_SCOPES)

    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(credentials.to_json())
        else:
            raise RuntimeError(
                "Google Calendar token is invalid and cannot be refreshed. "
                "Please regenerate the token."
            )

    return credentials


def _event_to_fixed_block(event: dict, index: int, timezone_name: str) -> FixedBlock:
    start_value = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
    end_value = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")

    start_time = None
    end_time = None
    time_label = "All day"

    if start_value and end_value:
        start_time = start_value
        end_time = end_value

        if "T" in str(start_value) and "T" in str(end_value):
            time_label = f"{_format_clock_time(start_value, timezone_name)}–{_format_clock_time(end_value, timezone_name)}"
        else:
            time_label = "All day"

    attendees = []
    for attendee in event.get("attendees", []):
        display = attendee.get("displayName") or attendee.get("email")
        if display:
            attendees.append(display)

    online_link = _extract_online_link(event)

    organizer = None
    if event.get("organizer"):
        organizer = event["organizer"].get("email") or event["organizer"].get("displayName")

    status = event.get("status")

    return FixedBlock(
        block_id=f"block-{index}",
        title=event.get("summary", "Untitled event"),
        start_time=start_time,
        end_time=end_time,
        time=time_label,
        location=event.get("location"),
        description=event.get("description"),
        attendees=attendees,
        online_link=online_link,
        html_link=event.get("htmlLink"),
        organizer=organizer,
        status=status,
        note=event.get("description"),
    )


def _extract_online_link(event: dict) -> str | None:
    hangout = event.get("hangoutLink")
    if hangout:
        return hangout

    conference_data = event.get("conferenceData", {})
    entry_points = conference_data.get("entryPoints", [])
    for point in entry_points:
        if point.get("uri"):
            return point.get("uri")

    return None


def _format_clock_time(timestamp: str, timezone_name: str) -> str:
    normalized = timestamp.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(ZoneInfo(timezone_name))

    hour = parsed.strftime("%I").lstrip("0") or "0"
    return f"{hour}:{parsed.strftime('%M')}"


def _demo_fixed_blocks() -> list[FixedBlock]:
    return [
        FixedBlock(
            block_id="block-1",
            title="Team Sync",
            time="10:00–10:30",
            location="Google Meet",
            note="notes ready",
        ),
        FixedBlock(
            block_id="block-2",
            title="Project Review",
            time="3:00–4:00",
            location="Zoom",
            note="deck linked",
        ),
    ]