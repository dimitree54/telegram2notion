FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including pip
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Install uv and dependencies
RUN pip install uv && uv sync --frozen

# Copy application code
COPY . .

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (if needed for health checks)
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "python", "main.py"] 