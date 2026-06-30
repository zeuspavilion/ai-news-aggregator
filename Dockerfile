FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies (build-essential and libpq-dev are needed for compiling psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock* requirements.txt ./

# Install dependencies into the system site-packages
RUN uv pip install --system --no-cache -r requirements.txt || uv pip install --system --no-cache .

# Copy application files
COPY main.py ./
COPY app/ ./app/

# Run the daily pipeline
ENTRYPOINT ["python", "main.py"]
