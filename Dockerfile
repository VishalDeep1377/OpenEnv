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

# Install the local package in editable mode to register the 'server' command
RUN pip install -e .

# The command to start the environment server using the registered entry point
# This satisfies the [project.scripts] validation requirement
CMD ["server"]
