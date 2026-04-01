import uvicorn
import sys
import os
from fastapi import FastAPI, HTTPException

# Add the parent directory to sys.path so we can import env and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import ExecEnv
from models import ExecAction

app = FastAPI(title="ExecEnv Server")
env_instance = ExecEnv()

@app.get("/")
def read_root():
    return {"message": "ExecEnv Server is running", "mode": "multi-mode deployment"}

@app.post("/reset")
async def reset():
    return {"observation": env_instance.reset()}

@app.post("/step")
async def step(action: ExecAction):
    obs, reward, done, info = env_instance.step(action)
    return {"observation": obs, "reward": reward, "done": done, "info": info}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# The official [project.scripts] entry point
def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
