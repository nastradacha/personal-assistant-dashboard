from datetime import date, datetime, time

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from .db import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    default_duration_minutes = Column(Integer, nullable=False)
    recurrence_pattern = Column(String, nullable=True)
    preferred_time_window = Column(String, nullable=True)
    default_alert_style = Column(String, nullable=False, default="visual_then_alarm")
    enabled = Column(Boolean, nullable=False, default=True)

    schedule_instances = relationship(
        "ScheduleInstance",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class ScheduleInstance(Base):
    __tablename__ = "schedule_instances"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    date = Column(Date, nullable=False)
    planned_start_time = Column(Time, nullable=False)
    planned_end_time = Column(Time, nullable=False)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="pending")

    task = relationship("Task", back_populates="schedule_instances")
    snooze_events = relationship(
        "SnoozeEvent",
        back_populates="schedule_instance",
        cascade="all, delete-orphan",
    )
    acknowledge_events = relationship(
        "AcknowledgeEvent",
        back_populates="schedule_instance",
        cascade="all, delete-orphan",
    )
    interactions = relationship(
        "Interaction",
        back_populates="schedule_instance",
        cascade="all, delete-orphan",
    )


class SnoozeEvent(Base):
    __tablename__ = "snooze_events"

    id = Column(Integer, primary_key=True, index=True)
    schedule_instance_id = Column(Integer, ForeignKey("schedule_instances.id"), nullable=False)
    minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    schedule_instance = relationship("ScheduleInstance", back_populates="snooze_events")


class AcknowledgeEvent(Base):
    __tablename__ = "acknowledge_events"

    id = Column(Integer, primary_key=True, index=True)
    schedule_instance_id = Column(Integer, ForeignKey("schedule_instances.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    schedule_instance = relationship("ScheduleInstance", back_populates="acknowledge_events")


class AlarmConfig(Base):
    __tablename__ = "alarm_config"

    id = Column(Integer, primary_key=True, index=True)
    sound = Column(String, nullable=False, default="beep")
    volume_percent = Column(Integer, nullable=False, default=12)


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    schedule_instance_id = Column(
        Integer,
        ForeignKey("schedule_instances.id"),
        nullable=False,
        index=True,
    )
    alert_type = Column(String, nullable=False)
    alert_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    response_type = Column(String, nullable=True)
    response_stage = Column(String, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    schedule_instance = relationship("ScheduleInstance", back_populates="interactions")
