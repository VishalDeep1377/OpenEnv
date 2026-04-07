import uvicorn
import sys
import os
from fastapi import FastAPI, HTTPException
from typing import Optional

# Add the parent directory to sys.path so we can import env and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exec_env import ExecEnv
from models import ExecAction

app = FastAPI(title="ExecEnv Server")
env_instance = ExecEnv()

@app.get("/")
def read_root():
    return {"message": "ExecEnv Server is running", "mode": "multi-mode deployment"}

@app.post("/reset")
async def reset(task_id: Optional[str] = None):
    return {"observation": await env_instance.reset(task_id=task_id)}

@app.post("/step")
async def step(action: ExecAction):
    return await env_instance.step(action)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# The official [project.scripts] entry point
def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
