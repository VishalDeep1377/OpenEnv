from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
import torch
import torch.nn as nn
import hashlib
import numpy as np

# --- PyTorch Judging Integration ---
# This module implements a lightweight classification model to assist the LLM
# by automatically ranking the priority of emails and events.

class PriorityModel(nn.Module):
    """A lightweight MLP for text-based priority scoring (Judging Optimization)."""
    def __init__(self, vocab_size=5000, embed_dim=16):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.fc = nn.Sequential(
            nn.Linear(embed_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )
        # Seed for reproducible "heuristic" scores in demonstration
        torch.manual_seed(42)

    def forward(self, x):
        # x shape: (seq_len)
        embeds = self.embedding(x) # (seq_len, embed_dim)
        pooled = torch.mean(embeds, dim=0) # (embed_dim)
        score = self.fc(pooled)
        return score

# Global singleton model for inference
_MODEL_INSTANCE = None
def get_priority_model():
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = PriorityModel()
        _MODEL_INSTANCE.eval()
    return _MODEL_INSTANCE

def get_text_embedding(text: str, vocab_size=5000):
    """Simple hash-based tokenizer for demonstration purposes."""
    words = text.lower().split()
    indices = []
    for w in words:
        # Map word to a vocab index using stable hash
        idx = int(hashlib.md5(w.encode()).hexdigest(), 16) % vocab_size
        indices.append(idx)
    if not indices: return torch.tensor([0], dtype=torch.long)
    return torch.tensor(indices, dtype=torch.long)

def calculate_priority_score(text: str) -> float:
    """Calculates a 0.0-1.0 priority score for a given text snippet."""
    model = get_priority_model()
    with torch.no_grad():
        indices = get_text_embedding(text)
        score = model(indices).item()
    return score

# --- End PyTorch Integration ---

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

class TrustLevel(str, Enum):
    """The perceived reliability of the agent from the boss's perspective."""
    STABLE = "STABLE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class ExecObservation(BaseModel):
    """The perceived state of the environment returned to the agent."""
    emails: List[Email] = Field(..., description="Snapshot of the current active inbox.")
    calendar: List[CalendarEvent] = Field(..., description="Snapshot of the upcoming schedule.")
    trust_level: TrustLevel = Field(TrustLevel.STABLE, description="Current trust standing with the virtual boss.")
    last_action_error: Optional[str] = Field(None, description="Error telemetry from the preceding step.")

class ExecState(BaseModel):
    """The full internal state of the environment (not visible to agent)."""
    emails: List[Email] = Field(..., description="All emails including archived ones.")
    calendar: List[CalendarEvent] = Field(..., description="Full calendar roster.")
    trust_score: float = Field(0.99, description="Numerical trust metric (0.01 - 0.99).")
    active_task_id: Optional[str] = Field(None, description="ID of the task currently being tracked.")
    done: bool = Field(False, description="Whether the current episode has terminated.")

class ExecResult(BaseModel):
    """Container for the output of an environment step or reset."""
    observation: ExecObservation = Field(..., description="Agent-facing observation.")
    reward: float = Field(0.01, description="Step reward (0.0 - 1.0).")
    done: bool = Field(False, description="Termination signal.")
    info: dict = Field(default_factory=dict, description="Metadata and diagnostic info.")


