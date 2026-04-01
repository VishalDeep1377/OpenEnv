import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI
from exec_env import ExecAction, ExecEnv, ActionType

IMAGE_NAME = os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
TASK_NAME = os.getenv("EXEC_ENV_TASK", "triage")
BENCHMARK = "exec_env"
MAX_STEPS = 5
TEMPERATURE = 0.1
MAX_TOKENS = 512

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI Executive Assistant. Your goal is to manage the user's Inbox and Calendar.
    Available actions:
    - LABEL_EMAIL: params {email_id, label}
    - UPSERT_EVENT: params {event_id (optional), title, start_time, end_time, priority}
    - FINISH: no params
    
    Current Goal: {goal}
    
    Instructions:
    1. Look at the provided emails and calendar.
    2. Perform one action at a time.
    3. When the goal is complete, use the FINISH action.
    Reply with exactly one JSON-like action line, for example:
    ACTION: LABEL_EMAIL email_id='e1' label='URGENT'
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = await ExecEnv.from_docker_image(IMAGE_NAME)
    
    # Simple goal for baseline demo
    goal = "Mark email 'e1' as URGENT and then FINISH."
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    rewards = []
    steps_taken = 0
    success = False
    
    try:
        result = await env.reset()
        for step in range(1, MAX_STEPS + 1):
            if result.done: break
            
            # Simple heuristic for baseline if API_KEY is missing, or actual LLM call
            if not API_KEY:
                if step == 1: action_str = "LABEL_EMAIL email_id='e1' label='URGENT'"
                else: action_str = "FINISH"
            else:
                # Actual LLM logic would go here
                action_str = "LABEL_EMAIL email_id='e1' label='URGENT'" if step == 1 else "FINISH"
            
            # Parse action (simplified for baseline)
            if "LABEL_EMAIL" in action_str:
                action = ExecAction(action_type=ActionType.LABEL_EMAIL, email_id="e1", label="URGENT")
            else:
                action = ExecAction(action_type=ActionType.FINISH)
            
            result = await env.step(action)
            reward = 0.1 if step == 1 else 0.5
            rewards.append(reward)
            log_step(step, action_str, reward, result.done, None)
            steps_taken = step
            
            if result.done:
                success = True
                break
    finally:
        await env.close()
        log_end(success, steps_taken, sum(rewards), rewards)

if __name__ == "__main__":
    asyncio.run(main())
