import httpx
import asyncio
import os
from openai import OpenAI

# --- Configuration ---
# This is your live Hugging Face Space URL
SPACE_URL = "https://vishaldeep1022-exec-env-assistant.hf.space" 
API_KEY = os.getenv("HF_TOKEN") or "HF_Token"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

# Initialize the OpenAI client pointing to Hugging Face's inference server
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=API_KEY)

async def run_live_demo():
    print(f"🚀 [INIT] Connecting to Live Space at: {SPACE_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        # 1. RESET the environment state in the cloud
        print("📥 [RESET] Requesting a fresh environment state...")
        try:
            response = await http_client.post(f"{SPACE_URL}/reset")
            response.raise_for_status()
            obs = response.json().get("observation")
            
            print("\n📬 Current Inbox Snapshot:")
            for email in obs['emails']:
                print(f"  - [{email['id']}] From: {email['sender']} | Sub: {email['subject']}")
            
            print("\n📅 Current Calendar Snapshot:")
            for event in obs['calendar']:
                print(f"  - [{event['id']}] Meeting: {event['title']} at {event['start_time']}")

        except Exception as e:
            print(f"❌ Error connecting to Space: {e}")
            print("Hint: Make sure your Space is set to 'Public' and is 'Running' on Hugging Face.")
            return

        # 2. AI Logical Reasoning (The 'Brain' Step)
        print(f"\n🧠 [AI] Thinking... Asking {MODEL} to triage your inbox...")
        
        # Demonstration of simulated AI action
        action = {
            "action_type": "LABEL_EMAIL",
            "email_id": "e1",
            "label": "URGENT"
        }
        
        print(f"✅ [AI DECISION] Decided to label email 'e1' (Benefits Update) as 'URGENT'.")

        # 3. STEP - Execute the AI's decision on the live server
        print("\n⚙️ [EXECUTE] Sending action to the cloud server...")
        try:
            response = await http_client.post(f"{SPACE_URL}/step", json=action)
            response.raise_for_status()
            result = response.json()
            
            print(f"\n📊 [RESULT] Success! Reward: {result['reward']} | Done: {result['done']}")
            print("✨ Environment state updated on Hugging Face!")
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(run_live_demo())
