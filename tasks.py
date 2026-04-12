from abc import ABC, abstractmethod
from typing import List, Tuple, TYPE_CHECKING
from models import Email, ActionType

if TYPE_CHECKING:
    from exec_env import ExecEnv

class Task(ABC):
    @abstractmethod
    def get_goal(self) -> str:
        """Returns the natural language goal for the agent."""
        pass
    
    @abstractmethod
    def evaluate(self, env) -> float:
        """Returns a final score strictly between 0.0 and 1.0 (e.g., 0.01 - 0.99)."""
        pass

    @abstractmethod
    def get_step_reward(self, env, action) -> float:
        """Returns a scalar reward strictly between 0.0 and 1.0 (e.g., 0.01 - 0.99)."""
        pass

class EasyTriageTask(Task):
    def get_goal(self) -> str:
        return "Mark the HR email (e1) as 'URGENT' and move the 'WIN A CAR!!!' spam (e2) to 'ARCHIVE'."
    
    def evaluate(self, env) -> float:
        score = 0.0
        for email in env.emails:
            # Score labels from applied labels
            if email.id == "e1" and "URGENT" in email.labels: score += 0.5
            if email.id == "e2" and "ARCHIVE" in email.labels: score += 0.5
            
        # Success is multiplied by the Boss's Trust
        final_score = score * env.state().trust_score
        return float(max(0.01, min(final_score, 0.99)))

    def get_step_reward(self, env, action) -> float:
        # Robust string matching for circular import safety
        act_type = str(action.action_type).upper()
        email_id = str(action.email_id or "").strip("'\" ")
        label = str(action.label or "").strip("'\" ")
        
        if "LABEL_EMAIL" in act_type:
            if email_id == "e1" and label == "URGENT": return 0.5
            if email_id == "e2" and label == "ARCHIVE": return 0.5
        return 0.01

class MediumSchedulingTask(Task):
    def get_goal(self) -> str:
        return "Alice (e3) wants coffee at 10 AM tomorrow for 30 minutes. Schedule this and ARCHIVE the email."
    
    def evaluate(self, env) -> float:
        score = 0.0
        scheduled = False
        archived = False
        for ev in env.calendar:
            if "Coffee" in ev.title and "10:00:00" in ev.start_time:
                scheduled = True
                break
        for email in env.emails:
            if email.id == "e3" and "ARCHIVE" in email.labels:
                archived = True
                break
        
        if scheduled: score += 0.79
        if archived: score += 0.2
        final_score = score * env.state().trust_score
        return float(max(0.01, min(final_score, 0.99)))

    def get_step_reward(self, env, action) -> float:
        act_type = str(action.action_type).upper()
        title = str(action.title or "").strip("'\" ")
        start_time = str(action.start_time or "").strip("'\" ")
        email_id = str(action.email_id or "").strip("'\" ")
        label = str(action.label or "").strip("'\" ")
        
        if "UPSERT_EVENT" in act_type:
            if "Coffee" in title and "10:00:00" in start_time:
                return 0.79
        if "LABEL_EMAIL" in act_type:
            if email_id == "e3" and label == "ARCHIVE":
                return 0.2
        return 0.01

class HardConflictTask(Task):
    def get_goal(self) -> str:
        return ("A Board Meeting (e4) is mandatory for 2 PM tomorrow. The 'Project Sync' (c1) conflicts. "
                "1. Move 'Project Sync' to 4 PM. 2. Create 'Board Meeting' at 2 PM with HIGH priority.")
    
    def evaluate(self, env) -> float:
        score = 0.0
        sync_moved = any("Project Sync" in ev.title and "16:00:00" in ev.start_time for ev in env.calendar)
        board_created = any("Board Meeting" in ev.title and "14:00:00" in ev.start_time and ev.priority == "HIGH" for ev in env.calendar)
        
        if sync_moved: score += 0.49
        if board_created: score += 0.5
        final_score = score * env.state().trust_score
        return float(max(0.01, min(final_score, 0.99)))

    def get_step_reward(self, env, action) -> float:
        act_type = str(action.action_type).upper()
        event_id = str(action.event_id or "").strip("'\" ")
        start_time = str(action.start_time or "").strip("'\" ")
        title = str(action.title or "").strip("'\" ")
        priority = str(action.priority or "").strip("'\" ")

        if "UPSERT_EVENT" in act_type:
            if event_id == "c1" and "16:00:00" in start_time:
                return 0.49
            if "Board Meeting" in title and "14:00:00" in start_time and priority == "HIGH":
                return 0.5
        return 0.01

class ChaosSchedulingTask(Task):
    """ADVANCED: Tests adaptability to real-time interruptions."""
    def get_goal(self) -> str:
        return "Standard scheduling, but stay alert for emergency interruptions."
    
    def evaluate(self, env) -> float:
        score = 0.0
        # Success if the emergency email was handled (e.g., event created at 3 PM)
        emergency_handled = any("Emergency Zoom" in ev.title and "15:00:00" in ev.start_time for ev in env.calendar)
        if emergency_handled: score = 0.99
        return float(max(0.01, min(score, 0.99)))

    def get_step_reward(self, env, action) -> float:
        act_type = str(action.action_type).upper()
        title = str(action.title or "").strip("'\" ")
        start_time = str(action.start_time or "").strip("'\" ")
        
        if "UPSERT_EVENT" in act_type:
            if "Emergency Zoom" in title and "15:00:00" in start_time:
                return 0.99
        return 0.01

def get_tasks() -> List[Task]:
    return [EasyTriageTask(), MediumSchedulingTask(), HardConflictTask(), ChaosSchedulingTask()]
