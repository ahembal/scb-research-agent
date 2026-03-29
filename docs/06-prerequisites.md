# Prerequisites

Before running the agent you need the following.

## 1. Python 3.10+

Check your version:
```bash
python3 --version
```

## 2. An Anthropic API key

The agent uses Claude (Anthropic) as its LLM backend.

To get a key:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy the key — you only see it once

Add it to your `.env` file:
```bash
cp .env.example .env
nano .env   # or any editor you prefer
```

Set:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Note: API usage is billed per token. The default model
(`claude-sonnet-4-20250514`) costs a small amount per query.
For a workshop session the total cost is typically under $1.

## 3. Internet access

The agent makes outbound requests to two external APIs:
- `https://statistikdatabasen.scb.se` — SCB Statistical Database
- `https://api.anthropic.com` — Anthropic Claude

Both must be reachable from wherever you run the service.

## Note on billing

A new Anthropic account requires credits before the API works.
Free tier access is not available for the API.

To add credits:
1. Go to https://console.anthropic.com/settings/billing
2. Click **Add credits**
3. $5 is more than enough for a full workshop session with this project

## Docker Hub image

The production image is published to Docker Hub as:
```
ahembal/scb-research-agent:latest
```
