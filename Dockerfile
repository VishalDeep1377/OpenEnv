# Use Python 3.11 for modern pydantic support
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy all project files (including pyproject.toml and uv.lock)
COPY . .

# Install the project in editable mode to expose the 'server' script
RUN pip install -e .

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860

# Run the project script defined in pyproject.toml
CMD ["exec-server"]
