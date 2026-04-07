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
        """Returns a final score 0.0 - 1.0 based on current environmental state."""
        pass

    @abstractmethod
    def get_step_reward(self, env, action) -> float:
        """Returns a scalar reward signaling progress during a step (0.0 - 1.0 cumulatively)."""
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
        return min(score * env.state().trust_score, 1.0)

    def get_step_reward(self, env, action) -> float:
        # Robust string matching for circular import safety
        act_type = str(action.action_type)
        if "LABEL_EMAIL" in act_type:
            if action.email_id == "e1" and action.label == "URGENT": return 0.5
            if action.email_id == "e2" and action.label == "ARCHIVE": return 0.5
        return 0.0

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
        
        if scheduled: score += 0.8
        if archived: score += 0.2
        return min(score * env.state().trust_score, 1.0)

    def get_step_reward(self, env, action) -> float:
        act_type = str(action.action_type)
        if "UPSERT_EVENT" in act_type:
            if "Coffee" in (action.title or "") and "10:00:00" in (action.start_time or ""):
                return 0.8
        if "LABEL_EMAIL" in act_type:
            if action.email_id == "e3" and action.label == "ARCHIVE":
                return 0.2
        return 0.0

class HardConflictTask(Task):
    def get_goal(self) -> str:
        return ("A Board Meeting (e4) is mandatory for 2 PM tomorrow. The 'Project Sync' (c1) conflicts. "
                "1. Move 'Project Sync' to 4 PM. 2. Create 'Board Meeting' at 2 PM with HIGH priority.")
    
    def evaluate(self, env) -> float:
        score = 0.0
        sync_moved = any("Project Sync" in ev.title and "16:00:00" in ev.start_time for ev in env.calendar)
        board_created = any("Board Meeting" in ev.title and "14:00:00" in ev.start_time and ev.priority == "HIGH" for ev in env.calendar)
        
        if sync_moved: score += 0.5
        if board_created: score += 0.5
        return min(score * env.state().trust_score, 1.0)

    def get_step_reward(self, env, action) -> float:
        act_type = str(action.action_type)
        if "UPSERT_EVENT" in act_type:
            if action.event_id == "c1" and "16:00:00" in (action.start_time or ""):
                return 0.5
            if "Board Meeting" in (action.title or "") and "14:00:00" in (action.start_time or "") and action.priority == "HIGH":
                return 0.5
        return 0.0

def get_tasks() -> List[Task]:
    return [EasyTriageTask(), MediumSchedulingTask(), HardConflictTask()]
