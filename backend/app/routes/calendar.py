from __future__ import annotations

from datetime import date
from typing import Union

from fastapi import APIRouter, Query

from app.schemas.workspace import CalendarDayResponse
from app.services.calendar_service import get_calendar_day, get_calendar_upcoming

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/today", response_model=CalendarDayResponse)
def get_calendar_today(target_date: Union[date, None] = Query(default=None)) -> CalendarDayResponse:
    return get_calendar_day(target_date)


@router.get("/upcoming", response_model=CalendarDayResponse)
def get_calendar_upcoming_endpoint(days_ahead: int = Query(default=7, ge=1, le=30)) -> CalendarDayResponse:
    return get_calendar_upcoming(days_ahead)
