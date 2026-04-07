import os
import uuid
import asyncio
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

# --- Models ---
class ActionType(str, Enum):
    LABEL_EMAIL = "LABEL_EMAIL"
    SEND_EMAIL = "SEND_EMAIL"
    UPSERT_EVENT = "UPSERT_EVENT"
    DELETE_EVENT = "DELETE_EVENT"
    FINISH = "FINISH"

class ExecAction(BaseModel):
    action_type: ActionType
    email_id: Optional[str] = None
    label: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    event_id: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    priority: Optional[str] = None

class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    labels: List[str] = []

class CalendarEvent(BaseModel):
    id: str
    title: str
    start_time: str
    end_time: str
    priority: str = "LOW"

class ExecObservation(BaseModel):
    emails: List[Email]
    calendar: List[CalendarEvent]
    last_action_error: Optional[str] = None

class ExecResult(BaseModel):
    observation: ExecObservation
    reward: float = 0.0
    done: bool = False
    info: dict = {}

# --- Environment ---
class ExecEnv:
    def __init__(self):
        self._emails: List[Email] = []
        self._calendar: List[CalendarEvent] = []
        self._last_error: Optional[str] = None
        self._done = False
        self.active_task = None
        self.reset_state()

    @property
    def emails(self) -> List[Email]:
        return self._emails

    @property
    def calendar(self) -> List[CalendarEvent]:
        return self._calendar

    @classmethod
    async def from_docker_image(cls, image_name: str):
        # In a real OpenEnv, this would connect to a remote container.
        # For the baseline script in the repo, we use the local class.
        return cls()

    def reset_state(self):
        self._emails = [
            Email(id="e1", sender="hr@company.com", subject="Urgent: Benefits Update", body="Please review the updated benefits by EOD."),
            Email(id="e2", sender="noreply@spam.com", subject="WIN A CAR!!!", body="Click here to claim your free car now!"),
            Email(id="e3", sender="alice@colleague.com", subject="Coffee tomorrow?", body="Are you free for a quick coffee at 10 AM tomorrow?"),
            Email(id="e4", sender="boss@company.com", subject="Board Meeting", body="The Board Meeting is confirmed for 2 PM tomorrow."),
            Email(id="e5", sender="project-x@team.com", subject="Weekly Sync", body="Just a reminder for our weekly sync at 2 PM tomorrow."),
        ]
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        self._calendar = [
            CalendarEvent(id="c1", title="Project Sync", start_time=tomorrow.isoformat(), end_time=(tomorrow + timedelta(hours=1)).isoformat(), priority="LOW"),
        ]
        self._last_error = None
        self._done = False

    async def reset(self, task_id: Optional[str] = None) -> ExecResult:
        from tasks import get_tasks
        self.reset_state()
        
        # Select active task by ID or class name
        tasks = get_tasks()
        task_id = (task_id or "triage").lower()
        
        if "triage" in task_id:
            self.active_task = tasks[0]
        elif "schedule" in task_id:
            self.active_task = tasks[1]
        elif "reschedule" in task_id:
            self.active_task = tasks[2]
        else:
            self.active_task = tasks[0]
            
        return ExecResult(observation=self._get_obs(), reward=0.0, done=False)

    def _get_obs(self) -> ExecObservation:
        return ExecObservation(
            emails=[e for e in self._emails if "ARCHIVE" not in e.labels],
            calendar=self._calendar,
            last_action_error=self._last_error
        )

    async def step(self, action: ExecAction) -> ExecResult:
        self._last_error = None
        reward = 0.0
        
        if action.action_type == ActionType.LABEL_EMAIL:
            for e in self._emails:
                if e.id == action.email_id:
                    if action.label not in e.labels: e.labels.append(action.label)
                    break
        elif action.action_type == ActionType.UPSERT_EVENT:
            new_ev = CalendarEvent(
                id=action.event_id or str(uuid.uuid4()),
                title=action.title or "New Event",
                start_time=action.start_time or datetime.now().isoformat(),
                end_time=action.end_time or (datetime.now() + timedelta(hours=1)).isoformat(),
                priority=action.priority or "LOW"
            )
            if action.event_id:
                self._calendar = [e if e.id != action.event_id else new_ev for e in self._calendar]
            else:
                self._calendar.append(new_ev)
        elif action.action_type == ActionType.FINISH:
            self._done = True

        if self.active_task:
            reward = self.active_task.evaluate(self)

        return ExecResult(observation=self._get_obs(), reward=reward, done=self._done)

    async def close(self):
        pass
