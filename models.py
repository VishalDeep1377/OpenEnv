from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    LABEL_EMAIL = "LABEL_EMAIL"
    SEND_EMAIL = "SEND_EMAIL"
    UPSERT_EVENT = "UPSERT_EVENT"
    DELETE_EVENT = "DELETE_EVENT"
    FINISH = "FINISH"

class ExecAction(BaseModel):
    """The formal action schema for the ExecEnv assistant agents."""
    action_type: ActionType = Field(..., description="The primitive action to execute in the workspace.")
    email_id: Optional[str] = Field(None, description="Unique identifier for the target email.")
    label: Optional[str] = Field(None, description="Label to apply (e.g., 'URGENT', 'SPAM', 'ARCHIVE').")
    to: Optional[str] = Field(None, description="Recipient address for automated email outreach.")
    subject: Optional[str] = Field(None, description="Subject line for email communications.")
    body: Optional[str] = Field(None, description="Content body for email communications.")
    event_id: Optional[str] = Field(None, description="Target calendar event ID for updates or deletions.")
    title: Optional[str] = Field(None, description="Display title for the calendar event.")
    start_time: Optional[str] = Field(None, description="ISO-8601 formatted start time for the event.")
    end_time: Optional[str] = Field(None, description="ISO-8601 formatted end time for the event.")
    priority: str = Field("LOW", description="Event priority classification: LOW, MEDIUM, or HIGH.")

class Email(BaseModel):
    """Internal representation of a workspace communication."""
    id: str = Field(..., description="Primary key of the email.")
    sender: str = Field(..., description="The originating email address.")
    subject: str = Field(..., description="The email subject line.")
    body: str = Field(..., description="The raw text content of the email.")
    labels: List[str] = Field(default_factory=list, description="Associated organizational tags.")

class CalendarEvent(BaseModel):
    """Internal representation of a scheduled time block."""
    id: str = Field(..., description="Primary key of the calendar event.")
    title: str = Field(..., description="The name/summary of the appointment.")
    start_time: str = Field(..., description="Start timestamp in ISO-8601.")
    end_time: str = Field(..., description="End timestamp in ISO-8601.")
    priority: str = Field("LOW", description="The importance level of the event.")

class ExecObservation(BaseModel):
    """The perceived state of the environment returned to the agent."""
    emails: List[Email] = Field(..., description="Snapshot of the current active inbox.")
    calendar: List[CalendarEvent] = Field(..., description="Snapshot of the upcoming 48-hour schedule.")
    last_action_error: Optional[str] = Field(None, description="Error telemetry from the preceding step.")

class ExecReward(BaseModel):
    reward: float = Field(..., description="The reward value (0.0 - 1.0 or delta)")
    done: bool = Field(..., description="Whether the episode is finished")
    info: dict = Field(default_factory=dict, description="Additional diagnostic information")
