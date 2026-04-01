import uvicorn
from fastapi import FastAPI, HTTPException
from env import ExecEnv
from models import ExecAction, ExecObservation

# Initialize the global environment instance
app = FastAPI(title="ExecEnv Server", description="OpenEnv server for AI Assistant tasks")
env_instance = ExecEnv()

@app.get("/")
def read_root():
    return {"message": "ExecEnv Server is running", "port": 7860}

@app.post("/reset")
async def reset():
    """Reset the environment to the initial state."""
    try:
        observation = env_instance.reset()
        return {"observation": observation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: ExecAction):
    """Execute a single step in the environment."""
    try:
        observation, reward, done, info = env_instance.step(action)
        return {
            "observation": observation,
            "reward": reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    """Retrieve the current full state of the environment."""
    try:
        return env_instance.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

def main():
    """The entry point for the [project.scripts] 'server' command."""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
