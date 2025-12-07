import json
import os
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..services import ai as ai_service
from ..tts import play_text
from .schedule import get_today_schedule, get_recent_interactions


router = APIRouter(prefix="/ai", tags=["ai"])


def _parse_bool_env(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    s = value.strip().lower()
    if not s:
        return default
    if s in {"0", "false", "no", "off"}:
        return False
    if s in {"1", "true", "yes", "on"}:
        return True
    return default


TTS_ENABLED = _parse_bool_env(os.getenv("TTS_ENABLED"), True)


class TemplateSuggestion(BaseModel):
    name: str
    category: str
    default_duration_minutes: int
    recurrence_pattern: Optional[str] = None
    preferred_time_window: Optional[str] = None
    default_alert_style: str = "visual_then_alarm"
    enabled: bool = True


class TemplateSuggestionsRequest(BaseModel):
    free_text: str


class TemplateSuggestionsResponse(BaseModel):
    templates: List[TemplateSuggestion]


class TemplateRefineRequest(BaseModel):
    template: TemplateSuggestion
    instruction: Optional[str] = None


class TemplateRefineResponse(BaseModel):
    template: TemplateSuggestion


class NowSuggestionResponse(BaseModel):
    suggestion: str


class HistoryInsightsRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HistoryInsightsResponse(BaseModel):
    insights: List[str]
    recommendations: List[str]


class AlertWordingRequest(BaseModel):
    category: str
    tone: str
    max_length: Optional[int] = 120
    count: Optional[int] = 5


class AlertWordingResponse(BaseModel):
    options: List[str]


class NotesSummaryRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class NotesSummaryResponse(BaseModel):
    patterns: List[str]
    recommendations: List[str]


class TTSPlayRequest(BaseModel):
    text: str


@router.post("/templates/suggestions", response_model=TemplateSuggestionsResponse)
async def get_template_suggestions(payload: TemplateSuggestionsRequest) -> TemplateSuggestionsResponse:
    """Use DeepSeek to turn a free-text routine description into template suggestions."""

    if not payload.free_text.strip():
        raise HTTPException(status_code=400, detail="free_text must not be empty")

    templates_data = await ai_service.generate_template_suggestions(payload.free_text)

    templates: List[TemplateSuggestion] = []
    for item in templates_data:
        try:
            templates.append(TemplateSuggestion(**item))
        except Exception:
            # Skip items that don't match the schema
            continue

    if not templates:
        raise HTTPException(status_code=502, detail="AI did not return any valid template suggestions")

    return TemplateSuggestionsResponse(templates=templates)


@router.post("/templates/refine", response_model=TemplateRefineResponse)
async def refine_template(payload: TemplateRefineRequest) -> TemplateRefineResponse:
    """Use DeepSeek to refine a single existing template (PA-031)."""

    if payload.template is None:
        raise HTTPException(status_code=400, detail="template is required")

    try:
        refined_data = await ai_service.refine_template(
            payload.template.model_dump(),
            payload.instruction,
        )
        refined = TemplateSuggestion(**refined_data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="AI returned invalid template data") from exc

    return TemplateRefineResponse(template=refined)


@router.get("/now/suggestion", response_model=NowSuggestionResponse)
async def get_now_suggestion(db: Session = Depends(get_db)) -> NowSuggestionResponse:
    """Provide a short AI hint about what to focus on right now (PA-032)."""

    schedule_items = get_today_schedule(db=db)
    interactions = get_recent_interactions(limit=30, db=db)

    now = datetime.now()
    current_time = now.time()

    active_item = None
    paused_item = None
    upcoming_items: List = []

    for item in schedule_items:
        status = getattr(item, "status", None)
        if status == "paused" and paused_item is None:
            paused_item = item
        elif status == "active" and active_item is None:
            active_item = item

        start_time = getattr(item, "planned_start_time", None)
        if start_time is not None and start_time >= current_time:
            upcoming_items.append(item)

    banner_item = paused_item or active_item

    def serialize_schedule_item(it) -> dict:
        if it is None:
            return {}
        start_time = getattr(it, "planned_start_time", None)
        end_time = getattr(it, "planned_end_time", None)
        return {
            "task_name": getattr(it, "task_name", None),
            "category": getattr(it, "category", None),
            "planned_start_time": start_time.isoformat() if start_time is not None else None,
            "planned_end_time": end_time.isoformat() if end_time is not None else None,
            "status": getattr(it, "status", None),
            "is_adhoc": getattr(it, "is_adhoc", False),
        }

    recent_interactions_payload = []
    for it in interactions[:10]:
        recent_interactions_payload.append(
            {
                "task_name": getattr(it, "task_name", None),
                "category": getattr(it, "category", None),
                "alert_type": getattr(it, "alert_type", None),
                "response_type": getattr(it, "response_type", None),
                "response_stage": getattr(it, "response_stage", None),
                "alert_started_at": getattr(it, "alert_started_at", None),
                "responded_at": getattr(it, "responded_at", None),
            }
        )

    context = {
        "now": now.isoformat(),
        "active_or_paused_task": serialize_schedule_item(banner_item) if banner_item else None,
        "upcoming_tasks": [serialize_schedule_item(it) for it in upcoming_items[:3]],
        "recent_interactions": recent_interactions_payload,
    }

    suggestion = await ai_service.generate_now_suggestion(context)
    return NowSuggestionResponse(suggestion=suggestion)


@router.post("/alerts/wording", response_model=AlertWordingResponse)
async def get_alert_wording(payload: AlertWordingRequest) -> AlertWordingResponse:
    """Generate short alert text options for a given category and tone (PA-034)."""

    category = (payload.category or "").strip()
    tone = (payload.tone or "").strip()
    if not category or not tone:
        raise HTTPException(status_code=400, detail="category and tone are required")

    max_length = payload.max_length or 120
    try:
        max_length = int(max_length)
    except (TypeError, ValueError):  # noqa: PERF203
        max_length = 120
    max_length = max(40, min(200, max_length))

    count = payload.count or 5
    try:
        count = int(count)
    except (TypeError, ValueError):  # noqa: PERF203
        count = 5
    count = max(3, min(8, count))

    options = await ai_service.generate_alert_wording(
        category=category,
        tone=tone,
        max_length=max_length,
        count=count,
    )

    return AlertWordingResponse(options=options)


@router.post("/history/insights", response_model=HistoryInsightsResponse)
async def get_history_insights(
    payload: HistoryInsightsRequest,
    db: Session = Depends(get_db),
) -> HistoryInsightsResponse:
    """Return AI-generated insights on recent interaction history (PA-033).

    The backend aggregates interactions over a chosen date range and sends only
    summarized counts (by category, response type, and time of day) to the AI.
    """

    today = date.today()
    end_date = payload.end_date or today
    start_date = payload.start_date or (end_date - timedelta(days=7))

    # Normalize and clamp range
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    max_span_days = 60
    delta_days = (end_date - start_date).days
    if delta_days > max_span_days:
        start_date = end_date - timedelta(days=max_span_days)

    rows = (
        db.query(models.Interaction, models.ScheduleInstance, models.Task)
        .join(
            models.ScheduleInstance,
            models.Interaction.schedule_instance_id == models.ScheduleInstance.id,
        )
        .join(models.Task, models.ScheduleInstance.task_id == models.Task.id)
        .filter(models.ScheduleInstance.date >= start_date)
        .filter(models.ScheduleInstance.date <= end_date)
        .order_by(
            models.Interaction.alert_started_at.desc(),
            models.Interaction.id.desc(),
        )
        .limit(1000)
        .all()
    )

    if not rows:
        return HistoryInsightsResponse(
            insights=[
                "No interaction history found in the selected date range, so there are no patterns to summarize.",
            ],
            recommendations=[],
        )

    totals_by_category: dict = {}
    by_category_and_response: dict = {}
    by_time_of_day_and_response: dict = {}
    total_interactions = 0

    def bucket_for_hour(hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        if 17 <= hour < 22:
            return "evening"
        return "late_night"

    for interaction, instance, task in rows:
        total_interactions += 1
        category = (task.category or "uncategorized").strip() or "uncategorized"
        response = (interaction.response_type or "none").strip() or "none"

        totals_by_category[category] = totals_by_category.get(category, 0) + 1

        cat_bucket = by_category_and_response.setdefault(category, {})
        cat_bucket[response] = cat_bucket.get(response, 0) + 1

        ts = interaction.alert_started_at
        if ts is not None:
            hour = ts.hour
            bucket = bucket_for_hour(hour)
            time_bucket = by_time_of_day_and_response.setdefault(bucket, {})
            time_bucket[response] = time_bucket.get(response, 0) + 1

    summary = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_interactions": total_interactions,
        "totals_by_category": totals_by_category,
        "by_category_and_response": by_category_and_response,
        "by_time_of_day_and_response": by_time_of_day_and_response,
    }

    result = await ai_service.summarize_history(summary)
    insights = result.get("insights") or []
    recommendations = result.get("recommendations") or []

    return HistoryInsightsResponse(insights=insights, recommendations=recommendations)


@router.post("/notes/summary", response_model=NotesSummaryResponse)
async def get_notes_summary(
    payload: NotesSummaryRequest,
    db: Session = Depends(get_db),
) -> NotesSummaryResponse:
    """Return AI-generated summary of skip/snooze notes (PA-035).

    Aggregates short micro-journal notes linked to schedule instances and interactions,
    and asks the AI to infer recurring reasons and suggest schedule/alert adjustments.
    """

    today = date.today()
    end_date = payload.end_date or today
    start_date = payload.start_date or (end_date - timedelta(days=7))

    # Normalize and clamp range
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    max_span_days = 60
    delta_days = (end_date - start_date).days
    if delta_days > max_span_days:
        start_date = end_date - timedelta(days=max_span_days)

    rows = (
        db.query(models.InteractionNote, models.ScheduleInstance, models.Task)
        .join(
            models.ScheduleInstance,
            models.InteractionNote.schedule_instance_id == models.ScheduleInstance.id,
        )
        .join(models.Task, models.ScheduleInstance.task_id == models.Task.id)
        .filter(models.ScheduleInstance.date >= start_date)
        .filter(models.ScheduleInstance.date <= end_date)
        .filter(models.InteractionNote.note_type.in_(["snooze", "skip"]))
        .order_by(models.InteractionNote.created_at.desc())
        .limit(500)
        .all()
    )

    if not rows:
        return NotesSummaryResponse(
            patterns=[
                "No skip or snooze notes were found in the selected date range.",
            ],
            recommendations=[],
        )

    notes: List[dict] = []
    for note, instance, task in rows:
        notes.append(
            {
                "task_name": task.name,
                "category": (task.category or "uncategorized").strip() or "uncategorized",
                "date": instance.date.isoformat(),
                "planned_start_time": instance.planned_start_time.isoformat()
                if instance.planned_start_time is not None
                else None,
                "note_type": (note.note_type or "").strip() or "other",
                "text": note.text,
            }
        )

    summary = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "count": len(notes),
        "notes": notes,
    }

    result = await ai_service.summarize_notes(summary)
    patterns = result.get("patterns") or []
    recommendations = result.get("recommendations") or []

    return NotesSummaryResponse(patterns=patterns, recommendations=recommendations)


@router.post("/tts/play", status_code=204)
async def play_tts(payload: TTSPlayRequest) -> None:
    """Play short coaching text as audio via local TTS on the Pi (PA-040)."""

    if not TTS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech is disabled by configuration.",
        )

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        play_text(text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"TTS playback failed: {exc}") from exc

    return None
