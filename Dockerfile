# Use Python 3.11 for modern pydantic support
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install dependencies
# We assume openenv-core and other requirements are listed in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Environment variables for HF Space
ENV PORT=7860
EXPOSE 7860

# The command to start the environment server
# Using uvicorn to serve the FastAPI app on port 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
