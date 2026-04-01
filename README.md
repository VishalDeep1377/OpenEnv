---
title: ExecEnv
emoji: 💼
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
tags:
  - openenv
---

<div align="center">
  <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/master/icons/briefcase.svg" width="100" height="100">
  <h1>🤖 ExecEnv: The AI Executive Assistant</h1>
  <p><b>State-of-the-Art OpenEnv for Evaluating Autonomous Agent Intelligence</b></p>

  [![OpenEnv-1.0.0](https://img.shields.io/badge/OpenEnv-1.0.0-green?style=for-the-badge&logo=huggingface)](https://github.com/openenv)
  [![Build-Passing](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)](https://huggingface.co/spaces/vishaldeep1022/exec-env-assistant)
  [![Docker-Ready](https://img.shields.io/badge/Deployment-Docker-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)
  [![License-MIT](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](https://opensource.org/licenses/MIT)
</div>

---

## 🌐 The Mission
**ExecEnv** is a production-grade benchmark designed to bridge the gap between "simple chat agents" and "true autonomous assistants." By simulating a professional's **Inbox** and **Calendar**, we force agents to perform multi-step logical reasoning, maintain state over long horizons, and resolve real-world priority conflicts.

---

## 🛠 Interaction Lifecycle
How the **ExecEnv** ecosystem communicates across the stack:

```mermaid
sequenceDiagram
    participant Agent as 🧠 AI Agent
    participant Env as 💼 ExecEnv Server
    participant DB as 📁 Mock Database
    participant Grader as ⚖️ Programmatic Grader

    Agent->>Env: GET /reset
    Env->>DB: Initialize State (5 Emails, 1 Event)
    DB-->>Env: Initial State
    Env-->>Agent: Observation (Inbox & Calendar)
    loop Until Task Complete
        Agent->>Env: POST /step {Action: LABEL_EMAIL}
        Env->>DB: Update State
        DB-->>Env: New State Snapshot
        Env-->>Agent: Observation + Reward Signal
    end
    Grader->>DB: Read Final State
    Grader-->>Agent: Final Score (0.0 - 1.0)
```

---

## 📋 Standardized Task Suite

| Difficulty | Task Name | Core Challenge | Scoring Logic |
| :--- | :--- | :--- | :--- |
| 🟢 **EASY** | **Morning Triage** | Pattern Recognition | +0.1 per correct label (URGENT/SPAM) |
| 🟡 **MEDIUM** | **Strategic Scheduling** | Temporal Reasoning | 1.0 for precise 30-min window extraction |
| 🔴 **HARD** | **Conflict Resolution** | Logical Prioritization | 1.0 for multi-step move + notify workflow |

---

## 💻 Tech Stack & Deployment

### ⚡ Technical Specifications
- **Model Engine**: OpenAI Client Interface (Qwen / GPT / Claude ready)
- **API Framework**: FastAPI + Uvicorn (Asynchronous I/O)
- **Data Integrity**: Pydantic V2 (Strict Schema Enforcement)
- **Runtime**: Python 3.11-slim (Optimized Container Footprint)

### 🚀 Quick Start
1. **Initialize Project**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch Baseline Inference**:
   ```bash
   set HF_TOKEN=your_token && python inference.py
   ```
3. **Verify Environment Logic**:
   ```bash
   python live_test.py
   ```

---

<div align="center">
  <p><i>Developed with ❤️ for the Meta & Hugging Face OpenEnv Hackathon 2024.</i></p>
  <img src="https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo-with-title.svg" width="200">
</div>
