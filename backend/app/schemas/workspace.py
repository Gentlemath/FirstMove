from __future__ import annotations

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field


class FixedBlock(BaseModel):
    block_id: str
    title: str
    start_time: Union[str, None] = None
    end_time: Union[str, None] = None
    time: str
    location: Union[str, None] = None
    description: Union[str, None] = None
    attendees: list[str] = Field(default_factory=list)
    online_link: Union[str, None] = None
    html_link: Union[str, None] = None
    organizer: Union[str, None] = None
    status: Union[str, None] = None
    note: Union[str, None] = None


class CalendarDayResponse(BaseModel):
    date: str
    connected: bool
    source: Literal["google", "demo"]
    fixed_blocks: list[FixedBlock] = Field(default_factory=list)


class WorkspaceGenerateRequest(BaseModel):
    date: Union[date, None] = None
    raw_tasks: list[str] = Field(default_factory=list)
    raw_task_text: Union[str, None] = None


class TaskCard(BaseModel):
    task_id: str
    title: str
    why_it_matters: str
    first_step: str
    hint: str
    tools: list[str] = Field(default_factory=list)
    section: Literal["now", "ready", "later"]
    status: Literal["now", "ready", "later", "finished", "dismissed"] = "now"


class Workspace(BaseModel):
    date: str
    source: Literal["rules", "llm"]
    today_focus: str
    fixed_blocks: list[FixedBlock] = Field(default_factory=list)
    task_cards: list[TaskCard] = Field(default_factory=list)
