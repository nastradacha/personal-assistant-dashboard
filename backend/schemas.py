from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    name: str
    category: str
    default_duration_minutes: int
    recurrence_pattern: Optional[str] = None
    preferred_time_window: Optional[str] = None
    default_alert_style: str = "visual_then_alarm"
    enabled: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleInstanceBase(BaseModel):
    task_id: int
    date: date
    planned_start_time: time
    planned_end_time: time
    status: str = "pending"


class ScheduleInstanceCreate(ScheduleInstanceBase):
    pass


class ScheduleInstanceRead(ScheduleInstanceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleInstanceUpdate(BaseModel):
    planned_start_time: Optional[time] = None
    status: Optional[str] = None


class TodayScheduleItem(BaseModel):
    id: int
    task_id: int
    task_name: str
    category: str
    date: date
    planned_start_time: time
    planned_end_time: time
    status: str
    remaining_seconds: Optional[int] = None
    server_now: Optional[datetime] = None
    is_adhoc: bool = False


class SnoozeRequest(BaseModel):
    minutes: int


class AlarmConfig(BaseModel):
    sound: str
    volume_percent: int


class AlarmConfigUpdate(BaseModel):
    sound: Optional[str] = None
    volume_percent: Optional[int] = None


class InteractionHistoryItem(BaseModel):
    id: int
    schedule_instance_id: int
    task_name: str
    category: str
    alert_type: str
    alert_started_at: datetime
    response_type: Optional[str] = None
    response_stage: Optional[str] = None
    responded_at: Optional[datetime] = None


class AdhocTodayTaskCreate(BaseModel):
    name: str
    category: str
    duration_minutes: int
    start_time: time
