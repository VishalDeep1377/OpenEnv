from abc import ABC, abstractmethod
from typing import List, Tuple
from exec_env import ExecEnv
from models import Email, ActionType

class Task(ABC):
    @abstractmethod
    def get_goal(self) -> str:
        pass
    
    @abstractmethod
    def evaluate(self, env: ExecEnv) -> float:
        pass

class EasyTriageTask(Task):
    def get_goal(self) -> str:
        return "Mark the HR email (Benefits Update) as 'URGENT' and delete (label as 'ARCHIVE') the 'WIN A CAR!!!' spam email."
    
    def evaluate(self, env: ExecEnv) -> float:
        score = 0.0
        # Check HR email (e1)
        for email in env.emails:
            if email.id == "e1" and "URGENT" in email.labels:
                score += 0.5
            if email.id == "e2" and "ARCHIVE" in email.labels:
                score += 0.5
        return min(score, 1.0)

class MediumSchedulingTask(Task):
    def get_goal(self) -> str:
        return "Based on Alice's email, schedule a 'Coffee with Alice' for 10 AM tomorrow. It should last 30 minutes."
    
    def evaluate(self, env: ExecEnv) -> float:
        score = 0.0
        # Find 10 AM tomorrow event
        for ev in env.calendar:
            if "Alice" in ev.title and "10:00:00" in ev.start_time:
                score = 1.0
                break
        return score

class HardConflictTask(Task):
    def get_goal(self) -> str:
        return ("A Board Meeting is mandatory for 2 PM tomorrow. Reschedule the 'Project Sync' (which is also at 2 PM) "
                "to 4 PM and then create the Board Meeting event at 2 PM with HIGH priority.")
    
    def evaluate(self, env: ExecEnv) -> float:
        score = 0.0
        sync_moved = False
        board_created = False
        
        for ev in env.calendar:
            if "Project Sync" in ev.title and "16:00:00" in ev.start_time:
                sync_moved = True
            if "Board Meeting" in ev.title and "14:00:00" in ev.start_time and ev.priority == "HIGH":
                board_created = True
        
        if sync_moved: score += 0.5
        if board_created: score += 0.5
        return min(score, 1.0)

def get_tasks() -> List[Task]:
    return [EasyTriageTask(), MediumSchedulingTask(), HardConflictTask()]
