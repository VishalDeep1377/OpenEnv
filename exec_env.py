import os
import uuid
import asyncio
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from models import ActionType, ExecAction, Email, CalendarEvent, ExecObservation, ExecState, TrustLevel, ExecResult

# --- Environment ---
class ExecEnv:
    def __init__(self):
        self._emails: List[Email] = []
        self._calendar: List[CalendarEvent] = []
        self._trust_score = 0.99  # Range strictly within (0, 1)
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
        return cls()

    def reset_state(self):
        # Realistic seed data
        self._emails = [
            Email(id="e1", sender="hr@company.com", subject="Urgent: Benefits Update", body="Review benefits by EOD."),
            Email(id="e2", sender="noreply@spam.com", subject="WIN A CAR!!!", body="Claim your free car now!"),
            Email(id="e3", sender="alice@colleague.com", subject="Coffee tomorrow?", body="Coffee at 10 AM tomorrow?"),
            Email(id="e4", sender="boss@company.com", subject="Board Meeting", body="Board Meeting confirmed for 2 PM tomorrow."),
            Email(id="e5", sender="project-x@team.com", subject="Weekly Sync", body="Weekly sync at 2 PM tomorrow."),
        ]
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        self._calendar = [
            CalendarEvent(id="c1", title="Project Sync", start_time=tomorrow.isoformat(), end_time=(tomorrow + timedelta(hours=1)).isoformat(), priority="LOW"),
        ]
        self._trust_score = 0.99
        self._last_error = None
        self._done = False

    async def reset(self, task_id: Optional[str] = None) -> ExecResult:
        from tasks import get_tasks
        self.reset_state()
        tasks = get_tasks()
        task_id = (task_id or "triage").lower()
        
        if "triage" in task_id: self.active_task = tasks[0]
        elif "schedule" in task_id: self.active_task = tasks[1]
        elif "reschedule" in task_id: self.active_task = tasks[2]
        else: self.active_task = tasks[0]
            
        return ExecResult(observation=self._get_obs(), reward=0.01, done=False)

    def _get_obs(self) -> ExecObservation:
        # Map numerical trust to a categorical level for the agent
        trust_level = TrustLevel.STABLE
        if self._trust_score < 0.4: trust_level = TrustLevel.CRITICAL
        elif self._trust_score < 0.8: trust_level = TrustLevel.WARNING

        return ExecObservation(
            emails=[e for e in self._emails if "ARCHIVE" not in e.labels],
            calendar=self._calendar,
            trust_level=trust_level,
            last_action_error=self._last_error
        )

    def state(self) -> ExecState:
        """Returns the full internal state (mandatory OpenEnv requirement)."""
        return ExecState(
            emails=self._emails,
            calendar=self._calendar,
            trust_score=self._trust_score,
            active_task_id=self.active_task.__class__.__name__ if self.active_task else None,
            done=self._done
        )

    def _update_trust(self, delta: float):
        self._trust_score = max(0.01, min(0.99, self._trust_score + delta))
        if self._trust_score <= 0.01:
            self._last_error = "CRITICAL: The boss has lost all trust in you. Proceed with extreme caution."

    async def step(self, action: ExecAction) -> ExecResult:
        self._last_error = None
        reward = 0.0
        act_type = str(action.action_type)
        
        # Penalize Low-quality or reckless actions - destroying trust
        if "FINISH" not in act_type and not (action.email_id or action.event_id or action.title):
            self._update_trust(-0.2)
            reward -= 0.1

        if "LABEL_EMAIL" in act_type:
            found = False
            for e in self._emails:
                if e.id == action.email_id:
                    if action.label not in e.labels: e.labels.append(action.label)
                    found = True
                    break
            if not found: 
                self._last_error = f"Email ID {action.email_id} not found."
                self._update_trust(-0.1)
                reward -= 0.1

        elif "SEND_EMAIL" in act_type:
            if not (action.to and action.subject):
                self._last_error = "SEND_EMAIL requires 'to' and 'subject'."
                self._update_trust(-0.1)
                reward -= 0.1
            else:
                pass

        elif "UPSERT_EVENT" in act_type:
            new_ev = CalendarEvent(
                id=action.event_id or str(uuid.uuid4()),
                title=action.title or "New Event",
                start_time=action.start_time or datetime.now().isoformat(),
                end_time=action.end_time or (datetime.now() + timedelta(hours=1)).isoformat(),
                priority=action.priority or "LOW"
            )
            if action.event_id:
                old_len = len(self._calendar)
                self._calendar = [e if e.id != action.event_id else new_ev for e in self._calendar]
                if len(self._calendar) == old_len and not any(e.id == action.event_id for e in self._calendar):
                    self._calendar.append(new_ev)
                    self._last_error = f"Event ID {action.event_id} not found. Created new event."
                    self._update_trust(-0.1)
            else:
                self._calendar.append(new_ev)

        elif "DELETE_EVENT" in act_type:
            found = False
            original_len = len(self._calendar)
            self._calendar = [e for e in self._calendar if e.id != action.event_id]
            if len(self._calendar) == original_len:
                self._last_error = f"Event ID {action.event_id} not found."
                reward -= 0.1
            else:
                self._update_trust(-0.05) # Deleting events is a slight trust cost unless required by task

        elif "FINISH" in act_type:
            self._done = True

        # Calculate granular reward signal
        task_step_reward = 0.0
        if self.active_task:
            task_step_reward = self.active_task.get_step_reward(self, action)
            reward += task_step_reward

        # Normalize reward to strictly (0.01, 0.99)
        final_reward = max(0.01, min(0.99, reward))

        return ExecResult(
            observation=self._get_obs(), 
            reward=final_reward, 
            done=self._done,
            info={
                "step_reward": task_step_reward,
                "final_score": self.active_task.evaluate(self) if self.active_task else 0.01,
                "trust_score": self._trust_score,
                "error": self._last_error
            }
        )



    async def close(self):
        pass

