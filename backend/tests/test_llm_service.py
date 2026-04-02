from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

FixedBlock = importlib.import_module("app.schemas.workspace").FixedBlock
llm_service = importlib.import_module("app.services.llm_service")
workspace_task_builder = importlib.import_module("app.services.workspace_task_builder")
normalize_tasks = workspace_task_builder.normalize_tasks
parse_llm_task_cards = workspace_task_builder.parse_llm_task_cards


def _fixed_block(title: str, time: str = "10:00 AM-10:30 AM") -> FixedBlock:
    return FixedBlock(
        block_id="block-1",
        title=title,
        start_time=None,
        end_time=None,
        time=time,
    )


def test_normalize_tasks_merges_and_deduplicates_raw_text() -> None:
    tasks = normalize_tasks(
        raw_tasks=["  Finish spec  ", "Reply recruiter"],
        raw_task_text="- Finish spec\n- Draft launch note\nReply recruiter",
    )

    assert tasks == ["Finish spec", "Reply recruiter", "Draft launch note"]


def test_parse_llm_task_cards_sorts_by_task_index_and_repairs_weak_fields() -> None:
    response_text = """
    ```json
    [
      {
        "task_index": 2,
        "title": "Reply to recruiter",
        "why_it_matters": "Keeps the conversation moving with minimal delay.",
        "first_step": "Open the thread and write a short reply.",
        "hint": "Send it before switching into deeper work.",
        "tools": ["Gmail", "Notes"],
        "section": "ready"
      },
      {
        "task_index": 1,
        "title": "Tighten spec outline",
        "why_it_matters": "This is important",
        "first_step": "Start working on the task.",
        "hint": "",
        "tools": "Docs",
        "section": "now"
      }
    ]
    ```
    """

    cards = parse_llm_task_cards(
        response_text=response_text,
        normalized_tasks=["Finish spec", "Reply recruiter"],
        fixed_blocks=[_fixed_block("Design review")],
    )

    assert [card.title for card in cards] == ["Tighten spec outline", "Reply to recruiter"]
    assert cards[0].why_it_matters == (
        "Clarifies the work so execution gets easier for the rest of the day."
    )
    assert cards[0].first_step == "Open the document and rewrite the weakest section first."
    assert cards[0].hint == (
        "Write the rough structure first and clean up wording after the main points are down."
    )
    assert [tool.label for tool in cards[0].tools] == ["Google Docs", "Notion"]
    assert cards[0].tools[0].href == "https://docs.google.com/document"
    assert cards[0].section == "now"
    assert cards[1].section == "ready"


def test_parse_llm_task_cards_replaces_generic_alarm_step_and_hint() -> None:
    response_text = """
    [
      {
        "task_index": 1,
        "title": "Set alarm and prepare for early wake-up tomorrow",
        "why_it_matters": "Starting early builds momentum for the day and prevents last-minute rush.",
        "first_step": "Begin by getting ready for tomorrow morning.",
        "hint": "Use a consistent pre-sleep routine to signal your body it's time to wind down.",
        "tools": ["Google Calendar"],
        "section": "now"
      }
    ]
    """

    cards = parse_llm_task_cards(
        response_text=response_text,
        normalized_tasks=["Set alarm and prepare for early wake-up tomorrow"],
        fixed_blocks=[],
    )

    assert cards[0].first_step == (
        "Set the exact wake-up alarm now and place the phone or clock away from the bed."
    )
    assert cards[0].hint == (
        "Lay out what you need tonight so the morning starts without extra decisions."
    )


def test_parse_llm_task_cards_normalizes_tool_aliases() -> None:
    response_text = """
    [
      {
        "task_index": 1,
        "title": "Prep slides",
        "why_it_matters": "Makes the review more effective.",
        "first_step": "Open the deck and rewrite the agenda slide.",
        "hint": "Fix the decision slide first.",
        "tools": ["Slides", "Meeting Notes", "Metrics Sheet"],
        "section": "now"
      }
    ]
    """

    cards = parse_llm_task_cards(
        response_text=response_text,
        normalized_tasks=["Prep slides"],
        fixed_blocks=[_fixed_block("Weekly review")],
    )

    assert [tool.label for tool in cards[0].tools] == [
        "Google Slides",
        "Notion",
        "Google Sheets",
    ]


def test_generate_workspace_repairs_invalid_llm_response(monkeypatch) -> None:
    responses = iter(
        [
            "not json at all",
            """
            [
              {
                "task_index": 1,
                "title": "Reply recruiter",
                "why_it_matters": "Keeps the external process moving and reduces follow-up risk.",
                "first_step": "Open the message thread and draft the shortest useful response.",
                "hint": "Keep the tone concise and send it before context switching again.",
                "tools": ["Gmail", "Calendar", "Notes"],
                "section": "now"
              }
            ]
            """,
        ]
    )

    monkeypatch.setattr(llm_service, "LLM_MODEL", "test-model")
    monkeypatch.setattr(llm_service, "OpenAI", lambda **kwargs: object())

    def fake_request_chat_completion(**kwargs):
        return next(responses)

    monkeypatch.setattr(llm_service, "_request_chat_completion", fake_request_chat_completion)

    workspace = llm_service.generate_workspace(
        target_date=None,
        raw_tasks=["Reply recruiter"],
        raw_task_text="Reply recruiter",
        fixed_blocks=[],
    )

    assert workspace.source == "llm"
    assert len(workspace.task_cards) == 1
    assert workspace.task_cards[0].title == "Reply recruiter"
    assert [tool.label for tool in workspace.task_cards[0].tools] == [
        "Gmail",
        "Google Calendar",
        "Notion",
    ]


def test_generate_workspace_falls_back_to_rules_after_failed_repair(monkeypatch) -> None:
    monkeypatch.setattr(llm_service, "LLM_MODEL", "test-model")
    monkeypatch.setattr(llm_service, "OpenAI", lambda **kwargs: object())
    monkeypatch.setattr(
        llm_service,
        "_request_chat_completion",
        lambda **kwargs: "still not json",
    )

    workspace = llm_service.generate_workspace(
        target_date=None,
        raw_tasks=["Finish spec"],
        raw_task_text="Finish spec",
        fixed_blocks=[],
    )

    assert workspace.source == "rules"
    assert workspace.task_cards[0].first_step == (
        "Open the document and rewrite the weakest section first."
    )
    assert [tool.label for tool in workspace.task_cards[0].tools] == [
        "Google Docs",
        "Notion",
    ]
