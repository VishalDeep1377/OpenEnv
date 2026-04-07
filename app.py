import sys
import os

# Ensure the root and server directory are in the path for flexible imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

# Import the FastAPI instance from our server module
from server.app import app

# This allows 'uvicorn app:app' to work from the root as expected by HF Spaces
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
