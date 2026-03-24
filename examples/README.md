# Examples

This folder contains ready-to-use example questions for the research agent.

## sample-questions.txt

A set of example questions grouped by SCB table.
Use these to quickly test the full assisted pipeline without having
to think of your own questions.

## How to use

Start the API:
```bash
make run
```

Pick a question from sample-questions.txt and run step 1:
```bash
curl -s -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the population of Sweden in 2024?"}' \
  | python3 -m json.tool
```

Then follow the assisted flow described in docs/05-api-usage.md.
