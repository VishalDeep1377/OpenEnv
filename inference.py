import asyncio
import os
import textwrap
import sys
import re
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import httpx

# Load local environment variables if present
load_dotenv()

# Import local modules
from exec_env import ActionType, ExecAction, ExecEnv, ExecObservation, ExecResult, Email
from tasks import get_tasks, Task
from models import calculate_priority_score

# Strictly use the API_BASE_URL and API_KEY environment variables as requested by the validator
# This ensures compliance with the mandatory LiteLLM proxy requirement.
# Aligning exactly with the checklist snippet:
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") # Strictly no hardcoded default


# Optional - for from_docker_image() or live server connection
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
ENV_URL = os.getenv("ENV_URL") # E.g., http://localhost:7860

TASK_NAME = os.getenv("EXEC_ENV_TASK", "triage")
BENCHMARK = "exec_env"
MAX_STEPS = 10
TEMPERATURE = 0.0
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.1
MAX_TOTAL_REWARD = 2.0  # Normalized for the 2-step baseline triage task

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI Executive Assistant. 
    1. First, explain your reasoning in <thinking>...</thinking>. Summarize what you have done and what remains.
    2. Then, provide EXACTLY ONE action in the format: ACTION: ACTION_TYPE key='val'
    
    IMPORTANT: Do not output multiple ACTION lines. Do not repeat an action if the observation shows it was already successful.
    Available actions: LABEL_EMAIL (keys: email_id, label), UPSERT_EVENT (keys: title, start_time, priority), FINISH.
    """
).strip()

def parse_action(response: str) -> ExecAction:
    """Parses the LLM response string into an ExecAction object."""
    match = re.search(r"ACTION:\s*(\w+)(.*)", response)
    if not match:
        return ExecAction(action_type=ActionType.FINISH)
    
    action_type_str = match.group(1)
    params_str = match.group(2)
    
    # Handles: key='val', key="val", key=val, key='val', ...
    params = {}
    param_matches = re.finditer(r"(\w+)=(['\"]?)(.*?)\2(?=[\s,]|$)", params_str)
    for m in param_matches:
        params[m.group(1)] = m.group(3)
    
    try:
        action_type = ActionType(action_type_str)
        return ExecAction(action_type=action_type, **params)
    except ValueError:
        return ExecAction(action_type=ActionType.FINISH)
    except Exception:
        # Pydantic validation error if params are wrong
        return ExecAction(action_type=ActionType.FINISH)
    
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if (error and error.strip()) else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)

class HttpExecEnv:
    """A client-side proxy for the ExecEnv server to enable live dashboard updates."""
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def reset(self, task_id: str) -> ExecResult:
        resp = await self.client.post("/reset", params={"task_id": task_id})
        return ExecResult(**resp.json())

    async def step(self, action: ExecAction) -> ExecResult:
        resp = await self.client.post("/step", json=action.model_dump())
        return ExecResult(**resp.json())

    async def close(self):
        await self.client.aclose()

async def run_task(task_id: str, client: OpenAI, env: ExecEnv):

    tasks = get_tasks()
    selected_task = next((t for t in tasks if t.__class__.__name__.lower().startswith(task_id.lower())), tasks[0])
    goal = selected_task.get_goal()
    
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    rewards = []
    steps_taken = 0
    
    success = False
    final_score = 0.0
    try:
        result = await env.reset(task_id=task_id)
        for step in range(1, MAX_STEPS + 1):
            if result.done: break
            
            # 1. State Augmentation for Judging (Hints)
            ai_hints = [f"Email {e.id} (Sub: {e.subject}): PyTorch Priority={calculate_priority_score(f'{e.subject} {e.body}'):.3f}" for e in result.observation.emails]
            obs_text = f"Observation: {result.observation.model_dump_json()}\nAI Analysis: {ai_hints}\nGoal: {goal}"
            if result.observation.last_action_error:
                obs_text = f"PREVIOUS ERROR: {result.observation.last_action_error}\n{obs_text}"

            # 2. LLM Inference (Nemotron/Qwen)
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": obs_text}],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS + 256
                )
                raw_res = response.choices[0].message.content.strip()
                
                # 3. Extract CoT Thinking Trace & Clean Action
                thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_res, re.DOTALL)
                if thinking_match: 
                    thought = thinking_match.group(1).strip()
                    # Log thought to stderr and env info for dashboard visibility
                    print(f"🧠 [THOUGHT] {thought[:100]}...", file=sys.stderr)
                    if hasattr(env, "info") or isinstance(env, HttpExecEnv):
                        # Attempt to store reasoning in state info (server side handling)
                        pass
                
                action_match = re.search(r"ACTION:\s*(.*)", raw_res)
                action_str = action_match.group(0).strip() if action_match else "ACTION: FINISH"
            except Exception as e:
                print(f"LLM Error: {e}", file=sys.stderr)
                action_str = "ACTION: FINISH"

            # 4. Environment Step
            action = parse_action(action_str)
            result = await env.step(action)
            
            # 5. Mandatory Structured Logging
            log_step(step, action_str, result.reward, result.done, result.observation.last_action_error)
            rewards.append(result.reward)
            steps_taken = step
            if result.done: break

        # Finalize
        final_score = selected_task.evaluate(env)
        final_score = min(max(final_score, 0.01), 0.99)
        success = final_score >= SUCCESS_SCORE_THRESHOLD
    finally:
        log_end(success, steps_taken, rewards)
    return final_score

async def main() -> None:
    if not HF_TOKEN:
        print("Error: HF_TOKEN environment variable must be set.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    if ENV_URL:
        print(f"📡 Connecting to Live Environment at {ENV_URL}...", file=sys.stderr)
        env = HttpExecEnv(ENV_URL)
    else:
        print("🏠 Running in Local Standalone Mode (Hackathon Logic)", file=sys.stderr)
        env = await ExecEnv.from_docker_image(LOCAL_IMAGE_NAME)
    
    # Task Filtering Logic for Validator Compliance
    requested_task = os.getenv("EXEC_ENV_TASK", "").lower()
    all_tasks = ["triage", "schedule", "reschedule", "chaos"]
    
    if requested_task and requested_task in all_tasks:
        target_tasks = [requested_task]
    else:
        # Default to running all if no specific task is requested (local benchmark mode)
        target_tasks = all_tasks
    
    scores = {}
    for t_id in target_tasks:
        try:
            score = await run_task(t_id, client, env)
            scores[t_id] = score
        except Exception as e:
            print(f"Task {t_id} failed with error: {e}", file=sys.stderr)
    
    await env.close()
    
    # Holistic breakdown (stderr only to avoid breaking stdout parser)
    print("\n--- BENCHMARK SUMMARY ---", file=sys.stderr)
    for tid, s in scores.items():
        print(f"Task: {tid:12} Score: {s:.2f}", file=sys.stderr)
    print("-------------------------\n", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())

