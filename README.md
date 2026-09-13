# Fetch

**One-line pitch:** Fetch turns a single Slack ask into a completed, verified deliverable — no manual app-switching.

Fetch is a multi-step AI agent that watches Slack for a triggering message (e.g. *"Sarah asked for the Q4 Planning Deck by Friday — get it done"*) and autonomously executes a cross-app workflow: it parses the ask, pulls context and source material from Google Drive and Gmail, drafts the deliverable, verifies its own work, and reports back to Slack — all without a human touching three different apps to get there.

## Architecture

```
 trigger (Slack message, live via Socket Mode)
        │
        ▼
 ┌───────────────┐     ┌──────────────┐     ┌──────────┐     ┌────────────┐
 │ parse_retrieve│ ──▶ │  draft_act   │ ──▶ │  verify  │ ──▶ │   report   │
 └───────────────┘     └──────────────┘     └──────────┘     └────────────┘
   LLM extracts ask/       drafts the           LLM-as-judge:    posts status +
   requester/deadline,     deliverable,          pass/fail +      confidence note
   searches Drive/Gmail    creates a real         confidence       back to Slack
   for source material     Google Doc                score
```

Built with [LangGraph](https://github.com/langchain-ai/langgraph) as a linear state graph — each node above is a graph node, with shared state (`AgentState`) threading the ask, retrieved context, draft, and verification result between them.

## Apps connected

- **Slack** — the *trigger* (a live Socket Mode listener watches a channel for new messages) **and** the final status report-back.
- **Google Drive** — source material retrieval (finds the relevant file by keyword search) **and** output (the drafted deliverable is created here as a real Google Doc).
- **Gmail** — **context retrieval only**, not a trigger. `parse_retrieve` does a best-effort search for related email threads and adds them as extra context for the draft. Fetch does not currently watch an inbox for new emails — only a Slack message starts a run. (A Gmail-poller trigger is a natural next step, not yet built.)

## Project layout

```
fetch-agent/
├── README.md
├── .env.example
├── requirements.txt
├── src/
│   ├── graph.py                  # LangGraph pipeline definition
│   ├── state.py                  # Shared AgentState schema
│   ├── main.py                   # One-shot CLI entrypoint (--input "...")
│   ├── listen.py                 # Live Slack Socket Mode listener (the real trigger)
│   ├── nodes/
│   │   ├── parse_retrieve.py     # LLM extraction + Drive/Gmail retrieval
│   │   ├── draft_act.py          # LLM drafting + Google Doc creation
│   │   ├── verify.py             # LLM-as-judge pass/fail + confidence
│   │   └── report.py             # Slack report-back
│   └── connectors/
│       ├── slack_client.py       # slack_sdk Web API + Socket Mode
│       ├── gmail_client.py       # Google API client (Gmail)
│       ├── drive_client.py       # Google API client (Drive)
│       └── google_auth.py        # Shared Google OAuth token loading
├── scripts/
│   ├── check_connections.py      # Slack/Gmail/Drive auth smoke test
│   └── google_oauth_setup.py     # One-time interactive Google OAuth flow
├── tests/
│   ├── test_pipeline.py
│   ├── test_parse_retrieve.py
│   └── test_draft_act.py
└── demo/
    └── (video goes here)
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, Slack tokens, Google OAuth client

# 1. One-time Google auth (opens a browser)
python -m scripts.google_oauth_setup

# 2. Confirm all three app connections are alive
python -m scripts.check_connections

# 3a. Live mode (recommended): run the listener, then just type an ask in
#     the configured Slack channel — Fetch reacts automatically.
python -m src.listen

# 3b. One-shot mode: run the pipeline directly against a test case.
python -m src.main --input "Sarah asked for the Q4 Planning Deck by Friday - get it done"
```

## Reliability approach

The `verify` node is an LLM-as-judge pass: it reviews the drafted deliverable against the original ask and produces a `pass`/`fail` verdict, a `0.0-1.0` confidence score, and a short justification. Crucially, it treats **honestly flagging missing source material** (rather than fabricating content to fill gaps) as correct, safe behavior — a draft that says "I don't have enough source data, here's what I need" passes with high confidence; a draft would only fail for being off-topic, inventing specifics it couldn't have known, or otherwise unusable.

That verdict is never silently dropped — `report` surfaces the status, confidence score, and verification notes directly in the Slack message, along with any retrieval errors encountered along the way (e.g. a failed Drive search), so a human always sees when something needs a closer look instead of a false "done."

## Known limitations

- **Drive retrieval is keyword-based** (`name contains 'X' and name contains 'Y'` on the extracted search keywords) — it won't find a source file whose name doesn't share words with the ask.
- **Every message in the watched Slack channel triggers a run** — there's no filter yet for "is this actually an ask" before running the full pipeline.
- **Gmail is context-only** (see above) — no email trigger yet.

## Demo

_Link to demo video here._
