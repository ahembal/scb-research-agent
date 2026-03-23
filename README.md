# Public Data Research Agent

A backend service that helps you explore and query Swedish public statistics
from [Statistics Sweden (SCB)](https://www.scb.se/en/).

## Design Principle

This agent is built on the principle of **human-assisted AI**, not autonomous AI.

At every meaningful step, the agent presents options and explanations — the human
makes the decision. The agent searches, ranks, and summarizes. The human chooses.

This is intentional. It keeps the human in control, makes the system transparent,
and produces more trustworthy results.

## How it works
```
User asks a question
        ↓
Agent searches SCB and presents ranked table candidates
        ↓
User picks a table
        ↓
Agent fetches dimensions and suggests values
        ↓
User confirms or adjusts the selection
        ↓
Agent queries SCB and returns answer + raw source data
```

## Quickstart
```bash
# 1. Clone the repo
git clone <repo-url>
cd public-data-research-agent

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -e .

# 4. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Run the API
uvicorn research_agent.main:app --reload --app-dir src

# 6. Open the interactive docs
open http://127.0.0.1:8000/docs
```

## Documentation

- [Overview & Architecture](docs/01-overview.md)
- [SCB Data & API](docs/02-scb-data.md)
- [Agent Flow](docs/03-agent-flow.md)
- [Session Model & API Contract](docs/04-session-model.md)
- [API Usage Examples](docs/05-api-usage.md)

## Deployment

- [Local — Kind cluster](docs/deployment/kind.md)
- [Cloud — Kubernetes](docs/deployment/k8s.md)
- [Local — Docker Compose](docs/deployment/compose.md)

## Requirements

See [Prerequisites](docs/06-prerequisites.md) for setup instructions.


- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## License

MIT
