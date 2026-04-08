import uvicorn
import sys
import os
from fastapi import FastAPI, HTTPException
from typing import Optional
from dotenv import load_dotenv
import gradio as gr
import pandas as pd

# Add the parent directory to sys.path so we can import env and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exec_env import ExecEnv
from models import ExecAction

# Load local environment variables from .env file
load_dotenv()

app = FastAPI(title="ExecEnv Server")
env_instance = ExecEnv()

@app.get("/")
def read_root():
    return {"message": "ExecEnv Server is running", "mode": "multi-mode deployment"}

@app.post("/reset")
async def reset(task_id: Optional[str] = None):
    return await env_instance.reset(task_id=task_id)

@app.post("/step")
async def step(action: ExecAction):
    return await env_instance.step(action)

@app.get("/state")
async def state():
    """Mandatory endpoint returning the full internal environment state."""
    return env_instance.state()


@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Gradio Judge Dashboard (Task 3 Optimization) ---

def get_dashboard_data():
    """Formats the current environment state for the Gradio UI."""
    state = env_instance.state()
    
    # Format Emails
    emails_data = [
        {"ID": e.id, "Sender": e.sender, "Subject": e.subject, "Labels": ", ".join(e.labels)}
        for e in state.emails
    ]
    
    # Format Calendar
    calendar_data = [
        {"ID": c.id, "Title": c.title, "Start": c.start_time, "Priority": c.priority}
        for c in state.calendar
    ]
    
    # Trust Formatting
    trust_label = state.trust_level
    trust_color = "green" if trust_label == "STABLE" else "red"
    trust_html = f"<b style='color: {trust_color}; font-size: 20px;'>{trust_label}</b>"
    
    return pd.DataFrame(emails_data), pd.DataFrame(calendar_data), trust_html

async def run_reset_ui(task_id):
    await env_instance.reset(task_id=task_id)
    return get_dashboard_data()

with gr.Blocks(title="OpenEnv Executive Dashboard", theme=gr.themes.Soft()) as ui:
    gr.Markdown("# 🚀 OpenEnv Executive Assistant Dashboard")
    gr.Markdown("This dashboard allows judges to visually inspect the environment state during the agent's execution.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🛡️ Boss's Trust Standing")
            trust_box = gr.HTML()
            task_select = gr.Dropdown(choices=["triage", "schedule", "reschedule"], label="Active Task", value="triage")
            reset_btn = gr.Button("🔄 Reset Environment", variant="primary")
        
        with gr.Column(scale=3):
            gr.Markdown("### 📥 Active Inbox")
            email_table = gr.DataFrame(interactive=False)
            
    with gr.Row():
        gr.Markdown("### 📅 Calendar Snapshot")
        calendar_table = gr.DataFrame(interactive=False)

    # Initial and button-triggered updates
    ui.load(get_dashboard_data, None, [email_table, calendar_table, trust_box])
    reset_btn.click(run_reset_ui, inputs=[task_select], outputs=[email_table, calendar_table, trust_box])
    
    # Auto-refresh every 2 seconds to show the judge what the agent is doing
    gr.Timer(2).tick(get_dashboard_data, None, [email_table, calendar_table, trust_box])

# Mount Gradio to the FastAPI app at root / for HF Spaces visibility
app = gr.mount_gradio_app(app, ui, path="/")

# --- End Dashboard ---

# The official [project.scripts] entry point
def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
