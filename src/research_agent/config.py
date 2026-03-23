# src/research_agent/config.py
"""
Central configuration for the research agent.

All settings are read from environment variables with sensible defaults.
Never hardcode secrets — always use .env or Kubernetes secrets.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── SCB API ───────────────────────────────────────────────────────────────────

# Base URL for the SCB Statistical Database API (PxWebApi v2)
SCB_API_BASE_URL = os.getenv(
    "SCB_API_BASE_URL",
    "https://statistikdatabasen.scb.se/api/v2"
)

# ── Anthropic ─────────────────────────────────────────────────────────────────

# API key — required, no default
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Model to use for all LLM calls
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

# Max tokens for LLM responses
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

# ── Session ───────────────────────────────────────────────────────────────────

# How long (seconds) to keep an idle session before expiring it
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
