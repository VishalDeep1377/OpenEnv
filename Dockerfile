# Use Python 3.11 for modern pydantic support
FROM python:3.11-slim

# Dockerfile specifically optimized for Hugging Face Spaces (Docker SDK)
# Using Python 3.11-slim for a balanced and lightweight environment

# Set up a new user with UID 1000 for permission safety (HF Recommendation)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies first for better caching
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application files
COPY --chown=user . /app

# Final Installation (registers 'server' and ensures local imports work)
RUN pip install --user -e .

# Expose the mandatory Hugging Face app_port
EXPOSE 7860

# Install the local package in editable mode to register the 'server' command
RUN pip install -e .

# The command to start the environment server using the registered entry point
# This satisfies the [project.scripts] validation requirement
CMD ["server"]
