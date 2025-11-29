# ==============================================================================
# BuySpy Telegram Bot - Multi-stage Docker Build with pip
# ==============================================================================

# Build stage
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment for user installation
ENV PYTHONUSERBASE=/tmp/.local
ENV PATH=/tmp/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --user --no-cache-dir -e .

# ==============================================================================
# Runtime stage
# ==============================================================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUSERBASE=/app/.local
ENV PATH=/app/.local/bin:$PATH

# Set work directory
WORKDIR /app

# Create non-root user
RUN groupadd -r buyspy && useradd -r -g buyspy -m -d /app -s /bin/bash buyspy

# Copy Python dependencies from builder stage
COPY --from=builder /tmp/.local /app/.local

# Copy application code
COPY --chown=buyspy:buyspy app/ ./app/
COPY --chown=buyspy:buyspy telegram_bot.py ./
COPY --chown=buyspy:buyspy .env.example ./

# Change ownership to non-root user
RUN chown -R buyspy:buyspy /app

# Switch to non-root user
USER buyspy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (if needed for future extensions)
EXPOSE 8080

# Run the telegram bot
CMD ["python", "telegram_bot.py"]
