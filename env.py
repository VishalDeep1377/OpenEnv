import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from models import ExecAction, ExecObservation, ActionType, Email, CalendarEvent

class ExecEnv:
    def __init__(self):
        self.emails: List[Email] = []
        self.calendar: List[CalendarEvent] = []
        self.last_error: Optional[str] = None
        self.done = False
        self.reset()

    def reset(self) -> ExecObservation:
        # Initial Emails
        self.emails = [
            Email(id="e1", sender="hr@company.com", subject="Urgent: Benefits Update", body="Please review the updated benefits by EOD."),
            Email(id="e2", sender="noreply@spam.com", subject="WIN A CAR!!!", body="Click here to claim your free car now!"),
            Email(id="e3", sender="alice@colleague.com", subject="Coffee tomorrow?", body="Are you free for a quick coffee at 10 AM tomorrow?"),
            Email(id="e4", sender="boss@company.com", subject="Board Meeting", body="The Board Meeting is confirmed for 2 PM tomorrow. Attendance is mandatory."),
            Email(id="e5", sender="project-x@team.com", subject="Weekly Sync", body="Just a reminder for our weekly sync at 2 PM tomorrow."),
        ]
        
        # Initial Calendar
        base_time = datetime.now() + timedelta(days=1)
        tomorrow_2pm = base_time.replace(hour=14, minute=0, second=0, microsecond=0)
        
        self.calendar = [
            CalendarEvent(id="c1", title="Project Sync", start_time=tomorrow_2pm.isoformat(), end_time=(tomorrow_2pm + timedelta(hours=1)).isoformat(), priority="LOW"),
        ]
        
        self.last_error = None
        self.done = False
        return self._get_obs()

    def _get_obs(self) -> ExecObservation:
        return ExecObservation(
            emails=[e for e in self.emails if "ARCHIVE" not in e.labels],
            calendar=self.calendar,
            last_action_error=self.last_error
        )

    def step(self, action: ExecAction) -> Tuple[ExecObservation, float, bool, dict]:
        self.last_error = None
        reward = 0.0
        
        try:
            if action.action_type == ActionType.LABEL_EMAIL:
                for target in self.emails:
                    if target.id == action.email_id:
                        if action.label not in target.labels:
                            target.labels.append(action.label)
                        break
                else:
                    self.last_error = f"Email ID {action.email_id} not found"
            
            elif action.action_type == ActionType.SEND_EMAIL:
                # In a real environment, this might send an actual email or mock it
                pass
            
            elif action.action_type == ActionType.UPSERT_EVENT:
                if action.event_id:
                    for i, ev in enumerate(self.calendar):
                        if ev.id == action.event_id:
                            self.calendar[i] = CalendarEvent(
                                id=ev.id,
                                title=action.title or ev.title,
                                start_time=action.start_time or ev.start_time,
                                end_time=action.end_time or ev.end_time,
                                priority=action.priority or ev.priority
                            )
                            break
                else:
                    new_ev = CalendarEvent(
                        id=str(uuid.uuid4()),
                        title=action.title,
                        start_time=action.start_time,
                        end_time=action.end_time,
                        priority=action.priority or "LOW"
                    )
                    self.calendar.append(new_ev)
            
            elif action.action_type == ActionType.DELETE_EVENT:
                self.calendar = [ev for ev in self.calendar if ev.id != action.event_id]
            
            elif action.action_type == ActionType.FINISH:
                self.done = True

        except Exception as e:
            self.last_error = str(e)
            reward = -0.1
            
        return self._get_obs(), reward, self.done, {}

    def state(self) -> dict:
        return {
            "emails": [e.dict() for e in self.emails],
            "calendar": [c.dict() for c in self.calendar]
        }
