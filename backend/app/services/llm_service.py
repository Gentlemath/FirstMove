from __future__ import annotations

import json
import logging
from datetime import date
from os import getenv
from pathlib import Path

from openai import OpenAI

from app.schemas.workspace import FixedBlock, TaskCard, Workspace

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "generate_workspace.txt"

# LLM Configuration
LLM_ENDPOINT_URL = getenv("LLM_ENDPOINT_URL", "http://localhost:8001/v1")
LLM_MODEL = getenv("LLM_MODEL")
LLM_TIMEOUT = int(getenv("LLM_TIMEOUT", "60"))


def generate_workspace(
    target_date: date | None,
    raw_tasks: list[str],
    raw_task_text: str | None,
    fixed_blocks: list[FixedBlock],
) -> Workspace:
    normalized_tasks = _normalize_tasks(raw_tasks, raw_task_text)
    resolved_date = (target_date or date.today()).isoformat()

    if not normalized_tasks:
        normalized_tasks = ["Protect one focused work block around today's calendar constraints."]

    # Try to generate task cards using LLM
    try:
        task_cards = _generate_task_cards_with_llm(
            normalized_tasks, fixed_blocks, resolved_date
        )
        source = "llm"
    except Exception as e:
        logger.warning(f"LLM generation failed, falling back to rules: {e}")
        task_cards = _generate_task_cards_with_rules(normalized_tasks, fixed_blocks)
        source = "rules"

    today_focus = task_cards[0].title if task_cards else "Focus your attention"

    return Workspace(
        date=resolved_date,
        source=source,
        today_focus=today_focus,
        fixed_blocks=fixed_blocks,
        task_cards=task_cards,
    )


def _generate_task_cards_with_llm(
    normalized_tasks: list[str],
    fixed_blocks: list[FixedBlock],
    resolved_date: str,
) -> list[TaskCard]:
    """Generate task cards by calling the vLLM endpoint."""
    logger.info(f"LLM_MODEL value: {LLM_MODEL}")
    logger.info(f"LLM_ENDPOINT_URL value: {LLM_ENDPOINT_URL}")
    
    if not LLM_MODEL:
        raise ValueError("LLM_MODEL environment variable is not set")
    
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    
    # Format the prompt with the user's context
    calendar_context = _format_calendar_context(fixed_blocks)
    tasks_text = "\n".join(f"- {task}" for task in normalized_tasks)
    
    user_prompt = f"""Generate task cards for the following tasks scheduled for {resolved_date}.

Calendar constraints:
{calendar_context}

Tasks to organize:
{tasks_text}

Return a JSON array with exactly {len(normalized_tasks)} objects, each with:
- title (string): The task title
- why_it_matters (string): Why this task is important
- first_step (string): The concrete first action to take
- hint (string): A brief helpful hint
- tools (array of strings): Tools needed for this task
- section (string): Priority section - "now", "ready", or "later"
"""

    client = OpenAI(
        api_key="not-needed-for-local-llm",
        base_url=LLM_ENDPOINT_URL,
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        timeout=LLM_TIMEOUT,
    )

    response_text = response.choices[0].message.content.strip()
    logger.debug("LLM raw response text: %s", response_text)
    
    # Extract JSON from response (handle markdown code blocks)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    try:
        task_data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM response as JSON: %s", exc)
        logger.error("Unparsed LLM output: %s", response_text)
        raise

    if isinstance(task_data, dict):
        logger.warning("LLM response is a single object; wrapping into a list.")
        task_data = [task_data]
    elif not isinstance(task_data, list):
        logger.error("LLM response is not a list or dict: %s", task_data)
        raise ValueError(f"LLM response is not a list or dict: {task_data}")

    task_cards = []
    for index, item in enumerate(task_data, start=1):
        # Ensure section is valid
        section = item.get("section", _default_section(index))
        if section not in ["now", "ready", "later"]:
            section = _default_section(index)
            
        task_cards.append(
            TaskCard(
                task_id=f"task-{index}",
                title=item.get("title", normalized_tasks[index - 1] if index <= len(normalized_tasks) else ""),
                why_it_matters=item.get("why_it_matters", ""),
                first_step=item.get("first_step", ""),
                hint=item.get("hint", ""),
                tools=item.get("tools", []),
                section=section,
                status=section,
            )
        )

    return task_cards


def _generate_task_cards_with_rules(
    normalized_tasks: list[str],
    fixed_blocks: list[FixedBlock],
) -> list[TaskCard]:
    """Fallback to rule-based task card generation."""
    return [
        TaskCard(
            task_id=f"task-{index}",
            title=task_title,
            why_it_matters=_infer_why_it_matters(task_title),
            first_step=_infer_first_step(task_title),
            hint=_infer_hint(task_title, fixed_blocks),
            tools=_infer_tools(task_title),
            section=_assign_section(index),
            status=_assign_section(index),
        )
        for index, task_title in enumerate(normalized_tasks, start=1)
    ]


def _format_calendar_context(fixed_blocks: list[FixedBlock]) -> str:
    """Format calendar blocks for the LLM context."""
    if not fixed_blocks:
        return "No fixed calendar events."
    
    context_lines = []
    for block in fixed_blocks:
        time_range = f"{block.start_time or block.time} - {block.end_time or ''}"
        location = f" at {block.location}" if block.location else ""
        context_lines.append(f"- {block.title}: {time_range}{location}")
    
    return "\n".join(context_lines)


def _default_section(index: int) -> str:
    """Determine default section by priority order."""
    if index == 1:
        return "now"
    if index <= 3:
        return "ready"
    return "later"


def _normalize_tasks(raw_tasks: list[str], raw_task_text: str | None) -> list[str]:
    combined_tasks = list(raw_tasks)

    cleaned_tasks: list[str] = []
    for task in combined_tasks:
        normalized = task.strip().lstrip("-").strip()
        if normalized:
            cleaned_tasks.append(normalized)

    return cleaned_tasks


def _assign_section(index: int) -> str:
    """Determine the section assignment by task index."""
    if index == 1:
        return "now"
    if index <= 3:
        return "ready"
    return "later"


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

    if "reply" in lowered or "email" in lowered:
        return "Open the message thread and draft the shortest useful response."
    if "spec" in lowered or "doc" in lowered:
        return "Open the document and rewrite the weakest section first."
    if "review" in lowered or "slide" in lowered:
        return "Open the latest materials and identify the one thing that must improve."
    if "read" in lowered or "article" in lowered:
        return "Skim the saved highlights before deciding whether a full read is worth it."

    return "Open the relevant file or tool and define the first concrete action."


def _infer_hint(task_title: str, fixed_blocks: list[FixedBlock]) -> str:
    has_meeting = any("meet" in block.title.lower() or "review" in block.title.lower() for block in fixed_blocks)
    lowered = task_title.lower()

    if has_meeting and ("review" in lowered or "slide" in lowered):
        return "Bias toward preparation that will change the meeting outcome."
    if "reply" in lowered or "email" in lowered:
        return "Keep the tone concise and send it before context switching again."
    if "read" in lowered or "article" in lowered:
        return "Treat this as optional unless the earlier tasks finish cleanly."

    return "Keep the next step small enough to start immediately."


def _infer_tools(task_title: str) -> list[str]:
    lowered = task_title.lower()

    if "reply" in lowered or "email" in lowered or "recruit" in lowered:
        return ["Gmail", "Calendar", "Notes"]
    if "spec" in lowered or "doc" in lowered or "write" in lowered:
        return ["Google Docs", "Reference Notes"]
    if "review" in lowered or "slide" in lowered or "meeting" in lowered:
        return ["Slides", "Meeting Notes", "Metrics Sheet"]
    if "read" in lowered or "article" in lowered or "research" in lowered:
        return ["Browser", "Notes"]

    return ["Notes"]
