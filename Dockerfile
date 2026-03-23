FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "research_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
