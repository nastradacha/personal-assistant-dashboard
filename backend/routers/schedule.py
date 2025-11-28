from datetime import date, datetime, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

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


def _get_or_create_alarm_config(db: Session) -> models.AlarmConfig:
    cfg = db.query(models.AlarmConfig).first()
    if cfg is None:
        cfg = models.AlarmConfig(sound="beep", volume_percent=12)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _get_latest_interaction(db: Session, instance_id: int) -> Optional[models.Interaction]:
    return (
        db.query(models.Interaction)
        .filter(models.Interaction.schedule_instance_id == instance_id)
        .order_by(models.Interaction.alert_started_at.desc(), models.Interaction.id.desc())
        .first()
    )


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

        for task in tasks:
            if not _task_applies_today(task, today):
                continue

            planned_start = cursor.time()
            planned_end = (cursor + timedelta(minutes=task.default_duration_minutes)).time()

            instance = models.ScheduleInstance(
                task_id=task.id,
                date=today,
                planned_start_time=planned_start,
                planned_end_time=planned_end,
                status="pending",
            )
            db.add(instance)
            cursor += timedelta(minutes=task.default_duration_minutes)

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

            created_any = False
            for task in tasks:
                if not _task_applies_today(task, today):
                    continue
                if task.id in existing_task_ids:
                    continue

                planned_start = cursor.time()
                planned_end = (cursor + timedelta(minutes=task.default_duration_minutes)).time()

                instance = models.ScheduleInstance(
                    task_id=task.id,
                    date=today,
                    planned_start_time=planned_start,
                    planned_end_time=planned_end,
                    status="pending",
                )
                db.add(instance)
                cursor += timedelta(minutes=task.default_duration_minutes)
                created_any = True

            if created_any:
                db.commit()

    cutoff = datetime.utcnow() - timedelta(minutes=10)
    stale = (
        db.query(models.Interaction)
        .filter(models.Interaction.response_type.is_(None))
        .filter(models.Interaction.alert_started_at <= cutoff)
        .all()
    )
    if stale:
        now_utc = datetime.utcnow()
        for interaction in stale:
            interaction.response_type = "none"
            interaction.response_stage = "none"
            interaction.responded_at = now_utc
        db.commit()

    rows = (
        db.query(models.ScheduleInstance, models.Task)
        .join(models.Task, models.ScheduleInstance.task_id == models.Task.id)
        .filter(models.ScheduleInstance.date == today)
        .order_by(models.ScheduleInstance.planned_start_time)
        .all()
    )

    now = datetime.now()
    current_time = now.time()
    result: List[schemas.TodayScheduleItem] = []
    for instance, task in rows:
        # Derive effective status from current time for non-cancelled/non-paused tasks.
        effective_status = instance.status
        if effective_status not in ("cancelled", "paused"):
            if instance.planned_start_time <= current_time < instance.planned_end_time:
                effective_status = "active"
            else:
                effective_status = "pending"

        # Treat tasks created via /adhoc-today (enabled = False) as ad-hoc for display.
        is_adhoc = not bool(task.enabled)

        remaining_seconds = None
        if effective_status in ("active", "paused"):
            end_dt = datetime.combine(instance.date, instance.planned_end_time)
            delta = (end_dt - now).total_seconds()
            remaining_seconds = max(0, int(delta))

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

    if update_in.planned_start_time is not None:
        start_dt = datetime.combine(instance.date, update_in.planned_start_time)
        end_dt = start_dt + timedelta(minutes=task.default_duration_minutes)
        instance.planned_start_time = start_dt.time()
        instance.planned_end_time = end_dt.time()

    if update_in.status is not None:
        instance.status = update_in.status

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

    interaction = models.Interaction(
        schedule_instance_id=instance.id,
        alert_type=alert_type,
    )
    db.add(interaction)
    db.commit()


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

    event = models.AcknowledgeEvent(schedule_instance_id=instance.id)
    db.add(event)
    db.commit()

    interaction = _get_latest_interaction(db, instance.id)
    stage_value = stage or "visual"
    now_utc = datetime.utcnow()
    if interaction and interaction.response_type is None:
        interaction.response_type = "acknowledge"
        interaction.response_stage = stage_value
        interaction.responded_at = now_utc
        db.commit()
    elif interaction is None:
        interaction = models.Interaction(
            schedule_instance_id=instance.id,
            alert_type="task_start",
            alert_started_at=now_utc,
            response_type="acknowledge",
            response_stage=stage_value,
            responded_at=now_utc,
        )
        db.add(interaction)
        db.commit()

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

    end_dt = datetime.combine(instance.date, instance.planned_end_time)
    end_dt = end_dt + timedelta(minutes=snooze_in.minutes)
    instance.planned_end_time = end_dt.time()

    # Log snooze event
    event = models.SnoozeEvent(
        schedule_instance_id=instance.id,
        minutes=snooze_in.minutes,
    )
    db.add(event)

    db.commit()
    db.refresh(instance)

    interaction = _get_latest_interaction(db, instance.id)
    stage_value = stage or "visual"
    now_utc = datetime.utcnow()
    if interaction and interaction.response_type is None:
        interaction.response_type = "snooze"
        interaction.response_stage = stage_value
        interaction.responded_at = now_utc
        db.commit()
    elif interaction is None:
        interaction = models.Interaction(
            schedule_instance_id=instance.id,
            alert_type="task_start",
            alert_started_at=now_utc,
            response_type="snooze",
            response_stage=stage_value,
            responded_at=now_utc,
        )
        db.add(interaction)
        db.commit()

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
