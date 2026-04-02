from __future__ import annotations

import json
import re
from typing import Any, Literal, cast

from app.schemas.workspace import FixedBlock, TaskCard
from app.services.tool_registry import resolve_tool_shortcuts, supported_tool_names

SectionName = Literal["now", "ready", "later"]

_GENERIC_FIRST_STEP_PHRASES = (
    "start working on",
    "work on this",
    "begin the task",
    "make progress on",
    "get started",
    "take the first step",
    "start by",
    "begin by",
)
_GENERIC_WHY_PHRASES = {
    "this is important",
    "it is important",
    "this matters",
    "important for progress",
}
_GENERIC_HINT_PHRASES = (
    "stay focused",
    "do your best",
    "one step at a time",
    "be consistent",
    "use a consistent routine",
    "take it one step at a time",
    "keep the momentum going",
    "stay organized",
    "take breaks",
    "manage your time",
)


def normalize_tasks(raw_tasks: list[str], raw_task_text: str | None) -> list[str]:
    cleaned_raw_tasks = [_clean_task_text(task) for task in raw_tasks]
    cleaned_from_text = _extract_tasks_from_text(raw_task_text)

    combined_tasks = [task for task in [*cleaned_raw_tasks, *cleaned_from_text] if task]
    return _dedupe_preserving_order(combined_tasks)


def build_generation_prompt(
    resolved_date: str,
    normalized_tasks: list[str],
    raw_task_text: str | None,
    fixed_blocks: list[FixedBlock],
) -> str:
    calendar_summary = summarize_calendar_constraints(fixed_blocks)
    calendar_context = format_calendar_context(fixed_blocks)
    task_lines = "\n".join(
        f"{index}. {task}" for index, task in enumerate(normalized_tasks, start=1)
    )
    original_notes = raw_task_text.strip() if raw_task_text and raw_task_text.strip() else "None provided."
    supported_tools = ", ".join(supported_tool_names())

    return f"""Prepare task cards for {resolved_date}.

Day constraints summary:
{calendar_summary}

Calendar events:
{calendar_context}

Input tasks:
{task_lines}

Original task notes:
{original_notes}

Return a JSON array with exactly {len(normalized_tasks)} objects and keep the same task order.
Each object must include:
- task_index (integer): 1-based index of the input task
- title (string): concise action-oriented task title
- why_it_matters (string): one sentence with a concrete payoff, dependency, or risk
- first_step (string): smallest visible action that starts the task in under 5 minutes
- hint (string): short tactical advice, ideally shaped by calendar constraints
- tools (array of strings): 0 to 4 canonical tool names chosen only from: {supported_tools}
- section (string): exactly one of "now", "ready", or "later"
"""


def build_repair_prompt(
    resolved_date: str,
    normalized_tasks: list[str],
    raw_task_text: str | None,
    fixed_blocks: list[FixedBlock],
    invalid_response: str,
) -> str:
    original_prompt = build_generation_prompt(
        resolved_date=resolved_date,
        normalized_tasks=normalized_tasks,
        raw_task_text=raw_task_text,
        fixed_blocks=fixed_blocks,
    )
    return f"""{original_prompt}

The previous response was invalid. Fix it so it satisfies every requirement.
Return only valid JSON with no markdown fences and no explanation.

Previous invalid response:
{invalid_response}
"""


def parse_llm_task_cards(
    response_text: str,
    normalized_tasks: list[str],
    fixed_blocks: list[FixedBlock],
) -> list[TaskCard]:
    payload = _extract_json_payload(response_text)

    try:
        task_data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response as JSON: {exc}") from exc

    items = _normalize_task_data(task_data, expected_count=len(normalized_tasks))
    ordered_items = _order_items_by_task_index(items, expected_count=len(normalized_tasks))

    task_cards: list[TaskCard] = []
    for index, item in enumerate(ordered_items, start=1):
        source_task = normalized_tasks[index - 1]
        section = _coerce_section(item.get("section"), index)

        title = _coerce_title(item.get("title")) or source_task
        why_it_matters = _coerce_why_it_matters(item.get("why_it_matters"))
        if not why_it_matters:
            why_it_matters = _infer_why_it_matters(source_task)

        first_step = _coerce_first_step(item.get("first_step"))
        if not first_step:
            first_step = _infer_first_step(source_task)

        hint = _coerce_hint(item.get("hint"))
        if not hint:
            hint = _infer_hint(source_task, fixed_blocks)

        tool_names = _coerce_tool_names(item.get("tools"))
        if not tool_names:
            tool_names = _infer_tool_names(source_task)
        tools = resolve_tool_shortcuts(tool_names)
        if not tools:
            tools = resolve_tool_shortcuts(_infer_tool_names(source_task))

        task_cards.append(
            TaskCard(
                task_id=f"task-{index}",
                title=title,
                why_it_matters=why_it_matters,
                first_step=first_step,
                hint=hint,
                tools=tools,
                section=section,
                status=section,
            )
        )

    return task_cards


def generate_rule_based_task_cards(
    normalized_tasks: list[str],
    fixed_blocks: list[FixedBlock],
) -> list[TaskCard]:
    return [
        TaskCard(
            task_id=f"task-{index}",
            title=task_title,
            why_it_matters=_infer_why_it_matters(task_title),
            first_step=_infer_first_step(task_title),
            hint=_infer_hint(task_title, fixed_blocks),
            tools=resolve_tool_shortcuts(_infer_tool_names(task_title)),
            section=_assign_section(index),
            status=_assign_section(index),
        )
        for index, task_title in enumerate(normalized_tasks, start=1)
    ]


def format_calendar_context(fixed_blocks: list[FixedBlock]) -> str:
    if not fixed_blocks:
        return "No fixed calendar events."

    context_lines = []
    for block in fixed_blocks:
        time_range = f"{block.start_time or block.time} - {block.end_time or ''}".rstrip()
        location = f" at {block.location}" if block.location else ""
        context_lines.append(f"- {block.title}: {time_range}{location}")

    return "\n".join(context_lines)


def summarize_calendar_constraints(fixed_blocks: list[FixedBlock]) -> str:
    if not fixed_blocks:
        return "- No fixed blocks. The day is mostly open."

    summary_lines = [f"- {len(fixed_blocks)} fixed block(s) already on the calendar."]

    first_block = fixed_blocks[0]
    summary_lines.append(f"- First visible block: {first_block.title} ({first_block.time}).")

    meeting_like_count = sum(1 for block in fixed_blocks if _is_meeting_like(block.title))
    if meeting_like_count:
        summary_lines.append(
            f"- {meeting_like_count} meeting-like block(s); prep that changes those outcomes should move earlier."
        )

    if any(block.location or block.online_link for block in fixed_blocks):
        summary_lines.append("- Some fixed blocks require location or call-link context switching.")

    return "\n".join(summary_lines)


def _normalize_task_data(task_data: Any, expected_count: int) -> list[dict[str, Any]]:
    if isinstance(task_data, dict):
        items = [task_data]
    elif isinstance(task_data, list):
        items = task_data
    else:
        raise ValueError("LLM response is not a JSON object or array.")

    if len(items) != expected_count:
        raise ValueError(
            f"LLM returned {len(items)} task objects; expected {expected_count}."
        )

    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Every LLM task item must be a JSON object.")
        normalized_items.append(item)

    return normalized_items


def _order_items_by_task_index(
    items: list[dict[str, Any]],
    expected_count: int,
) -> list[dict[str, Any]]:
    indexes = [item.get("task_index") for item in items]
    if not all(isinstance(index, int) for index in indexes):
        return items

    integer_indexes = cast(list[int], indexes)
    if set(integer_indexes) != set(range(1, expected_count + 1)):
        return items

    return sorted(items, key=lambda item: cast(int, item["task_index"]))


def _extract_json_payload(response_text: str) -> str:
    stripped = response_text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    if stripped.startswith("[") or stripped.startswith("{"):
        return stripped

    array_start = stripped.find("[")
    array_end = stripped.rfind("]")
    if array_start != -1 and array_end > array_start:
        return stripped[array_start : array_end + 1].strip()

    object_start = stripped.find("{")
    object_end = stripped.rfind("}")
    if object_start != -1 and object_end > object_start:
        return stripped[object_start : object_end + 1].strip()

    raise ValueError("Could not find a JSON payload in the LLM response.")


def _clean_task_text(task: str) -> str:
    cleaned = task.strip()
    cleaned = re.sub(r"^\s*[-*•]\s*", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[.)]\s*", "", cleaned)
    cleaned = re.sub(r"^\s*\[\s?[xX]?\s?\]\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_tasks_from_text(raw_task_text: str | None) -> list[str]:
    if not raw_task_text or not raw_task_text.strip():
        return []

    lines = [_clean_task_text(line) for line in raw_task_text.splitlines()]
    line_tasks = [line for line in lines if line]
    if len(line_tasks) >= 2:
        return line_tasks

    if any(separator in raw_task_text for separator in (";", "•")):
        inline_tasks = [
            _clean_task_text(part)
            for part in re.split(r"\s*[;•]\s*", raw_task_text)
        ]
        inline_tasks = [task for task in inline_tasks if task]
        if len(inline_tasks) >= 2:
            return inline_tasks

    single_task = _clean_task_text(raw_task_text)
    return [single_task] if single_task else []


def _dedupe_preserving_order(tasks: list[str]) -> list[str]:
    deduped_tasks: list[str] = []
    seen: set[str] = set()

    for task in tasks:
        key = task.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped_tasks.append(task)

    return deduped_tasks


def _default_section(index: int) -> SectionName:
    if index == 1:
        return "now"
    if index <= 3:
        return "ready"
    return "later"


def _assign_section(index: int) -> SectionName:
    return _default_section(index)


def _coerce_section(value: object, index: int) -> SectionName:
    if value in {"now", "ready", "later"}:
        return cast(SectionName, value)
    return _default_section(index)


def _coerce_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _coerce_title(value: object) -> str:
    title = _coerce_text(value)
    if not title:
        return ""
    if re.fullmatch(r"task\s*\d+", title, flags=re.IGNORECASE):
        return ""
    return title


def _coerce_why_it_matters(value: object) -> str:
    text = _coerce_text(value)
    if not text:
        return ""
    if text.casefold() in _GENERIC_WHY_PHRASES:
        return ""
    return text


def _coerce_first_step(value: object) -> str:
    text = _coerce_text(value)
    if not text:
        return ""
    lowered = text.casefold()
    if any(phrase in lowered for phrase in _GENERIC_FIRST_STEP_PHRASES):
        return ""
    if _is_overly_generic_instruction(text):
        return ""
    return text


def _coerce_hint(value: object) -> str:
    text = _coerce_text(value)
    if not text:
        return ""
    lowered = text.casefold()
    if any(phrase in lowered for phrase in _GENERIC_HINT_PHRASES):
        return ""
    if _is_overly_generic_instruction(text):
        return ""
    return text


def _coerce_tool_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    tools: list[str] = []
    seen: set[str] = set()
    for item in value:
        tool = _coerce_text(item)
        if not tool:
            continue
        key = tool.casefold()
        if key in seen:
            continue
        seen.add(key)
        tools.append(tool)

    return tools[:4]


def _is_meeting_like(title: str) -> bool:
    lowered = title.casefold()
    return any(word in lowered for word in ("meeting", "review", "sync", "call", "interview"))


def _infer_why_it_matters(task_title: str) -> str:
    lowered = task_title.lower()

    if "recruit" in lowered or "interview" in lowered:
        return "Keeps the external process moving and reduces follow-up risk."
    if "spec" in lowered or "doc" in lowered or "write" in lowered:
        return "Clarifies the work so execution gets easier for the rest of the day."
    if "review" in lowered or "meeting" in lowered or "slide" in lowered:
        return "Improves meeting quality and avoids showing up underprepared."
    if "read" in lowered or "article" in lowered or "research" in lowered:
        return "Builds context, but should stay behind the higher-leverage work."

    return "Creates useful momentum on an important task."


def _infer_first_step(task_title: str) -> str:
    lowered = task_title.lower()

    if "alarm" in lowered or "wake" in lowered or "sleep" in lowered:
        return "Set the exact wake-up alarm now and place the phone or clock away from the bed."
    if "reply" in lowered or "email" in lowered:
        return "Open the message thread and draft the shortest useful response."
    if "spec" in lowered or "doc" in lowered:
        return "Open the document and rewrite the weakest section first."
    if "review" in lowered or "slide" in lowered:
        return "Open the latest materials and identify the one thing that must improve."
    if "read" in lowered or "article" in lowered:
        return "Skim the saved highlights before deciding whether a full read is worth it."
    if "prepare" in lowered or "prep" in lowered:
        return "Open the relevant notes or materials and list the first missing item to prepare."

    return "Open the relevant file or tool and define the first concrete action."


def _infer_hint(task_title: str, fixed_blocks: list[FixedBlock]) -> str:
    has_meeting = any(
        "meet" in block.title.lower() or "review" in block.title.lower()
        for block in fixed_blocks
    )
    lowered = task_title.lower()

    if "alarm" in lowered or "wake" in lowered or "sleep" in lowered:
        return "Lay out what you need tonight so the morning starts without extra decisions."
    if "spec" in lowered or "doc" in lowered or "write" in lowered:
        return "Write the rough structure first and clean up wording after the main points are down."
    if has_meeting and ("review" in lowered or "slide" in lowered):
        return "Bias toward preparation that will change the meeting outcome."
    if "reply" in lowered or "email" in lowered:
        return "Keep the tone concise and send it before context switching again."
    if "read" in lowered or "article" in lowered:
        return "Treat this as optional unless the earlier tasks finish cleanly."
    if "prepare" in lowered or "prep" in lowered:
        return "Finish the highest-risk prep item before polishing smaller details."

    return "Clear one obvious distraction before you start so the task gets a clean first pass."


def _infer_tool_names(task_title: str) -> list[str]:
    lowered = task_title.lower()

    if "reply" in lowered or "email" in lowered or "recruit" in lowered:
        return ["Gmail", "Google Calendar", "Notion"]
    if "spec" in lowered or "doc" in lowered or "write" in lowered:
        return ["Google Docs", "Notion"]
    if "review" in lowered or "slide" in lowered:
        return ["Google Slides", "Notion", "Google Sheets"]
    if "meeting" in lowered:
        return ["Google Calendar", "Notion", "Zoom"]
    if "read" in lowered or "article" in lowered or "research" in lowered:
        return ["Notion", "Google Docs"]

    return ["Notion"]


def _is_overly_generic_instruction(text: str) -> bool:
    lowered = text.casefold()
    word_count = len(re.findall(r"[a-zA-Z0-9']+", lowered))

    generic_starts = (
        "start ",
        "begin ",
        "work on ",
        "focus on ",
        "make progress ",
        "prepare for ",
        "get ready ",
        "be sure to ",
        "remember to ",
        "try to ",
        "keep ",
        "use ",
    )
    generic_nouns = (
        "task",
        "project",
        "work",
        "goal",
        "routine",
        "momentum",
        "time",
        "progress",
        "details",
    )

    if word_count <= 4:
        return True
    if any(lowered.startswith(prefix) for prefix in generic_starts) and not any(
        noun in lowered for noun in ("document", "thread", "slide", "deck", "alarm", "phone", "message", "calendar", "notes")
    ):
        return True
    if sum(noun in lowered for noun in generic_nouns) >= 2:
        return True

    return False
