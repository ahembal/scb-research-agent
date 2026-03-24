# Dockerfile
# Multi-stage is overkill for this project — single stage keeps it simple
# and easy to understand for workshop participants.

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies first (separate layer for better caching)
# If only source code changes, this layer is reused from cache
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source
COPY src ./src

# Set Python path so the app can find its modules
ENV PYTHONPATH=/app/src

# Run as non-root user for security
# Never run production containers as root
RUN useradd --create-home appuser
USER appuser

# Document which port the app listens on
EXPOSE 8000

# Health check — Kubernetes uses this to know when the pod is ready
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"

CMD ["uvicorn", "research_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
