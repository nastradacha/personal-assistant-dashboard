from datetime import datetime, timedelta, time
from typing import Optional, Tuple

from .. import models


def compute_effective_status_and_remaining(
    instance: models.ScheduleInstance,
    now: datetime,
) -> Tuple[str, Optional[int]]:
    effective_status = instance.status
    if effective_status not in ("cancelled", "paused"):
        current_time = now.time()
        if instance.planned_start_time <= current_time < instance.planned_end_time:
            effective_status = "active"
        else:
            effective_status = "pending"

    remaining_seconds: Optional[int] = None
    if effective_status in ("active", "paused"):
        end_dt = datetime.combine(instance.date, instance.planned_end_time)
        delta = (end_dt - now).total_seconds()
        remaining_seconds = max(0, int(delta))

    return effective_status, remaining_seconds


def update_instance_time_and_status(
    instance: models.ScheduleInstance,
    task: models.Task,
    planned_start_time: Optional[time],
    new_status: Optional[str],
) -> None:
    if planned_start_time is not None:
        start_dt = datetime.combine(instance.date, planned_start_time)
        end_dt = start_dt + timedelta(minutes=task.default_duration_minutes)
        instance.planned_start_time = start_dt.time()
        instance.planned_end_time = end_dt.time()

    if new_status is not None:
        instance.status = new_status


def snooze_instance(
    instance: models.ScheduleInstance,
    minutes: int,
) -> None:
    end_dt = datetime.combine(instance.date, instance.planned_end_time)
    end_dt = end_dt + timedelta(minutes=minutes)
    instance.planned_end_time = end_dt.time()
