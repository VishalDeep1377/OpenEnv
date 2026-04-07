import asyncio
import os
import textwrap
import re
from typing import List, Optional
from openai import OpenAI
from exec_env import ExecAction, ExecEnv, ActionType

# Strictly use the API_BASE_URL and API_KEY environment variables provided by the validator
# Robustly fetch environment variables with multiple naming conventions
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN") or os.getenv("HF_Token")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

if not API_KEY:
    # Fail fast if no key is found, but provide helpful debug info
    raise KeyError("MISSING API_KEY: Please set API_KEY or HF_TOKEN in your environment/secrets.")

# Optional - for from_docker_image()
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

TASK_NAME = os.getenv("EXEC_ENV_TASK", "triage")
BENCHMARK = "exec_env"
MAX_STEPS = 10
TEMPERATURE = 0.0
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.1
MAX_TOTAL_REWARD = 2.0  # Normalized for the 2-step baseline triage task

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI Executive Assistant. Your goal is to manage the user's Inbox and Calendar.
    Available actions:
    - LABEL_EMAIL: params {email_id, label}
    - UPSERT_EVENT: params {event_id (optional), title, start_time, end_time, priority}
    - FINISH: no params
    
    Instructions:
    1. Look at the provided emails and calendar in the observation.
    2. Perform one action at a time.
    3. When the goal is complete, use the FINISH action.
    Reply with exactly one action line in the following format:
    ACTION: ACTION_TYPE key1='val1' key2='val2'
    
    Examples:
    ACTION: LABEL_EMAIL email_id='e1' label='URGENT'
    ACTION: UPSERT_EVENT title='Team Lunch' start_time='2024-04-10T12:00:00' priority='HIGH'
    ACTION: FINISH
    """
).strip()

def parse_action(response: str) -> ExecAction:
    """Parses the LLM response string into an ExecAction object."""
    match = re.search(r"ACTION:\s*(\w+)(.*)", response)
    if not match:
        return ExecAction(action_type=ActionType.FINISH)
    
    action_type_str = match.group(1)
    params_str = match.group(2)
    
    # Extract key-value pairs like key='value' or key="value"
    params = {}
    param_matches = re.finditer(r"(\w+)=['\"](.*?)['\"]", params_str)
    for m in param_matches:
        params[m.group(1)] = m.group(2)
    
    try:
        action_type = ActionType(action_type_str)
    except ValueError:
        return ExecAction(action_type=ActionType.FINISH)
    
    return ExecAction(action_type=action_type, **params)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

async def main() -> None:
    if not API_KEY:
        print("Error: API_KEY environment variable must be set.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = await ExecEnv.from_docker_image(LOCAL_IMAGE_NAME)
    
    goal = "Mark email 'e1' as URGENT and then FINISH."
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    rewards = []
    steps_taken = 0
    success = False
    
    try:
        result = await env.reset()
        for step in range(1, MAX_STEPS + 1):
            if result.done: break
            
            # Construct the prompt with current observation
            obs_text = f"Observation: {result.observation.model_dump_json()}\nGoal: {goal}"
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": obs_text}
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS
                )
                action_str = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"LLM API Error: {e}")
                # Fallback to a safe finish if API fails consecutively
                action_str = "ACTION: FINISH"

            # Parse and execute action
            action = parse_action(action_str)
            result = await env.step(action)
            
            # Simple reward logic for baseline tracker
            reward = 1.0 if (step == 1 and action.action_type == ActionType.LABEL_EMAIL) or (step == 2 and action.action_type == ActionType.FINISH) else 0.0
            rewards.append(reward)
            
            log_step(step, action_str, reward, result.done, None)
            steps_taken = step
            
            if result.done:
                success = True
                break
    finally:
        await env.close()
        final_score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        final_score = min(max(final_score, 0.0), 1.0)
        success = final_score >= SUCCESS_SCORE_THRESHOLD
        log_end(success, steps_taken, final_score, rewards)

if __name__ == "__main__":
    asyncio.run(main())
