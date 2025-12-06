from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .. import models


def get_latest_interaction(db: Session, instance_id: int) -> Optional[models.Interaction]:
    return (
        db.query(models.Interaction)
        .filter(models.Interaction.schedule_instance_id == instance_id)
        .order_by(models.Interaction.alert_started_at.desc(), models.Interaction.id.desc())
        .first()
    )


def close_stale_interactions(db: Session, cutoff_minutes: int = 10) -> None:
    cutoff = datetime.utcnow() - timedelta(minutes=cutoff_minutes)
    stale = (
        db.query(models.Interaction)
        .filter(models.Interaction.response_type.is_(None))
        .filter(models.Interaction.alert_started_at <= cutoff)
        .all()
    )
    if not stale:
        return

    now_utc = datetime.utcnow()
    for interaction in stale:
        interaction.response_type = "none"
        interaction.response_stage = "none"
        interaction.responded_at = now_utc
    db.commit()


def start_interaction(
    db: Session,
    instance: models.ScheduleInstance,
    alert_type: str = "task_start",
) -> None:
    interaction = models.Interaction(
        schedule_instance_id=instance.id,
        alert_type=alert_type,
    )
    db.add(interaction)
    db.commit()


def record_acknowledge(
    db: Session,
    instance: models.ScheduleInstance,
    stage: Optional[str] = None,
) -> None:
    event = models.AcknowledgeEvent(schedule_instance_id=instance.id)
    db.add(event)
    db.commit()

    interaction = get_latest_interaction(db, instance.id)
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


def record_snooze(
    db: Session,
    instance: models.ScheduleInstance,
    minutes: int,
    stage: Optional[str] = None,
) -> None:
    event = models.SnoozeEvent(
        schedule_instance_id=instance.id,
        minutes=minutes,
    )
    db.add(event)
    db.commit()

    interaction = get_latest_interaction(db, instance.id)
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


def add_note_for_instance(
    db: Session,
    instance: models.ScheduleInstance,
    note_type: str,
    text: str,
) -> None:
    interaction = get_latest_interaction(db, instance.id)
    note = models.InteractionNote(
        schedule_instance_id=instance.id,
        interaction_id=interaction.id if interaction else None,
        note_type=note_type,
        text=text,
    )
    db.add(note)
    db.commit()
