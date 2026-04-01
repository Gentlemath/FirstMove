from __future__ import annotations

from fastapi import APIRouter

from app.schemas.workspace import Workspace, WorkspaceGenerateRequest
from app.services.calendar_service import get_calendar_day
from app.services.llm_service import generate_workspace

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.post("/generate", response_model=Workspace)
def generate_workspace_route(payload: WorkspaceGenerateRequest) -> Workspace:
    calendar_day = get_calendar_day(payload.date)
    return generate_workspace(
        target_date=payload.date,
        raw_tasks=payload.raw_tasks,
        raw_task_text=payload.raw_task_text,
        fixed_blocks=calendar_day.fixed_blocks,
    )
