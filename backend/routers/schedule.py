from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import interactions as interactions_service
from ..services import schedule as schedule_service

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _task_applies_today(task: models.Task, today: date) -> bool:
    pattern = (task.recurrence_pattern or "").strip().lower()
    if not pattern or pattern == "daily":
        return True

    weekday = today.weekday()  # 0 = Monday
    if pattern == "weekdays":
        return weekday < 5
    if pattern == "weekends":
        return weekday >= 5

    parts = [p.strip() for p in pattern.split(",") if p.strip()]
    if parts:
        abbrev_to_idx = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }
        allowed = set()
        for p in parts:
            key = p[:3]
            if key in abbrev_to_idx:
                allowed.add(abbrev_to_idx[key])
        if allowed:
            return weekday in allowed

    # Fallback: treat unrecognized patterns as "daily" for now
    return True


def _parse_preferred_window(raw: Optional[str]) -> Optional[Tuple[time, time]]:
    """Parse a preferred_time_window string into (start, end).

    Supports common variants such as:
    - "07:00-11:00"
    - "07:00 - 11:00"
    - "1:17 pm - 1:20 pm"
    - "07:00-11:00 or evenings" (trailing text is ignored)
    """

    if not raw:
        return None
    s = (raw or "").strip()
    if not s:
        return None

    # Normalize dashes and split on the first '-'
    s = s.replace("\u2013", "-")
    dash_index = s.find("-")
    if dash_index == -1:
        return None

    left = s[:dash_index].strip()
    right = s[dash_index + 1 :].strip()
    if not left or not right:
        return None

    def _parse_part(part: str) -> Optional[time]:
        p = (part or "").strip().lower()
        if not p:
            return None

        # Keep only the first couple of tokens to drop trailing notes like "or evenings".
        tokens = p.split()
        if not tokens:
            return None
        candidate = " ".join(tokens[:2])

        # Try 12-hour clocks with am/pm markers first.
        if "am" in candidate or "pm" in candidate:
            for fmt in ("%I:%M %p", "%I %p", "%I:%M%p", "%I%p"):
                try:
                    return datetime.strptime(candidate, fmt).time()
                except ValueError:
                    continue

        # Fallback to 24-hour style like '7:00' or '07:00' or just '7'.
        base = tokens[0]
        for fmt in ("%H:%M", "%H"):
            try:
                return datetime.strptime(base, fmt).time()
            except ValueError:
                continue

        return None

    start_t = _parse_part(left)
    end_t = _parse_part(right)
    if start_t is None or end_t is None:
        return None
    if start_t >= end_t:
        return None
    return start_t, end_t


def _find_slot_in_window(
    today: date,
    duration_minutes: int,
    window: Tuple[time, time],
    instances: List[models.ScheduleInstance],
) -> Optional[time]:
    """Find earliest free slot of given duration fully inside the window.

    The slot must not overlap any existing instances in ``instances`` for ``today``.
    Returns a planned_start_time or None if no slot fits.
    """

    if duration_minutes <= 0:
        return None

    window_start_t, window_end_t = window
    window_start_dt = datetime.combine(today, window_start_t)
    window_end_dt = datetime.combine(today, window_end_t)
    if window_start_dt >= window_end_dt:
        return None

    duration = timedelta(minutes=duration_minutes)

    intervals: List[Tuple[datetime, datetime]] = []
    for inst in instances:
        if inst.date != today:
            continue
        start_dt = datetime.combine(today, inst.planned_start_time)
        end_dt = datetime.combine(today, inst.planned_end_time)
        intervals.append((start_dt, end_dt))

    intervals.sort(key=lambda pair: pair[0])

    candidate = window_start_dt
    for start_dt, end_dt in intervals:
        if end_dt <= window_start_dt:
            # This interval ends before the window starts; ignore.
            continue
        if start_dt >= window_end_dt:
            # This and all subsequent intervals start after the window.
            break

        # Is there a gap before this interval?
        if candidate + duration <= start_dt and candidate + duration <= window_end_dt:
            return candidate.time()

        # Move candidate past this interval if it overlaps.
        if candidate < end_dt:
            candidate = end_dt
        if candidate >= window_end_dt:
            break

    # After all intervals, there may still be room at the end of the window.
    if candidate + duration <= window_end_dt:
        return candidate.time()
    return None


def _get_or_create_alarm_config(db: Session) -> models.AlarmConfig:
    cfg = db.query(models.AlarmConfig).first()
    if cfg is None:
        cfg = models.AlarmConfig(sound="beep", volume_percent=12)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _update_active_instance(db: Session, today: date) -> None:
    """Ensure exactly one non-cancelled instance for today is marked active, based on time.

    Rules (PA-005):
    - When current time >= planned_start_time for a pending task, it becomes active.
    - Only one task can be active at a time.
    - If system restarts, calling this again recomputes the correct active task.
    """

    now = datetime.now()
    current_time = now.time()

    instances = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.date == today)
        .filter(models.ScheduleInstance.status != "cancelled")
        .order_by(models.ScheduleInstance.planned_start_time)
        .all()
    )

    if not instances:
        return

    # If any instance is paused, do not auto-change statuses; user must resume manually.
    if any(instance.status == "paused" for instance in instances):
        return

    # Choose an active instance only if "now" is within its planned window.
    active_candidate = None
    for instance in instances:
        if instance.planned_start_time <= current_time < instance.planned_end_time:
            active_candidate = instance
            break
        if instance.planned_start_time > current_time:
            break

    # Reset to pending first (non-cancelled/non-paused), except the active one.
    for instance in instances:
        if instance.status == "paused":
            continue
        if active_candidate is not None and instance.id == active_candidate.id:
            instance.status = "active"
            if instance.actual_start_time is None:
                instance.actual_start_time = now
        else:
            instance.status = "pending"

    db.commit()


@router.get("/today", response_model=List[schemas.TodayScheduleItem])
def get_today_schedule(db: Session = Depends(get_db)):
    today = date.today()

    existing = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.date == today)
        .order_by(models.ScheduleInstance.planned_start_time)
        .all()
    )

    if not existing:
        tasks = (
            db.query(models.Task)
            .filter(models.Task.enabled.is_(True))
            .order_by(models.Task.name)
            .all()
        )
        if not tasks:
            return []

        start_time = time(hour=9, minute=0)
        cursor = datetime.combine(today, start_time)
        instances_for_today: List[models.ScheduleInstance] = []

        for task in tasks:
            if not _task_applies_today(task, today):
                continue

            window = _parse_preferred_window(task.preferred_time_window)
            planned_start: Optional[time] = None

            if window is not None:
                slot = _find_slot_in_window(
                    today=today,
                    duration_minutes=task.default_duration_minutes,
                    window=window,
                    instances=instances_for_today,
                )
                if slot is not None:
                    planned_start = slot

            if planned_start is None:
                # If there was a preferred window but no room, skip scheduling this
                # template for today instead of placing it outside the window.
                if window is not None:
                    continue

                planned_start = cursor.time()
                cursor = cursor + timedelta(minutes=task.default_duration_minutes)

            start_dt = datetime.combine(today, planned_start)
            end_dt = start_dt + timedelta(minutes=task.default_duration_minutes)

            instance = models.ScheduleInstance(
                task_id=task.id,
                date=today,
                planned_start_time=planned_start,
                planned_end_time=end_dt.time(),
                status="pending",
            )
            db.add(instance)
            instances_for_today.append(instance)

        db.commit()
    else:
        # Top up today's schedule with any newly added enabled tasks that don't yet have
        # an instance for today. This makes it easier to test new templates without
        # needing a full regenerate.
        existing_task_ids = {instance.task_id for instance in existing}
        tasks = (
            db.query(models.Task)
            .filter(models.Task.enabled.is_(True))
            .order_by(models.Task.name)
            .all()
        )
        if tasks:
            # Start new tasks after the last planned end time (if any), otherwise 09:00.
            if existing:
                last_end_time = max(inst.planned_end_time for inst in existing)
                cursor = datetime.combine(today, last_end_time)
            else:
                cursor = datetime.combine(today, time(hour=9, minute=0))

            instances_for_today: List[models.ScheduleInstance] = list(existing)
            created_any = False
            for task in tasks:
                if not _task_applies_today(task, today):
                    continue
                if task.id in existing_task_ids:
                    continue

                window = _parse_preferred_window(task.preferred_time_window)
                planned_start: Optional[time] = None

                if window is not None:
                    slot = _find_slot_in_window(
                        today=today,
                        duration_minutes=task.default_duration_minutes,
                        window=window,
                        instances=instances_for_today,
                    )
                    if slot is not None:
                        planned_start = slot

                if planned_start is None:
                    # If there was a preferred window but no room, skip scheduling this
                    # template for today instead of placing it outside the window.
                    if window is not None:
                        continue

                    planned_start = cursor.time()
                    cursor = cursor + timedelta(minutes=task.default_duration_minutes)

                start_dt = datetime.combine(today, planned_start)
                end_dt = start_dt + timedelta(minutes=task.default_duration_minutes)

                instance = models.ScheduleInstance(
                    task_id=task.id,
                    date=today,
                    planned_start_time=planned_start,
                    planned_end_time=end_dt.time(),
                    status="pending",
                )
                db.add(instance)
                instances_for_today.append(instance)
                created_any = True

            if created_any:
                db.commit()

    interactions_service.close_stale_interactions(db)

    rows = (
        db.query(models.ScheduleInstance, models.Task)
        .join(models.Task, models.ScheduleInstance.task_id == models.Task.id)
        .filter(models.ScheduleInstance.date == today)
        .filter(models.ScheduleInstance.status != "cancelled")
        .order_by(models.ScheduleInstance.planned_start_time)
        .all()
    )

    now = datetime.now()
    result: List[schemas.TodayScheduleItem] = []
    for instance, task in rows:
        # Derive effective status from current time for non-cancelled/non-paused tasks.
        effective_status, remaining_seconds = schedule_service.compute_effective_status_and_remaining(
            instance=instance,
            now=now,
        )

        # Treat tasks created via /adhoc-today (enabled = False) as ad-hoc for display.
        is_adhoc = not bool(task.enabled)

        result.append(
            schemas.TodayScheduleItem(
                id=instance.id,
                task_id=instance.task_id,
                task_name=task.name,
                category=task.category,
                date=instance.date,
                planned_start_time=instance.planned_start_time,
                planned_end_time=instance.planned_end_time,
                status=effective_status,
                remaining_seconds=remaining_seconds,
                server_now=now,
                is_adhoc=is_adhoc,
            )
        )
    return result


@router.post("/adhoc-today", response_model=schemas.TodayScheduleItem)
def create_adhoc_today_task(
    payload: schemas.AdhocTodayTaskCreate,
    db: Session = Depends(get_db),
):
    """Create a one-off task instance directly in today's schedule (PA-004 extension)."""

    today = date.today()

    if payload.duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be positive",
        )

    name = (payload.name or "").strip()
    category = (payload.category or "").strip() or "misc"
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )

    # Create a disabled template to back this one-off instance, so it doesn't
    # automatically appear on future days but can be reused later if desired.
    task = models.Task(
        name=name,
        category=category,
        default_duration_minutes=payload.duration_minutes,
        recurrence_pattern=None,
        preferred_time_window=None,
        default_alert_style="visual_then_alarm",
        enabled=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    start_dt = datetime.combine(today, payload.start_time)
    end_dt = start_dt + timedelta(minutes=payload.duration_minutes)

    instance = models.ScheduleInstance(
        task_id=task.id,
        date=today,
        planned_start_time=payload.start_time,
        planned_end_time=end_dt.time(),
        status="pending",
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    remaining_seconds = None
    if instance.status in ("active", "paused"):
        now = datetime.now()
        end_dt2 = datetime.combine(instance.date, instance.planned_end_time)
        delta2 = (end_dt2 - now).total_seconds()
        remaining_seconds = max(0, int(delta2))

    return schemas.TodayScheduleItem(
        id=instance.id,
        task_id=instance.task_id,
        task_name=task.name,
        category=task.category,
        date=instance.date,
        planned_start_time=instance.planned_start_time,
        planned_end_time=instance.planned_end_time,
        status=instance.status,
        remaining_seconds=remaining_seconds,
    )


@router.post(
    "/instances/{instance_id}/notes",
    status_code=status.HTTP_204_NO_CONTENT,
)
def create_interaction_note(
    instance_id: int,
    payload: schemas.InteractionNoteCreate,
    db: Session = Depends(get_db),
):
    """Create a short micro-journal note linked to a schedule instance and its latest interaction.

    Used for PA-035 to record optional skip/snooze reasons.
    """

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text is required",
        )

    # Keep notes short to avoid bloating storage or AI prompts.
    if len(text) > 300:
        text = text[:300]

    note_type = (payload.note_type or "").strip().lower() or "other"

    instance = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule instance not found",
        )

    interactions_service.add_note_for_instance(
        db=db,
        instance=instance,
        note_type=note_type,
        text=text,
    )

    # 204 NO CONTENT
    return None


@router.put("/instances/{instance_id}", response_model=schemas.TodayScheduleItem)
def update_schedule_instance(
    instance_id: int,
    update_in: schemas.ScheduleInstanceUpdate,
    db: Session = Depends(get_db),
):
    instance = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule instance not found",
        )

    task = db.query(models.Task).filter(models.Task.id == instance.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task for schedule instance not found",
        )

    schedule_service.update_instance_time_and_status(
        instance=instance,
        task=task,
        planned_start_time=update_in.planned_start_time,
        new_status=update_in.status,
    )

    db.commit()
    db.refresh(instance)

    remaining_seconds = None
    if instance.status in ("active", "paused"):
        now = datetime.now()
        end_dt = datetime.combine(instance.date, instance.planned_end_time)
        delta = (end_dt - now).total_seconds()
        remaining_seconds = max(0, int(delta))

    return schemas.TodayScheduleItem(
        id=instance.id,
        task_id=instance.task_id,
        task_name=task.name,
        category=task.category,
        date=instance.date,
        planned_start_time=instance.planned_start_time,
        planned_end_time=instance.planned_end_time,
        status=instance.status,
        remaining_seconds=remaining_seconds,
    )


@router.get("/interactions/recent", response_model=List[schemas.InteractionHistoryItem])
def get_recent_interactions(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return recent interaction history for alerts (PA-014)."""

    # Clamp limit to a reasonable range
    if limit <= 0:
        limit = 1
    if limit > 200:
        limit = 200

    rows = (
        db.query(models.Interaction, models.ScheduleInstance, models.Task)
        .join(
            models.ScheduleInstance,
            models.Interaction.schedule_instance_id == models.ScheduleInstance.id,
        )
        .join(models.Task, models.ScheduleInstance.task_id == models.Task.id)
        .order_by(
            models.Interaction.alert_started_at.desc(),
            models.Interaction.id.desc(),
        )
        .limit(limit)
        .all()
    )

    result: List[schemas.InteractionHistoryItem] = []
    for interaction, instance, task in rows:
        result.append(
            schemas.InteractionHistoryItem(
                id=interaction.id,
                schedule_instance_id=interaction.schedule_instance_id,
                task_name=task.name,
                category=task.category,
                alert_type=interaction.alert_type,
                alert_started_at=interaction.alert_started_at,
                response_type=interaction.response_type,
                response_stage=interaction.response_stage,
                responded_at=interaction.responded_at,
            )
        )

    return result


@router.get("/alarm-config", response_model=schemas.AlarmConfig)
def get_alarm_config(db: Session = Depends(get_db)):
    cfg = _get_or_create_alarm_config(db)
    return schemas.AlarmConfig(sound=cfg.sound, volume_percent=cfg.volume_percent)


@router.put("/alarm-config", response_model=schemas.AlarmConfig)
def update_alarm_config(
    update_in: schemas.AlarmConfigUpdate,
    db: Session = Depends(get_db),
):
    cfg = _get_or_create_alarm_config(db)

    if update_in.sound is not None:
        allowed = {"beep", "chime"}
        if update_in.sound not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alarm sound",
            )
        cfg.sound = update_in.sound

    if update_in.volume_percent is not None:
        try:
            vol = int(update_in.volume_percent)
        except (TypeError, ValueError):
            vol = 12
        vol = max(0, min(100, vol))
        cfg.volume_percent = vol

    db.commit()
    db.refresh(cfg)

    return schemas.AlarmConfig(sound=cfg.sound, volume_percent=cfg.volume_percent)


@router.get("/alert-wordings/{category}", response_model=schemas.AlertWordingConfig)
def get_alert_wording_config(category: str, db: Session = Depends(get_db)):
    cat_norm = (category or "").strip()
    if not cat_norm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is required",
        )

    cfg = db.query(models.AlertWording).filter(models.AlertWording.category == cat_norm).first()
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No alert wording configured for this category",
        )

    return schemas.AlertWordingConfig(category=cfg.category, tone=cfg.tone, text=cfg.text)


@router.put("/alert-wordings/{category}", response_model=schemas.AlertWordingConfig)
def upsert_alert_wording_config(
    category: str,
    payload: schemas.AlertWordingUpdate,
    db: Session = Depends(get_db),
):
    cat_norm = (category or "").strip()
    if not cat_norm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is required",
        )

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is required",
        )

    tone = (payload.tone or "unspecified").strip() or "unspecified"

    cfg = db.query(models.AlertWording).filter(models.AlertWording.category == cat_norm).first()
    if cfg is None:
        cfg = models.AlertWording(category=cat_norm, tone=tone, text=text)
        db.add(cfg)
    else:
        cfg.tone = tone
        cfg.text = text

    db.commit()
    db.refresh(cfg)

    return schemas.AlertWordingConfig(category=cfg.category, tone=cfg.tone, text=cfg.text)


@router.post(
    "/instances/{instance_id}/interactions/start",
    status_code=status.HTTP_204_NO_CONTENT,
)
def start_interaction(
    instance_id: int,
    alert_type: str = "task_start",
    db: Session = Depends(get_db),
):
    instance = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule instance not found",
        )

    interactions_service.start_interaction(db=db, instance=instance, alert_type=alert_type)


@router.post("/instances/{instance_id}/acknowledge", response_model=schemas.TodayScheduleItem)
def acknowledge_schedule_instance(
    instance_id: int,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Record that the current alert for this instance was acknowledged (PA-011)."""

    instance = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule instance not found",
        )

    task = db.query(models.Task).filter(models.Task.id == instance.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task for schedule instance not found",
        )

    interactions_service.record_acknowledge(db=db, instance=instance, stage=stage)

    remaining_seconds = None
    if instance.status in ("active", "paused"):
        now = datetime.now()
        end_dt = datetime.combine(instance.date, instance.planned_end_time)
        delta = (end_dt - now).total_seconds()
        remaining_seconds = max(0, int(delta))

    return schemas.TodayScheduleItem(
        id=instance.id,
        task_id=instance.task_id,
        task_name=task.name,
        category=task.category,
        date=instance.date,
        planned_start_time=instance.planned_start_time,
        planned_end_time=instance.planned_end_time,
        status=instance.status,
        remaining_seconds=remaining_seconds,
    )


@router.post("/instances/{instance_id}/snooze", response_model=schemas.TodayScheduleItem)
def snooze_schedule_instance(
    instance_id: int,
    snooze_in: schemas.SnoozeRequest,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Extend the planned end time of a schedule instance by the given number of minutes."""

    if snooze_in.minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snooze minutes must be positive",
        )

    instance = (
        db.query(models.ScheduleInstance)
        .filter(models.ScheduleInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule instance not found",
        )

    task = db.query(models.Task).filter(models.Task.id == instance.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task for schedule instance not found",
        )

    schedule_service.snooze_instance(
        instance=instance,
        minutes=snooze_in.minutes,
    )

    db.commit()
    db.refresh(instance)

    interactions_service.record_snooze(
        db=db,
        instance=instance,
        minutes=snooze_in.minutes,
        stage=stage,
    )

    remaining_seconds = None
    if instance.status in ("active", "paused"):
        now = datetime.now()
        end_dt = datetime.combine(instance.date, instance.planned_end_time)
        delta = (end_dt - now).total_seconds()
        remaining_seconds = max(0, int(delta))

    return schemas.TodayScheduleItem(
        id=instance.id,
        task_id=instance.task_id,
        task_name=task.name,
        category=task.category,
        date=instance.date,
        planned_start_time=instance.planned_start_time,
        planned_end_time=instance.planned_end_time,
        status=instance.status,
        remaining_seconds=remaining_seconds,
    )
