from __future__ import annotations

import logging
from datetime import date
from os import getenv
from pathlib import Path
from typing import Literal

from openai import OpenAI

from app.schemas.workspace import FixedBlock, TaskCard, Workspace
from app.services.workspace_task_builder import (
    build_generation_prompt,
    build_repair_prompt,
    generate_rule_based_task_cards,
    normalize_tasks,
    parse_llm_task_cards,
)

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "generate_workspace.txt"
WorkspaceSource = Literal["rules", "llm"]

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
    normalized_tasks = normalize_tasks(raw_tasks, raw_task_text)
    resolved_date = (target_date or date.today()).isoformat()

    if not normalized_tasks:
        normalized_tasks = ["Protect one focused work block around today's calendar constraints."]

    # Try to generate task cards using LLM
    try:
        task_cards = _generate_task_cards_with_llm(
            normalized_tasks, raw_task_text, fixed_blocks, resolved_date
        )
        source: WorkspaceSource = "llm"
    except Exception as exc:
        logger.warning("LLM generation failed, falling back to rules: %s", exc)
        task_cards = generate_rule_based_task_cards(normalized_tasks, fixed_blocks)
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
    raw_task_text: str | None,
    fixed_blocks: list[FixedBlock],
    resolved_date: str,
) -> list[TaskCard]:
    """Generate task cards by calling the vLLM endpoint."""
    model_name = LLM_MODEL

    logger.info("LLM model: %s", model_name)
    logger.info("LLM endpoint: %s", LLM_ENDPOINT_URL)

    if not model_name:
        raise ValueError("LLM_MODEL environment variable is not set")

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    generation_prompt = build_generation_prompt(
        resolved_date=resolved_date,
        normalized_tasks=normalized_tasks,
        raw_task_text=raw_task_text,
        fixed_blocks=fixed_blocks,
    )

    client = OpenAI(
        api_key="not-needed-for-local-llm",
        base_url=LLM_ENDPOINT_URL,
    )

    response_text = _request_chat_completion(
        client=client,
        model_name=model_name,
        prompt_template=prompt_template,
        user_prompt=generation_prompt,
        temperature=0.3,
    )

    try:
        return parse_llm_task_cards(response_text, normalized_tasks, fixed_blocks)
    except ValueError as exc:
        logger.warning("Initial LLM response was invalid; attempting repair: %s", exc)
        repair_prompt = build_repair_prompt(
            resolved_date=resolved_date,
            normalized_tasks=normalized_tasks,
            raw_task_text=raw_task_text,
            fixed_blocks=fixed_blocks,
            invalid_response=response_text,
        )
        repaired_text = _request_chat_completion(
            client=client,
            model_name=model_name,
            prompt_template=prompt_template,
            user_prompt=repair_prompt,
            temperature=0.0,
        )
        return parse_llm_task_cards(repaired_text, normalized_tasks, fixed_blocks)


def _request_chat_completion(
    client: OpenAI,
    model_name: str,
    prompt_template: str,
    user_prompt: str,
    temperature: float,
) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        timeout=LLM_TIMEOUT,
    )

    response_text = response.choices[0].message.content
    if response_text is None:
        raise ValueError("LLM response content is empty")

    stripped_response = response_text.strip()
    logger.debug("LLM raw response text: %s", stripped_response)
    return stripped_response
