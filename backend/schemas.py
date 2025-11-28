from datetime import date, time
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


class SnoozeRequest(BaseModel):
    minutes: int


class AlarmConfig(BaseModel):
    sound: str
    volume_percent: int


class AlarmConfigUpdate(BaseModel):
    sound: Optional[str] = None
    volume_percent: Optional[int] = None
