import uvicorn
import sys
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, List
from dotenv import load_dotenv
import gradio as gr
import pandas as pd
import json
import asyncio

# Add the parent directory to sys.path so we can import env and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exec_env import ExecEnv
from models import ExecAction

# Load local environment variables from .env file
load_dotenv()

app = FastAPI(title="ExecEnv Server")
env_instance = ExecEnv()



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

# --- WebSocket Infrastructure (Advanced Feature) ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Periodically push the state to the client
            state = env_instance.state()
            await websocket.send_json(state.model_dump())
            await asyncio.sleep(1) # Stream every second
    except WebSocketDisconnect:
        pass

# --- Gradio Judge Dashboard (Task 3 Optimization) ---

def get_dashboard_data():
    """Formats the current environment state for the Gradio UI."""
    state = env_instance.state()
    
    # Format Emails with Priority Markers
    emails_data = []
    for e in state.emails:
        priority = "URGENT" if "URGENT" in e.labels else "NORMAL"
        emails_data.append({
            "ID": e.id,
            "Sender": e.sender,
            "Subject": e.subject,
            "Priority": priority,
            "Labels": ", ".join(e.labels) if e.labels else "-"
        })
    
    # Format Calendar with Priority Highlighting
    calendar_data = []
    for c in state.calendar:
        # Simple ISO date formatting for readability
        time_str = c.start_time.split("T")[1][:5] if "T" in c.start_time else c.start_time
        calendar_data.append({
            "Time": time_str,
            "Event": c.title,
            "Priority": c.priority,
            "ID": c.id
        })
    
    # Professional Trust Gauge (HTML)
    trust_label = state.trust_level
    trust_score = state.trust_score * 100
    color = "#22c55e" if trust_label == "STABLE" else "#eab308" if trust_label == "WARNING" else "#ef4444"
    
    trust_html = f"""
    <div style='background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
            <span style='color: #94a3b8; font-size: 0.875rem; font-weight: 500;'>BOSS'S TRUST</span>
            <span style='background: {color}22; color: {color}; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; border: 1px solid {color}44;'>{trust_label}</span>
        </div>
        <div style='height: 8px; background: #334155; border-radius: 4px; overflow: hidden;'>
            <div style='height: 100%; width: {trust_score}%; background: {color}; transition: width 0.5s ease-in-out;'></div>
        </div>
        <div style='margin-top: 6px; text-align: right; color: #94a3b8; font-size: 0.75rem;'>{trust_score:.1f}% Reliability</div>
    </div>
    """
    
    # Metadata info
    task_id = state.active_task_id or "NONE"
    status_html = f"<div style='color: #94a3b8;'><b>Active Task:</b> {task_id.upper()}</div>"
    
    # Reasoning Trace (Advanced UI)
    reasoning_trace = state.info.get("reasoning_trace", "No reasoning recorded yet.")
    
    return pd.DataFrame(emails_data), pd.DataFrame(calendar_data), trust_html, status_html, reasoning_trace

async def run_reset_ui(task_id):
    await env_instance.reset(task_id=task_id)
    return get_dashboard_data()

with gr.Blocks() as ui:
    with gr.Sidebar(label="Command Center"):
        gr.Markdown("## 🤖 ExecEnv Core")
        gr.Markdown("Socially Intelligent Assistant Control")
        
        trust_box = gr.HTML()
        status_box = gr.HTML()
        
        gr.Markdown("---")
        task_select = gr.Dropdown(
            choices=["triage", "schedule", "reschedule", "chaos"], 
            label="Initialize Task", 
            value="triage"
        )
        reset_btn = gr.Button("🔄 Reset Environment", variant="primary")
        
        gr.Markdown("---")
        gr.Markdown("### 📡 System Telemetry")
        gr.HTML("<div style='color: #64748b; font-size: 0.75rem;'>v2.1.0-advanced<br>Status: ONLINE</div>")

    with gr.Column():
        gr.Markdown("# 🚀 Executive Assistant Workspace")
        
        with gr.Tabs():
            with gr.TabItem("📥 Communication Center"):
                gr.Markdown("### Active Inbox")
                email_table = gr.DataFrame(interactive=False, wrap=True)
            
            with gr.TabItem("📅 Scheduling Matrix"):
                gr.Markdown("### Calendar Snapshot")
                calendar_table = gr.DataFrame(interactive=False)
                
            with gr.TabItem("🧠 Agent Reasoning"):
                gr.Markdown("### Real-time Chain-of-Thought")
                reasoning_box = gr.TextArea(
                    label="Internal Thinking Process",
                    interactive=False, 
                    lines=15,
                    max_lines=20
                )

    # Initial and button-triggered updates
    output_comps = [email_table, calendar_table, trust_box, status_box, reasoning_box]
    ui.load(get_dashboard_data, None, output_comps)
    reset_btn.click(run_reset_ui, inputs=[task_select], outputs=output_comps)
    
    # Auto-refresh logic (2 seconds)
    gr.Timer(2).tick(get_dashboard_data, None, output_comps)

# Mount Gradio to the FastAPI app at root / for HF Spaces visibility
app = gr.mount_gradio_app(app, ui, path="/")

# --- End Dashboard ---

# The official [project.scripts] entry point
def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
