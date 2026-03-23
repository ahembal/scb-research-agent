# Overview & Architecture

## What this project is

A backend API service that helps users explore and query
[Swedish public statistics](https://www.statistikdatabasen.scb.se/) using
natural language, powered by Claude (Anthropic).

The service does not answer questions from its own knowledge.
Every answer is grounded in data fetched live from the SCB Statistical Database.

## Design Principle: Assisted AI

This project is built around one core principle:

> **The agent assists. It does not decide.**

Many AI systems make silent decisions on behalf of the user — picking a data source,
choosing parameters, filtering results — without showing their reasoning.

This project takes the opposite approach. At every meaningful decision point,
the agent presents its findings and reasoning, and the human makes the choice.

This produces:
- More transparent results
- More trustworthy answers
- A better learning experience for workshop participants

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                        Client                           │
│                  (curl / frontend / etc)                │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────┐
│                     FastAPI App                         │
│                      main.py                            │
│                                                         │
│   POST /session/start                                   │
│   POST /session/select-table                            │
│   POST /session/confirm-query                           │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼────────┐
│   agent.py     │ │session_store │ │  scb_*.py     │
│                │ │              │ │               │
│ Step functions │ │ In-memory    │ │ SCB API calls │
│ LLM prompting  │ │ session state│ │ metadata      │
└─────────┬──────┘ └──────────────┘ └──────┬────────┘
          │                                │
┌─────────▼──────┐               ┌─────────▼────────┐
│  Anthropic API │               │   SCB API        │
│  Claude        │               │   PxWebApi v2    │
└────────────────┘               └──────────────────┘
```

## Key components

| File | Responsibility |
|---|---|
| `main.py` | HTTP routing, request/response handling |
| `agent.py` | Step functions for the assisted pipeline |
| `session_store.py` | In-memory session state between steps |
| `prompts.py` | LLM prompt templates (rank and explain, not decide) |
| `models.py` | Internal data models for agent state |
| `schema.py` | FastAPI request/response models |
| `scb_metadata.py` | Search and fetch metadata from SCB |
| `scb_query_builder.py` | Build SCB API query payloads |
| `result_parser.py` | Map dimension codes to human-readable labels |
| `metadata_parser.py` | Parse dimension structures from metadata |
| `config.py` | Environment-based configuration |

## Technology choices

| Technology | Why |
|---|---|
| FastAPI | Fast, async, auto-generates OpenAPI docs |
| Anthropic Claude | LLM for ranking, summarizing, and answering |
| httpx | Async HTTP client for SCB API calls |
| Pydantic | Data validation for requests and responses |
| In-memory session store | Simple, no infrastructure needed for the workshop |
