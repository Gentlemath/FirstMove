from __future__ import annotations

from typing import Literal, TypedDict

from app.schemas.workspace import ToolShortcut


class ToolShortcutConfig(TypedDict):
    key: str
    label: str
    href: str
    kind: Literal["web", "app"]


# Shared defaults stay web-first. Local app shortcuts should be a separate
# user-specific layer so the default API output remains portable across machines.
_TOOL_SHORTCUTS: dict[str, ToolShortcutConfig] = {
    "gmail": {
        "key": "gmail",
        "label": "Gmail",
        "href": "https://mail.google.com",
        "kind": "web",
    },
    "google calendar": {
        "key": "google-calendar",
        "label": "Google Calendar",
        "href": "https://calendar.google.com",
        "kind": "web",
    },
    "google docs": {
        "key": "google-docs",
        "label": "Google Docs",
        "href": "https://docs.google.com/document",
        "kind": "web",
    },
    "google sheets": {
        "key": "google-sheets",
        "label": "Google Sheets",
        "href": "https://docs.google.com/spreadsheets",
        "kind": "web",
    },
    "google slides": {
        "key": "google-slides",
        "label": "Google Slides",
        "href": "https://docs.google.com/presentation",
        "kind": "web",
    },
    "google drive": {
        "key": "google-drive",
        "label": "Google Drive",
        "href": "https://drive.google.com",
        "kind": "web",
    },
    "notion": {
        "key": "notion",
        "label": "Notion",
        "href": "https://www.notion.so",
        "kind": "web",
    },
    "slack": {
        "key": "slack",
        "label": "Slack",
        "href": "https://app.slack.com/client",
        "kind": "web",
    },
    "github": {
        "key": "github",
        "label": "GitHub",
        "href": "https://github.com",
        "kind": "web",
    },
    "coding": {
        "key": "coding",
        "label": "vscode",
        "href": "https://code.visualstudio.com",
        "kind": "app",
    },
    "figma": {
        "key": "figma",
        "label": "Figma",
        "href": "https://www.figma.com/files",
        "kind": "web",
    },
    "zoom": {
        "key": "zoom",
        "label": "Zoom",
        "href": "https://zoom.us",
        "kind": "web",
    },
}

_TOOL_ALIASES = {
    "apple calendar": "google calendar",
    "calendar": "google calendar",
    "calendar app": "google calendar",
    "docs": "google docs",
    "document": "google docs",
    "drive": "google drive",
    "email": "gmail",
    "figjam": "figma",
    "apple mail": "gmail",
    "mac calender": "google calendar",
    "mac calendar": "google calendar",
    "mac mail": "gmail",
    "mail": "gmail",
    "meeting notes": "notion",
    "metrics sheet": "google sheets",
    "notes": "notion",
    "sheet": "google sheets",
    "sheets": "google sheets",
    "slides": "google slides",
    "spreadsheet": "google sheets",
}


def supported_tool_names() -> list[str]:
    return [shortcut["label"] for shortcut in _TOOL_SHORTCUTS.values()]


def resolve_tool_shortcuts(tool_names: list[str]) -> list[ToolShortcut]:
    shortcuts: list[ToolShortcut] = []
    seen: set[str] = set()

    for name in tool_names:
        canonical_key = _canonicalize_tool_name(name)
        if not canonical_key or canonical_key in seen:
            continue

        shortcut = _TOOL_SHORTCUTS.get(canonical_key)
        if shortcut is None:
            continue

        seen.add(canonical_key)
        shortcuts.append(ToolShortcut(**shortcut))

    return shortcuts


def _canonicalize_tool_name(name: str) -> str | None:
    cleaned = name.strip().casefold()
    if not cleaned:
        return None

    return _TOOL_ALIASES.get(cleaned, cleaned)
