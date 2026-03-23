# Contributing

## Design Principles

Before contributing, please read and internalize the core design principle:

> The agent assists. It does not decide.

Every piece of logic you add should respect this. If you find yourself writing
code that silently makes a choice on behalf of the user, stop and rethink.

## Code Conventions

- All Python files start with a path comment: `# src/research_agent/agent.py`
- Every module has a top-level docstring explaining its purpose
- Every function has a docstring explaining what it does, not how
- No magic values — all configuration goes in `config.py` via env vars
- Keep functions small and single-purpose

## Branching

- `main` — stable, always runnable
- `phase/X` — work in progress for a specific phase
- `fix/short-description` — bug fixes

## Running tests
```bash
make test
```

## Running the API locally
```bash
make run
```

## Adding a new dependency

Add it to `pyproject.toml` under `dependencies`, then run:
```bash
pip install -e .
```

## Environment variables

Never commit `.env`. Always update `.env.example` when adding new env vars.
