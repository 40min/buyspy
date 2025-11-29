# ==============================================================================
# BuySpy Telegram Bot - Multi-stage Docker Build
# ==============================================================================

# Stage 1: Builder - Install dependencies and prepare the environment
FROM python:3.13-slim as builder

# Install system dependencies required for building
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Create virtual environment and sync dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --no-dev --no-cache

# ==============================================================================
# Stage 2: Runtime - Final image with Node.js for BrightData MCP
# ==============================================================================

FROM python:3.13-slim as runtime

# Install Node.js for BrightData MCP tool (npx)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install additional runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r buyspy && useradd -r -g buyspy -m -d /app -s /bin/bash buyspy

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
WORKDIR /app
COPY --chown=buyspy:buyspy app/ ./app/
COPY --chown=buyspy:buyspy telegram_bot.py ./
COPY --chown=buyspy:buyspy .env.example ./

# Switch to non-root user
USER buyspy

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (if needed for future extensions)
EXPOSE 8080

# Run the telegram bot
CMD ["python", "telegram_bot.py"]
