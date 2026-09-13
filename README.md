# Fetch

**One-line pitch:** Fetch turns a single Slack/email ask into a completed, verified deliverable — no manual app-switching.

Fetch is a multi-step AI agent that watches for a triggering event (e.g. a Slack message: *"Sarah asked for the Q3 deck by Friday — get it done"*) and autonomously executes a cross-app workflow: it parses the ask, pulls context and source material, drafts the deliverable, verifies its own work, and reports back — all without a human touching four different apps to get there.

## Architecture

```
 trigger (Slack/email)
        │
        ▼
 ┌──────────────┐     ┌──────────────┐     ┌──────────┐     ┌────────────┐
 │ parse_retrieve│ ──▶ │  draft_act   │ ──▶ │  verify  │ ──▶ │   report   │
 └──────────────┘     └──────────────┘     └──────────┘     └────────────┘
   reads the ask,        generates the        LLM-judge        posts status +
   extracts deadline,    deliverable,          self-check,      confidence note
   pulls doc/thread      creates task/         confidence/      back to Slack
   from Gmail/Drive       calendar block        pass-fail
```

Built with [LangGraph](https://github.com/langchain-ai/langgraph) as a linear/branching state graph — each node above is a graph node, with shared state (`AgentState`) threading the ask, retrieved context, draft, and verification result between them.

## Apps connected

- **Slack** — trigger ingestion (the initial ask) + final status report-back
- **Gmail** — context retrieval (relevant email threads)
- **Google Drive** — document retrieval (source data) and output (deliverable draft)

## Project layout

```
Fetch/
├── README.md
├── .env.example
├── requirements.txt
├── src/
│   ├── graph.py              # LangGraph pipeline definition
│   ├── state.py               # Shared AgentState schema
│   ├── nodes/
│   │   ├── parse_retrieve.py
│   │   ├── draft_act.py
│   │   ├── verify.py
│   │   └── report.py
│   ├── connectors/
│   │   ├── slack_client.py
│   │   ├── gmail_client.py
│   │   └── drive_client.py
│   └── main.py
├── scripts/
│   └── check_connections.py   # quick Slack/Gmail/Drive auth smoke test
├── tests/
│   └── test_pipeline.py
└── demo/
    └── (video goes here later)
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in API keys / MCP server URLs

# 1. Confirm all three app connections are alive
python -m scripts.check_connections

# 2. Run the full pipeline against a test case
python -m src.main --input "Sarah asked for the Q3 deck by Friday — get it done"
```

## Reliability approach

_Fill in after the verify node is built — describe the self-check/confidence signal, what triggers a fail vs. pass, and how failures are surfaced instead of silently reported as success._

## Demo

_Link to demo video here._
